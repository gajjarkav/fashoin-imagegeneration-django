from django.conf import settings

from .gemini import GeminiService

class ImageRouter:

    PROVIDERS = {
        "gemini": GeminiService,
    }

    def __init__(self):

        provider = getattr(
            settings,
            "IMAGE_PROVIDER",
            "gemini",
        ).lower()

        provider_cls = self.PROVIDERS.get(
            provider,
            GeminiService,
        )

        self.provider = provider_cls()

    def generate_image(
        self,
        image_path,
        styling_plan,
    ):

        return self.provider.generate_outfit_images(
            image_path,
            styling_plan,
        )