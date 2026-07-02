from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest

from .forms import UploadForm
from .models import (
    Upload,
    ClothingAnalysis,
    StyleSession,
    GeneratedImage,
)
from .services import WorkflowService
from .services.generated_image_service import GeneratedImageService
from .services.imagekit import ImageKitService


def home(request):
    return render(request, "stylist/home.html")


def upload_image(request):

    if request.method == "POST":

        form = UploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            upload = form.save()

            return redirect(
                "stylist:analysis",
                upload.uuid,
            )

    else:

        form = UploadForm()

    return render(
        request,
        "stylist/upload.html",
        {
            "form": form,
        },
    )

def analysis(request, uuid):

    upload = get_object_or_404(
        Upload,
        uuid=uuid,
    )

    workflow = WorkflowService()

    try:

        analysis = ClothingAnalysis.objects.filter(
            upload=upload,
        ).first()

        if analysis is None:


            result = workflow.run_analysis(
                upload
            )

            analysis = ClothingAnalysis.objects.create(
                upload=upload,
                category=result.get("category", ""),
                dominant_color=result.get("primary_color", ""),
                analysis_json=result,
            )

        style_session = StyleSession.objects.filter(
            analysis=analysis
        ).first()

        if style_session is None:

            style_json = workflow.run_style_planner(
                analysis.analysis_json,
            )

            style_session = StyleSession.objects.create(
                analysis=analysis,
                theme="CASUAL",
                recommendation_json=style_json,
            )

        return redirect(
            "stylist:results",
            uuid=upload.uuid,
        )

    except Exception as exc:
        raise
        # return render(
        #     request,
        #     "stylist/error.html",
        #     {
        #         "error": str(exc),
        #         "upload": upload
        #     },
        #     status=500
        # )


def chat(request, uuid):

    upload = get_object_or_404(
        Upload,
        uuid=uuid
    )

    analysis = get_object_or_404(
        ClothingAnalysis,
        upload=upload
    )

    style_session = (
        StyleSession.objects.filter(
            analysis=analysis,
        ).latest("created_at",)
    )

    generated_images = GeneratedImage.objects.filter(
        style_session=style_session,
    )

    if request.method == "POST":

        user_prompt = request.POST.get(
            "message",
            ""
        ).strip()

        if user_prompt:
            workflow = WorkflowService()

            previous_plan = (
                style_session.recommendation_json
            )

            response = workflow.run_refinement(
                upload,
                previous_plan,
                user_prompt,
            )

            images = response

            option = (generated_images.count() + 1)

            GeneratedImageService.save(
                style_session=style_session,
                option_number=option,
                image_bytes=image_bytes,
                prompt=user_prompt,
            )

            return redirect(
                "stylist:chat",
                uuid=upload.uuid,
            )

    generated_images = GeneratedImage.objects.filter(
        style_session=style_session,
    )

    return render(
        request,
        "stylist/chat.html",
        {
            "upload": upload,
            "analysis": analysis,
            "style_session": style_session,
            "generated_images": generated_images,
        },
    )


def results(request, uuid):

    upload = get_object_or_404(
        Upload,
        uuid=uuid
    )

    analysis = get_object_or_404(
        ClothingAnalysis,
        upload=upload,
    )

    style_session = (
        StyleSession.objects.filter(analysis=analysis).latest("created_at",)
    )

    generated_images = GeneratedImage.objects.filter(
        style_session=style_session
    )

    return render(
        request,
        "stylist/results.html",
        {
            "upload": upload,
            "analysis": analysis,
            "style_session": style_session,
            "generated_images": generated_images,
        },
    )


def generate_image(request, uuid):

    if request.method != "POST":
        return HttpResponseBadRequest()

    upload = get_object_or_404(
        Upload,
        uuid=uuid
    )

    analysis = get_object_or_404(
        ClothingAnalysis,
        upload=upload,
    )

    style_session = (StyleSession.objects.filter(analysis=analysis).latest("created_at"))

    outfit_index = int(request.POST.get("outfit_index", -1))

    outfits = style_session.recommendation_json.get(
        "outfits", []
    )

    if outfit_index < 0 or outfit_index >= len(outfits):
        return HttpResponseBadRequest()

    workflow = WorkflowService()

    try: 
        imagekit = ImageKitService()

        public_url = imagekit.upload_image(
            upload.original_image.path,
        )

        response = workflow.image_router.generate_image(
            public_url,
            outfits[outfit_index],
        )

        option_number = (
            GeneratedImage.objects.filter(
                style_session=style_session,
            ).count() + 1
        )

        GeneratedImageService.save(
            style_session=style_session,
            option_number=option_number,
            image_bytes=response,
            prompt=str(
                outfits[outfit_index],
            ),
        )

        option_number += 1

        return redirect(
            "stylist:results",
            uuid=upload.uuid,
        )

    except Exception as exc:

        return render(
            request,
            "stylist/error.html",
            {
                "error": str(exc),
                "upload": upload,
            },
            status=500,
        )