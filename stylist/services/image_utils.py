import uuid

from django.core.files.base import ContentFile


def image_bytes_to_content_file(
    image_bytes: bytes,
):

    return ContentFile(
        image_bytes,
        name=f"{uuid.uuid4().hex}.png",
    )