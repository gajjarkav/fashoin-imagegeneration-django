from pathlib import Path
import base64

import requests
from django.conf import settings

from .exceptions import ImageGenerationError


class ImageKitService:

    BASE_URL = "https://upload.imagekit.io/api/v1/files/upload"

    def __init__(self):

        self.private_key = settings.IMAGEKIT_PRIVATE_KEY

    def upload_image(
        self,
        image_path: str,
    ) -> str:

        path = Path(image_path)

        with open(path, "rb") as image:

            encoded = base64.b64encode(
                image.read()
            ).decode("utf-8")

        data = {
            "file": encoded,
            "fileName": path.name,
            "useUniqueFileName": "true",
            "folder": "/fashion_uploads",
        }

        response = requests.post(
            self.BASE_URL,
            auth=(self.private_key, ""),
            data=data,
            timeout=120,
        )

        if response.status_code != 200:

            raise ImageGenerationError(
                f"ImageKit Upload Failed\n{response.text}"
            )

        result = response.json()

        return result["url"]

    def delete_image(
        self,
        file_id: str,
    ):

        response = requests.delete(
            f"https://api.imagekit.io/v1/files/{file_id}",
            auth=(self.private_key, ""),
            timeout=60,
        )

        if response.status_code not in (200, 204):
            raise ImageGenerationError(response.text)

    def generate_outfit_images(
        self,
        image_url: str,
        styling_plan: dict,
    ):
        import urllib.parse

        prompt_parts = []
        if styling_plan.get("bottom"):
            prompt_parts.append(styling_plan["bottom"])
        if styling_plan.get("footwear"):
            prompt_parts.append(styling_plan["footwear"])
            
        prompt = "model wearing this with " + " and ".join(prompt_parts)
        
        # ImageKit uses dashes for spaces in prompts
        encoded_prompt = urllib.parse.quote(prompt.replace(" ", "-").replace("/", "-").strip())
        
        # Append the transformation query parameter
        if "?" in image_url:
            gen_url = f"{image_url}&tr=e-changebg-prompt-{encoded_prompt}"
        else:
            gen_url = f"{image_url}?tr=e-changebg-prompt-{encoded_prompt}"
            
        # Add a random query param to bust cache
        import random
        gen_url += f"&cb={random.randint(1, 100000)}"

        response = requests.get(gen_url, timeout=60)

        if response.status_code not in (200, 201, 202):
            raise ImageGenerationError(
                f"ImageKit AI generation failed: {response.text}"
            )

        return response.content