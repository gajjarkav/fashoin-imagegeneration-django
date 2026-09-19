import time
import random
import requests
from django.conf import settings
from .base_image import BaseImageProvider
from .exceptions import ImageGenerationError
import json
from .prompts_image import IMAGE_SYSTEM_PROMPT

class PixazoImageService(BaseImageProvider):
    def __init__(self):
        self.api_key = settings.PIXAZO_SUBSCRIPTION_KEY
        self.url = "https://gateway.pixazo.ai/sd3/v1/getData"
        
    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": str(self.api_key)
        }
        
    def generate_outfit_images(self, image_url: str, styling_plan: dict):
        prompt = f"""
{IMAGE_SYSTEM_PROMPT}

Styling Plan

{json.dumps(styling_plan, indent=2)}
"""

        data = {
            "prompt": prompt,
            "negativePrompt": "dark, blurry, bad anatomy, deformed",
            "steps": 28,
            "cfg": 4.0,
            "aspect_ratio": "3:4",  # Portrait aspect ratio for fashion
            "output_format": "jpg",
            "output_quality": 90,
            "prompt_strength": 0.85
        }

        # Some APIs allow an image for img2img. We include it just in case SD3 supports it.
        # If it doesn't, it will just ignore it or act as text-to-image.
        data["image"] = image_url

        response = requests.post(self.url, json=data, headers=self._headers(), timeout=60)
        
        if response.status_code != 200:
            raise ImageGenerationError(f"Pixazo API Error: {response.text}")
            
        result = response.json()
        
        # Based on user's output: {"output": "https://..."}
        media_url = result.get("output")
        
        if not media_url:
            raise ImageGenerationError(f"Pixazo API Error: No output URL returned. Response: {result}")
            
        image_resp = requests.get(media_url, timeout=30)
        return image_resp.content
