import json
import re
import time
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
    REFINE_OUTFIT_PROMPT,
)
from .prompts_image import build_outfit_edit_prompt
from .base_image import BaseImageProvider


class GeminiService(BaseImageProvider):
    """
    Wrapper around Google Gemini APIs.

    Text  : gemini-3-flash-preview (falls back to gemini-2.5-flash)
    Image : gemini-2.5-flash-image  ("Nano Banana", free tier, supports
            editing WITH a reference image). The old code called
            models.generate_images(model='imagen-3.0-generate-001') which
              a) does not exist on the Gemini API free tier (404), and
              b) is text-to-image only - the uploaded photo was never sent,
                 so it could never produce the user's own outfit.
            Editing is done with generate_content([prompt, image_part]).
    """

    TEXT_MODELS = (
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
    )

    IMAGE_MODELS = (
        "gemini-2.5-flash-image",          # Nano Banana - free tier
        "gemini-3.1-flash-lite-image",     # free-tier alias on AI Studio (2026)
        "gemini-2.5-flash-image-preview",  # legacy preview id
    )

    MAX_RETRIES = 3

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GOOGLE_API_KEY,
        )

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _strip_markdown(text: str) -> str:
        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]

        if text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3:]

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
    def _status_code(exc: Exception):
        """Best-effort HTTP status from a google.genai error."""
        match = re.match(r"\s*(\d{3})\b", str(exc))
        if match:
            return int(match.group(1))
        return getattr(exc, "code", None)

    @staticmethod
    def _image_part(image_path: str):
        import requests

        if image_path.startswith("http://") or image_path.startswith("https://"):
            response = requests.get(image_path, timeout=60)
            response.raise_for_status()
            data = response.content
            suffix = Path(image_path.split("?")[0]).suffix.lower()
            if not suffix:
                suffix = ".jpg"
        else:
            path = Path(image_path)
            suffix = path.suffix.lower()
            data = path.read_bytes()

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
            data=data,
            mime_type=mime_map[suffix],
        )

    @staticmethod
    def _extract_image_bytes(response) -> bytes:
        """Pull the inline image out of a generate_content response."""
        for candidate in (getattr(response, "candidates", None) or []):
            content = getattr(candidate, "content", None)
            for part in (getattr(content, "parts", None) or []):
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None)
                if data:
                    return data
        return b""

    def _generate_text(self, prompt: str, parts=None) -> str:
        contents = parts if parts is not None else prompt
        last_error = None

        for model in self.TEXT_MODELS:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                )
                return response.text or ""

            except ClientError as exc:
                if self._status_code(exc) in (404, 400):
                    last_error = exc      # unknown model id -> try next
                    continue
                raise

            except ServerError as exc:
                raise GeminiUnavailableError(str(exc)) from exc

        raise GeminiResponseError(
            f"No usable Gemini text model. Last error: {last_error}"
        )

    def _edit_image(self, prompt: str, image_path: str) -> bytes:
        """
        Instruction-based edit of `image_path` using the free-tier image
        models, with model fallback and 429/503 backoff.
        """
        image_part = self._image_part(image_path)
        last_error = None

        for model in self.IMAGE_MODELS:
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[prompt, image_part],
                    )

                    data = self._extract_image_bytes(response)
                    if data:
                        return data

                    raise GeminiResponseError(
                        "Gemini returned no image part. Text: "
                        + (response.text or "<empty>")
                    )

                except ClientError as exc:
                    status = self._status_code(exc)

                    if status in (404, 400):
                        last_error = exc   # model id not available -> next
                        break

                    if status in (429, 503):
                        last_error = exc   # free-tier rate limit -> backoff
                        time.sleep(10 * (attempt + 1))
                        continue

                    raise ImageGenerationError(str(exc)) from exc

                except ServerError as exc:
                    last_error = exc
                    time.sleep(10 * (attempt + 1))

        raise ImageGenerationError(
            f"Gemini image generation failed on all models. "
            f"Last error: {last_error}"
        )

    # ------------------------------------------------------------------ #
    # pipeline steps
    # ------------------------------------------------------------------ #

    def analyze_clothing(self, image_path: str) -> dict:
        try:
            text = self._generate_text(
                ANALYZE_CLOTHING_PROMPT,
                parts=[ANALYZE_CLOTHING_PROMPT, self._image_part(image_path)],
            )
            return self._parse_json(text)

        except GeminiUnavailableError:
            raise

        except GeminiResponseError:
            raise

        except ClientError as exc:
            raise ClothingAnalysisError(str(exc)) from exc

        except Exception as exc:
            raise ClothingAnalysisError(str(exc)) from exc

    def generate_style_plan(self, analysis: dict) -> dict:
        prompt = f"""
{STYLE_PLANNER_PROMPT}

Clothing Analysis

{json.dumps(analysis, indent=2)}
"""
        try:
            return self._parse_json(self._generate_text(prompt))

        except GeminiUnavailableError:
            raise

        except GeminiResponseError:
            raise

        except ClientError as exc:
            raise StylePlanningError(str(exc)) from exc

        except Exception as exc:
            raise StylePlanningError(str(exc)) from exc

    def generate_outfit_images(
        self,
        image_path: str,
        styling_plan: dict,
    ):
        """
        Edit the uploaded photo: same person + same hero garment, but
        full-body, wearing the planned outfit, on a new background.
        """
        prompt = build_outfit_edit_prompt(styling_plan)

        try:
            return self._edit_image(prompt, image_path)

        except ImageGenerationError:
            raise

        except ServerError as exc:
            raise GeminiUnavailableError(str(exc)) from exc

        except ClientError as exc:
            raise ImageGenerationError(str(exc)) from exc

        except Exception as exc:
            raise ImageGenerationError(str(exc)) from exc

    def refine_outfit(
        self,
        image_path: str,
        previous_plan: dict,
        user_prompt: str,
    ):
        """
        Chat refinement: update the plan in text first, then edit the photo
        with the updated plan (the old code ignored the photo completely).
        """
        plan_prompt = f"""
{REFINE_OUTFIT_PROMPT}

Previous Styling Plan

{json.dumps(previous_plan, indent=2)}

User Request

{user_prompt}

Return ONLY valid JSON with the same schema as the previous styling plan
(a single outfit object with theme, bottom, footwear, accessories, bag,
jewelry, reason). No markdown, no code fences.
"""
        try:
            updated_plan = self._parse_json(self._generate_text(plan_prompt))

        except Exception:
            # If the planner step fails, still honour the raw user request.
            updated_plan = {
                "theme": previous_plan.get("theme", ""),
                "bottom": previous_plan.get("bottom", ""),
                "footwear": previous_plan.get("footwear", ""),
                "accessories": previous_plan.get("accessories", []),
                "bag": previous_plan.get("bag", ""),
                "jewelry": previous_plan.get("jewelry", []),
                "reason": user_prompt,
            }

        edit_prompt = (
            build_outfit_edit_prompt(updated_plan)
            + f"\n\nAdditional user instruction to apply: {user_prompt}"
        )

        try:
            return self._edit_image(edit_prompt, image_path)

        except ImageGenerationError:
            raise

        except ServerError as exc:
            raise GeminiUnavailableError(str(exc)) from exc

        except ClientError as exc:
            raise ImageGenerationError(str(exc)) from exc

        except Exception as exc:
            raise ImageGenerationError(str(exc)) from exc