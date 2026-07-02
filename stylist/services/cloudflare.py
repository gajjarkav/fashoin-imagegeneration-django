import base64

import requests
from django.conf import settings

from .base_image import BaseImageProvider
from .exceptions import ImageGenerationError


class CloudflareImageService(BaseImageProvider):

    MODEL = "pruna/p-image-edit"

    def __init__(self):

        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = settings.CLOUDFLARE_API_TOKEN

        self.url = (
            f"https://api.cloudflare.com/client/v4/"
            f"accounts/{self.account_id}/ai/run"
        )

    def _headers(self):

        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def generate_outfit_images(
        self,
        image_url: str,
        styling_plan: dict,
    ):

        prompt = f"""
Create a realistic professional fashion photograph.

DO NOT modify:
- shirt
- tshirt
- hoodie
- jacket
- logo
- print
- graphics
- fabric
- color
- texture

Only complete the outfit.

Bottom:
{styling_plan.get("bottom", "")}

Footwear:
{styling_plan.get("footwear", "")}

Accessories:
{styling_plan.get("accessories", "")}

Bag:
{styling_plan.get("bag", "")}

Jewelry:
{styling_plan.get("jewelry", "")}

Reason:
{styling_plan.get("reason", "")}
"""

        payload = {
            "model": self.MODEL,
            "input": {
                "prompt": prompt,
                "images": [
                    image_url,
                ],
                "aspect_ratio": "3:4",
            },
        }

        response = requests.post(
            self.url,
            headers=self._headers(),
            json=payload,
            timeout=300,
        )

        if response.status_code != 200:

            try:
                error = response.json()
            except Exception:
                error = response.text

            raise ImageGenerationError(error)

        result = response.json()

        if not result.get("success", False):

            raise ImageGenerationError(result)

        image = result["result"]["image"]

        if image.startswith("data:image"):

            image = image.split(",", 1)[1]

        return base64.b64decode(image)