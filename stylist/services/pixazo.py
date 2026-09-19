import time

import requests
from django.conf import settings

from .base_image import BaseImageProvider
from .exceptions import ImageGenerationError
from .prompts_image import build_outfit_edit_prompt, build_outfit_caption


class PixazoImageService(BaseImageProvider):
    """
    Pixazo (gateway.pixazo.ai) image provider.

    WHAT WAS WRONG
    --------------
    The old code POSTed to /sd3/v1/getData (Stable Diffusion 3) with
      * the styling plan injected as raw JSON into the prompt, and
      * prompt_strength 0.85 img2img.
    SD3 is a plain diffusion model: it cannot follow instructions such as
    "keep the shirt, add these trousers and shoes, go full body". It blended
    the input pixels with the JSON words, which is why every result looked
    like the input photo with a random background and the planned shoes
    lying around as props.

    WHAT IT DOES NOW
    ----------------
    1. Primary: FLUX 2 Pro image-to-image - an instruction-following editor
       (async queue: submit -> poll /v2/requests/status/{id} -> media_url).
    2. Fallback: SD3 img2img, but with a flat descriptive caption and a
       moderate prompt_strength so the person/top survive while the scene
       and outfit change.
    """

    EDIT_URL = (
        "https://gateway.pixazo.ai/flux-2-pro-image-to-image-866/"
        "v1/flux-2-pro-image-to-image-request"
    )
    SD3_URL = "https://gateway.pixazo.ai/sd3/v1/getData"
    POLL_TIMEOUT = 240
    POLL_INTERVAL = 4

    def __init__(self):
        self.api_key = settings.PIXAZO_SUBSCRIPTION_KEY

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": str(self.api_key),
        }

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _download(self, url: str) -> bytes:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.content

    def _poll(self, polling_url: str) -> str:
        deadline = time.time() + self.POLL_TIMEOUT

        while time.time() < deadline:
            response = requests.get(
                polling_url,
                headers=self._headers(),
                timeout=30,
            )

            if response.status_code != 200:
                raise ImageGenerationError(
                    f"Pixazo polling error {response.status_code}: {response.text}"
                )

            result = response.json()
            status = str(result.get("status", "")).upper()

            if status == "COMPLETED":
                output = result.get("output") or {}
                media = output.get("media_url") or []
                if isinstance(media, str):
                    return media
                if media:
                    return media[0]
                raise ImageGenerationError(
                    f"Pixazo job completed without media: {result}"
                )

            if status in ("FAILED", "ERROR"):
                raise ImageGenerationError(
                    f"Pixazo job failed: {result.get('error') or result}"
                )

            time.sleep(self.POLL_INTERVAL)

        raise ImageGenerationError("Pixazo job timed out while polling.")

    # ------------------------------------------------------------------ #
    # providers
    # ------------------------------------------------------------------ #

    def _flux2_edit(self, image_url: str, styling_plan: dict) -> bytes:
        prompt = build_outfit_edit_prompt(styling_plan)

        data = {
            "prompt": prompt,
            "image_urls": [image_url],
            "image_size": "portrait_4_3",
            "output_format": "jpeg",
        }

        response = requests.post(
            self.EDIT_URL,
            json=data,
            headers=self._headers(),
            timeout=60,
        )

        if response.status_code != 202 and response.status_code != 200:
            raise ImageGenerationError(
                f"Pixazo FLUX2 edit error {response.status_code}: {response.text}"
            )

        result = response.json()

        # synchronous payload (some plans) -> {"output": "..."} or media url
        if result.get("output"):
            output = result["output"]
            if isinstance(output, str):
                return self._download(output)
            media = output.get("media_url") or []
            if media:
                return self._download(media[0] if isinstance(media, list) else media)

        polling_url = result.get("polling_url")
        if not polling_url:
            raise ImageGenerationError(
                f"Pixazo FLUX2 edit: unexpected response {result}"
            )

        media_url = self._poll(polling_url)
        return self._download(media_url)

    def _sd3_img2img(self, image_url: str, styling_plan: dict) -> bytes:
        prompt = build_outfit_caption(styling_plan)

        data = {
            "prompt": prompt,
            "negative_prompt": (
                "floating clothes, shoes on the ground, cropped legs, "
                "waist-up crop, same background, dark, blurry, bad anatomy, "
                "deformed, watermark"
            ),
            "image": image_url,
            "prompt_strength": 0.65,
            "steps": 30,
            "cfg": 6.0,
            "output_format": "jpg",
            "output_quality": 90,
        }

        response = requests.post(
            self.SD3_URL,
            json=data,
            headers=self._headers(),
            timeout=120,
        )

        if response.status_code != 200:
            raise ImageGenerationError(
                f"Pixazo SD3 error {response.status_code}: {response.text}"
            )

        result = response.json()
        media_url = result.get("output")

        if not media_url:
            raise ImageGenerationError(
                f"Pixazo SD3: no output URL returned. Response: {result}"
            )

        return self._download(media_url)

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def generate_outfit_images(self, image_url: str, styling_plan: dict):
        try:
            return self._flux2_edit(image_url, styling_plan)
        except ImageGenerationError as exc:
            # fall back to tuned SD3 img2img instead of failing the request
            last_error = exc

        try:
            return self._sd3_img2img(image_url, styling_plan)
        except ImageGenerationError as exc:
            raise ImageGenerationError(
                f"Pixazo: both FLUX2 edit and SD3 fallback failed. "
                f"FLUX2: {last_error} | SD3: {exc}"
            ) from exc
