from django.contrib import admin

from .models import (
    ClothingAnalysis,
    GeneratedImage,
    StyleSession,
    Upload,
)


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "uuid",
        "created_at",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "uuid",
    )

    ordering = (
        "-created_at",
    )


@admin.register(ClothingAnalysis)
class ClothingAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "category",
        "dominant_color",
        "created_at",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
        "analysis_json",
    )

    search_fields = (
        "category",
        "dominant_color",
    )

    ordering = (
        "-created_at",
    )


@admin.register(StyleSession)
class StyleSessionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "theme",
        "created_at",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
        "recommendation_json",
    )

    list_filter = (
        "theme",
    )

    ordering = (
        "-created_at",
    )


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "style_session",
        "option_number",
        "created_at",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )