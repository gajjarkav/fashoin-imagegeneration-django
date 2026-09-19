import replicate

from django.conf import settings

from .base_image import BaseImageProvider
from .exceptions import ImageGenerationError
from .prompts_image import build_outfit_edit_prompt


class ReplicateImageService(BaseImageProvider):

    MODEL = "black-forest-labs/flux-kontext-pro"

    def __init__(self):

        self.client = replicate.Client(
            api_token=settings.REPLICATE_API_TOKEN,
        )

    def generate_outfit_images(
        self,
        image_url: str,
        styling_plan: dict,
    ):

        prompt = build_outfit_edit_prompt(styling_plan)

        output = self.client.run(
            self.MODEL,
            input={
                "prompt": prompt,
                "input_image": image_url,
                "output_format": "png",
            },
        )

        if isinstance(output, list):
            output = output[0]

        return output.read()