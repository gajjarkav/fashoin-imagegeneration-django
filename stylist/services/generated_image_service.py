from .image_utils import image_bytes_to_content_file
from stylist.models import GeneratedImage


class GeneratedImageService:

    @staticmethod
    def save(
        style_session,
        option_number,
        image_bytes,
        prompt,
    ):

        image = GeneratedImage(
            style_session=style_session,
            option_number=option_number,
            generation_prompt=prompt,
        )

        image.generated_image.save(
            f"generated_{option_number}.png",
            image_bytes_to_content_file(
                image_bytes,
            ),
            save=True,
        )

        return image