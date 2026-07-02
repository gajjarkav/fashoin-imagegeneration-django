import json
from pathlib import Path

from django.conf import settings

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from .exceptions import (
    ClothingAnalysisError,
    GeminiResponseError,
    GeminiUnavailableError,
    ImageGenerationError,
    StylePlanningError,
)

from .prompts import (
    ANALYZE_CLOTHING_PROMPT,
    STYLE_PLANNER_PROMPT,
    IMAGE_GENERATION_PROMPT,
    REFINE_OUTFIT_PROMPT,
)
from .prompts_image import IMAGE_SYSTEM_PROMPT
from .base_image import BaseImageProvider


class GeminiService(BaseImageProvider):
    """
    Wrapper around Google Gemini APIs.
    """

    MODEL_TEXT = "gemini-3-flash-preview"
    MODEL_IMAGE = "gemini-2.5-flash-image"

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GOOGLE_API_KEY,
        )

    @staticmethod
    def _strip_markdown(text: str) -> str:

        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]

        if text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    @classmethod
    def _parse_json(cls, text: str) -> dict:

        if not text:
            raise GeminiResponseError(
                "Gemini returned an empty response."
            )

        text = cls._strip_markdown(text)

        try:
            return json.loads(text)

        except json.JSONDecodeError as exc:
            raise GeminiResponseError(
                "Gemini returned invalid JSON."
            ) from exc

    @staticmethod
    def _image_part(image_path: str):

        path = Path(image_path)

        suffix = path.suffix.lower()

        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }

        if suffix not in mime_map:
            raise ValueError(
                f"Unsupported image type: {suffix}"
            )

        return types.Part.from_bytes(
            data=path.read_bytes(),
            mime_type=mime_map[suffix],
        )

    def analyze_clothing(
        self,
        image_path: str,
    ) -> dict:

        try:

            response = self.client.models.generate_content(
                model=self.MODEL_TEXT,
                contents=[
                    ANALYZE_CLOTHING_PROMPT,
                    self._image_part(image_path),
                ],
            )

            return self._parse_json(
                response.text,
            )

        except ServerError as exc:

            raise GeminiUnavailableError(
                str(exc),
            ) from exc

        except ClientError as exc:

            raise ClothingAnalysisError(
                str(exc),
            ) from exc

        except Exception as exc:

            raise ClothingAnalysisError(
                str(exc),
            ) from exc

    def generate_style_plan(
        self,
        analysis: dict,
    ) -> dict:

        prompt = f"""
{STYLE_PLANNER_PROMPT}

Clothing Analysis

{json.dumps(analysis, indent=2)}
"""

        try:

            response = self.client.models.generate_content(
                model=self.MODEL_TEXT,
                contents=prompt,
            )

            return self._parse_json(
                response.text,
            )

        except ServerError as exc:

            raise GeminiUnavailableError(
                str(exc),
            ) from exc

        except ClientError as exc:

            raise StylePlanningError(
                str(exc),
            ) from exc

        except Exception as exc:

            raise StylePlanningError(
                str(exc),
            ) from exc


    def generate_outfit_images(
        self,
        image_path: str,
        styling_plan: dict,
    ):

        prompt = f"""
{IMAGE_SYSTEM_PROMPT}

Styling Plan

{json.dumps(styling_plan, indent=2)}
"""

        try:

            response = self.client.models.generate_content(
                model=self.MODEL_IMAGE,
                contents=[
                    prompt,
                    self._image_part(image_path),
                ],
            )

            return response

        except ServerError as exc:

            raise GeminiUnavailableError(
                str(exc),
            ) from exc

        except ClientError as exc:

            raise ImageGenerationError(
                str(exc),
            ) from exc

        except Exception as exc:

            raise ImageGenerationError(
                str(exc),
            ) from exc

    def refine_outfit(
        self,
        image_path: str,
        previous_plan: dict,
        user_prompt: str,
    ):

        prompt = f"""
{REFINE_OUTFIT_PROMPT}

Previous Styling Plan

{json.dumps(previous_plan, indent=2)}

User Request

{user_prompt}
"""

        try:

            response = self.client.models.generate_content(
                model=self.MODEL_IMAGE,
                contents=[
                    prompt,
                    self._image_part(image_path),
                ],
            )

            return response

        except ServerError as exc:

            raise GeminiUnavailableError(
                str(exc),
            ) from exc

        except ClientError as exc:

            raise ImageGenerationError(
                str(exc),
            ) from exc

        except Exception as exc:

            raise ImageGenerationError(
                str(exc),
            ) from exc