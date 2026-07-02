import replicate

from django.conf import settings

from .base_image import BaseImageProvider
from .exceptions import ImageGenerationError


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

        prompt = f"""
You are a professional celebrity fashion stylist.

Edit the uploaded image.

IMPORTANT

Keep the uploaded upper clothing EXACTLY the same.

Do NOT modify:

- shirt
- t-shirt
- hoodie
- jacket
- logo
- graphics
- print
- color
- texture
- fabric
- sleeves
- fit
- neckline

Only complete the remaining outfit.

Bottom:
{styling_plan.get("bottom", "")}

Footwear:
{styling_plan.get("footwear", "")}

Accessories:
{", ".join(styling_plan.get("accessories", []))}

Bag:
{styling_plan.get("bag", "")}

Jewelry:
{", ".join(styling_plan.get("jewelry", []))}

Reason:
{styling_plan.get("reason", "")}

Create a realistic professional full-body fashion photograph.
"""

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