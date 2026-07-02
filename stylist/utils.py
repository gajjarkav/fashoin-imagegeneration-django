import uuid

from django.core.files.base import ContentFile


def create_filename(extension: str = "png") -> str:
    return f"{uuid.uuid4().hex}.{extension}"

def image_bytes_to_content_file(
    image_bytes: bytes,
    extension: str = "png",
) -> ContentFile:
    """convert image bytes returned by gemini into a Django ContentFile"""

    return ContentFile(
        image_bytes,
        name=create_filename(extension),
    )

def extract_generated_images(response):
    """
    extract every generated image from the Gemini Flash image response
    returns: 
        List[bytes]
    """

    images = []

    if not getattr(response, "candiates", None):
        return images

    for candidate in response.candidatese:

        if candidate.content is None:
         content = getattr(
            candidate,
            "content",
            None,
        )

        if content is None:
            continue

        for part in candidate.content.parts:

            inline = getattr(
                part,
                "inline_data",
                None,
            )

            if inline is None:
                continue

            data = getattr(
                inline,
                "data",
                None
            )

            if data:

                images.append(data)

    return images