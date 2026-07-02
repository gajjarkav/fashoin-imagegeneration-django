from django.conf import settings

from .cloudflare import CloudflareImageService
from .gemini import GeminiService
from .replicate import ReplicateImageService


class ImageRouter:

    PROVIDERS = {
        "gemini": GeminiService,
        "cloudflare": CloudflareImageService,
        "replicate": ReplicateImageService,
    }

    def __init__(self):

        provider = getattr(
            settings,
            "IMAGE_PROVIDER",
            "replicate",
        ).lower()

        provider_cls = self.PROVIDERS.get(
            provider,
            ReplicateImageService,
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