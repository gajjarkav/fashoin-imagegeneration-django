import os
import json
import base64
import logging
from django.conf import settings
from .exceptions import ClothingAnalysisError, StylePlanningError

from .prompts import (
    ANALYZE_CLOTHING_PROMPT,
    STYLE_PLANNER_PROMPT,
    REFINE_OUTFIT_PROMPT,
)
from .base_image import BaseImageProvider

try:
    from openai import OpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
except ImportError:
    pass  # We will handle missing packages gracefully or expect the user has installed them

logger = logging.getLogger("stylist")

class AzureOpenAIService(BaseImageProvider):
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://k77gajjar-23-resource.services.ai.azure.com/openai/v1")
        self.deployment_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-5-mini")
        
        # Check if an explicit API key is provided in .env
        api_key = os.getenv("AZURE_OPENAI_API_KEY", None)

        if api_key:
            # Use the explicit API key if available
            self.client = OpenAI(
                base_url=self.endpoint,
                api_key=api_key
            )
        else:
            # Fallback to Azure Authentication via DefaultAzureCredential
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://ai.azure.com/.default"
            )
            self.client = OpenAI(
                base_url=self.endpoint,
                api_key=token_provider
            )

    def _generate_text(self, messages: list) -> str:
        try:
            # Using the new Responses API exactly as requested in your Python snippet
            response = self.client.responses.create(
                model=self.deployment_name,
                input=messages,
            )
            
            # Extract the text answer
            output = response.output[0]
            if hasattr(output, "text"):
                return output.text
            elif isinstance(output, dict) and "text" in output:
                return output["text"]
            else:
                return str(output)
        except Exception as exc:
            logger.error(f"Azure OpenAI Error: {exc}")
            raise

    def _parse_json(self, text: str) -> dict:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                text = text[start:end]
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error(f"Azure OpenAI returned invalid JSON: {text}")
            raise Exception("Invalid JSON returned by AI") from exc

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        mime = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mime = "image/png"
        elif image_path.lower().endswith(".webp"):
            mime = "image/webp"
        return f"data:{mime};base64,{encoded}"

    def analyze_clothing(self, image_path: str) -> dict:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ANALYZE_CLOTHING_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": self._encode_image(image_path)
                        }
                    }
                ]
            }
        ]
        try:
            text = self._generate_text(messages)
            return self._parse_json(text)
        except Exception as exc:
            raise ClothingAnalysisError(str(exc)) from exc

    def generate_style_plan(self, analysis: dict) -> dict:
        prompt = f"{STYLE_PLANNER_PROMPT}\n\nClothing Analysis:\n{json.dumps(analysis, indent=2)}"
        messages = [
            {"role": "user", "content": prompt}
        ]
        try:
            text = self._generate_text(messages)
            return self._parse_json(text)
        except Exception as exc:
            raise StylePlanningError(str(exc)) from exc

    def generate_refined_plan(self, previous_plan: dict, user_prompt: str) -> dict:
        prompt = f"{REFINE_OUTFIT_PROMPT}\n\nPrevious Plan:\n{json.dumps(previous_plan, indent=2)}\n\nUser Request: {user_prompt}"
        messages = [
            {"role": "user", "content": prompt}
        ]
        try:
            text = self._generate_text(messages)
            return self._parse_json(text)
        except Exception as exc:
            raise Exception(str(exc)) from exc

    def generate_outfit_images(self, image_path: str, styling_plan: dict) -> bytes:
        raise NotImplementedError("AzureOpenAI text model does not generate images. Route to FLUX instead.")

    def refine_outfit(self, image_path: str, previous_plan: dict, user_prompt: str) -> bytes:
        raise NotImplementedError("AzureOpenAI text model does not generate images. Route to FLUX instead.")
