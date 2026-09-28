import base64
import time
import logging
import requests
from io import BytesIO
from django.conf import settings

from .base_image import BaseImageProvider
from .prompts_image import build_flux_prompt

logger = logging.getLogger(__name__)

class FluxServiceException(Exception):
    pass

class FluxContentFilterException(FluxServiceException):
    """Raised when Azure rejects the prompt for content safety."""
    pass

class FluxService(BaseImageProvider):
    def __init__(self):
        self.endpoint = settings.AZURE_FLUX_ENDPOINT.rstrip('/')
        self.api_key = settings.AZURE_FLUX_API_KEY
        self.model = settings.AZURE_FLUX_MODEL.lower()
        self.api_version = settings.AZURE_FLUX_API_VERSION
        
        if not self.endpoint or not self.api_key:
            logger.error("Azure FLUX configuration is missing.")
            
    def edit_image(self, image_file, prompt, width=1024, height=1024, output_format="jpeg"):
        if not self.endpoint or not self.api_key:
            raise FluxServiceException("Azure FLUX configuration is missing.")
            
        # Convert image to base64
        try:
            image_bytes = image_file.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to read and encode image: {e}")
            raise FluxServiceException("Invalid image data.")
            
        if "/providers/" in self.endpoint:
            url = f"{self.endpoint}?api-version={self.api_version}"
        else:
            url = f"{self.endpoint}/providers/blackforestlabs/v1/{self.model}?api-version={self.api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "input_image": base64_image,
            "width": width,
            "height": height,
            "output_format": output_format,
        }
        
        start_time = time.time()
        logger.info(f"Sending prompt to Azure FLUX: {prompt[:300]}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            duration = time.time() - start_time
            
            logger.info(f"FLUX generation took {duration:.2f}s - Status: {response.status_code}")
            
            if response.status_code == 429:
                logger.error("Azure FLUX rate limit exceeded (429).")
                raise FluxServiceException("Rate limit exceeded. Please try again later.")
            elif response.status_code in [401, 403]:
                logger.error("Azure FLUX authentication error.")
                raise FluxServiceException("Authentication error with Azure service.")
            elif 400 <= response.status_code < 500:
                logger.error(f"Azure FLUX client error {response.status_code}: {response.text}")
                # Detect content safety violations specifically so callers can retry
                try:
                    err_code = response.json().get("error", {}).get("code", "")
                except Exception:
                    err_code = ""
                if err_code == "content_safety_violation":
                    raise FluxContentFilterException("Prompt blocked by Azure content filter.")
                raise FluxServiceException(f"Azure API error: {response.status_code}")
            elif response.status_code >= 500:
                logger.error(f"Azure FLUX server error {response.status_code}: {response.text}")
                raise FluxServiceException("Azure service is currently unavailable.")
                
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            logger.info(f"Azure FLUX response keys: {list(data.keys())}")

            # ── helper: extract image string from a sample item ──────────
            def _extract_from_item(item):
                """item can be a bare string or a dict with image/url key."""
                if isinstance(item, str):
                    return item
                if isinstance(item, dict):
                    # try common key names returned by BFL / Azure wrappers
                    for key in ("url", "b64_json", "image", "image_data", "data"):
                        if key in item:
                            return item[key]
                    # last resort: return the first string value found
                    for v in item.values():
                        if isinstance(v, str) and len(v) > 20:
                            return v
                return None

            # ── try every known response shape ────────────────────────────
            image_str = None

            result_block = data.get("result", {})

            # shape 1: result.sample  (list of str or list of dicts)
            sample = result_block.get("sample")
            if isinstance(sample, list) and sample:
                logger.info(f"sample[0] type: {type(sample[0])}, preview: {str(sample[0])[:80]}")
                image_str = _extract_from_item(sample[0])
            elif isinstance(sample, str) and sample:
                image_str = sample

            # shape 2: result.image
            if not image_str:
                image_str = _extract_from_item(result_block.get("image") or "")

            # shape 3: top-level image / output list
            if not image_str:
                image_str = _extract_from_item(data.get("image") or "")
            if not image_str:
                outputs = data.get("output", [])
                if isinstance(outputs, list) and outputs:
                    image_str = _extract_from_item(outputs[0])

            # shape 4: OpenAI-compatible format  {"created":..., "data":[{"b64_json":"..."}]}
            if not image_str:
                data_list = data.get("data", [])
                if isinstance(data_list, list) and data_list:
                    logger.info(f"Using OpenAI-compat 'data' format. data[0] preview: {str(data_list[0])[:80]}")
                    image_str = _extract_from_item(data_list[0])

            if image_str:
                return image_str

            logger.error(f"Unrecognised Azure FLUX response structure: {list(data.keys())} | result keys: {list(result_block.keys())}")
            raise FluxServiceException("Received malformed response from Azure.")
                
        except requests.exceptions.Timeout:
            logger.error("Azure FLUX request timed out.")
            raise FluxServiceException("Request to Azure timed out.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Azure FLUX request failed: {e}")
            raise FluxServiceException("Network error while connecting to Azure.")
        except ValueError:
            logger.error("Azure FLUX returned non-JSON response.")
            raise FluxServiceException("Invalid response format from Azure.")

    # Minimal safe fallback used when the primary prompt triggers the content filter
    _FALLBACK_PROMPT = "fashion outfit editorial photo, photorealistic, studio lighting."

    def generate_outfit_images(self, image_path, styling_plan):
        prompt = build_flux_prompt(styling_plan)
        try:
            with open(image_path, 'rb') as f:
                result_data = self.edit_image(f, prompt)
        except FluxContentFilterException:
            logger.warning("Primary prompt blocked by content filter. Retrying with fallback prompt.")
            theme = (styling_plan or {}).get("theme", "casual")
            fallback = f"fashion outfit photo, {theme} style, photorealistic, studio lighting."
            with open(image_path, 'rb') as f:
                result_data = self.edit_image(f, fallback)
        return self._decode_result(result_data)

    def refine_outfit(self, image_path, previous_plan, user_prompt):
        prompt = build_flux_prompt(previous_plan)
        try:
            with open(image_path, 'rb') as f:
                result_data = self.edit_image(f, prompt)
        except FluxContentFilterException:
            logger.warning("Refine prompt blocked by content filter. Retrying with fallback prompt.")
            with open(image_path, 'rb') as f:
                result_data = self.edit_image(f, self._FALLBACK_PROMPT)
        return self._decode_result(result_data)

    def _decode_result(self, result_data):
        if result_data.startswith("http://") or result_data.startswith("https://"):
            import requests
            response = requests.get(result_data, timeout=60)
            return response.content
        else:
            if "," in result_data:
                result_data = result_data.split(",")[1]
            return base64.b64decode(result_data)
