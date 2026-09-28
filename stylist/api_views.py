import logging
import uuid
import base64
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from stylist.services.flux import FluxService, FluxServiceException

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp']
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

@csrf_exempt
def edit_image_api(request):
    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Received image edit request")

    # 1. Validate inputs
    image_file = request.FILES.get('image')
    prompt = request.POST.get('prompt')

    if not image_file:
        return JsonResponse({"success": False, "error": "Missing image file"}, status=400)
    if not prompt:
        return JsonResponse({"success": False, "error": "Missing prompt"}, status=400)

    # 2. Validate image MIME type and size
    if image_file.content_type not in ALLOWED_MIME_TYPES:
        return JsonResponse({"success": False, "error": f"Unsupported image format: {image_file.content_type}"}, status=400)
        
    if image_file.size > MAX_IMAGE_SIZE:
        return JsonResponse({"success": False, "error": "Image size exceeds 10MB limit"}, status=400)

    # 3. Read optional parameters
    try:
        width = int(request.POST.get('width', 1024))
        height = int(request.POST.get('height', 1024))
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid width or height"}, status=400)
        
    output_format = request.POST.get('output_format', 'jpeg')

    # 4. Call Azure FLUX Service
    try:
        flux_service = FluxService()
        result_image_data = flux_service.edit_image(
            image_file=image_file, 
            prompt=prompt, 
            width=width, 
            height=height, 
            output_format=output_format
        )
        
        # 5. Handle the result (URL or base64)
        if result_image_data.startswith("http://") or result_image_data.startswith("https://"):
            image_url = result_image_data
        else:
            # Decode base64 and save to storage
            if "," in result_image_data:
                # Strip data URI prefix if present
                result_image_data = result_image_data.split(",")[1]
                
            image_bytes = base64.b64decode(result_image_data)
            ext = output_format if output_format in ['jpeg', 'png', 'webp'] else 'jpg'
            file_name = f"generated/flux_{request_id}.{ext}"
            saved_path = default_storage.save(file_name, ContentFile(image_bytes))
            image_url = request.build_absolute_uri(default_storage.url(saved_path))
            
        logger.info(f"[{request_id}] Successfully generated image")
        
        return JsonResponse({
            "success": True,
            "image_url": image_url,
            "model": "FLUX.2-pro"
        })

    except FluxServiceException as e:
        logger.error(f"[{request_id}] FLUX Service Error: {e}")
        # Return generic message for internal errors unless it's a known user-facing error
        error_message = str(e)
        status_code = 502 # Bad Gateway usually for upstream errors
        if "Authentication error" in error_message or "missing" in error_message:
            error_message = "Image generation service is improperly configured."
            status_code = 500
        elif "Rate limit" in error_message:
            status_code = 429
        elif "Invalid image data" in error_message:
            status_code = 400
            
        return JsonResponse({"success": False, "error": error_message}, status=status_code)
        
    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error during image generation")
        return JsonResponse({"success": False, "error": "An unexpected error occurred"}, status=500)
