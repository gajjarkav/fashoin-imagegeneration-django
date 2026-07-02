import uuid

from django.db import models
from .constants import ThemeChoices


class TimeStampedUUIDModels(models.Model):
    """Abstract base model"""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True

class Upload(TimeStampedUUIDModels):
    """original uploaded clothing image"""

    original_image = models.ImageField(
        upload_to="uploads/",
    )

    def __str__(self):
        return f"Upload #{self.id}"


class ClothingAnalysis(TimeStampedUUIDModels):
    """one AI analysis per uploads"""

    upload = models.OneToOneField(
        Upload,
        on_delete=models.CASCADE,
        related_name="analysis",
    )

    category = models.CharField(
        max_length=100,
    )

    dominant_color = models.CharField(
        max_length=100,
    )

    analysis_json = models.JSONField(
        default=dict,
    )

    def __str__(self):
        return f"{self.category} ({self.dominant_color})"


class StyleSession(TimeStampedUUIDModels):
    """one styling request"""

    analysis = models.ForeignKey(
        ClothingAnalysis,
        on_delete=models.CASCADE,
        related_name="style_session",
    )

    theme = models.CharField(
        max_length=30,
        choices=ThemeChoices.choices,
    )

    user_prompt = models.TextField(
        blank=True,
    )

    recommendation_json = models.JSONField(
        default=dict,
    )

    def __str__(self):
        return f"{self.get_theme_display()} | Session #{self.id}"

class GeneratedImage(TimeStampedUUIDModels):
    """generated outfit image"""

    style_session = models.ForeignKey(
        StyleSession,
        on_delete=models.CASCADE,
        related_name="generated_images",
    )

    generated_image = models.ImageField(
        upload_to="generated/",
    )

    option_number = models.PositiveSmallIntegerField()

    generation_prompt = models.TextField()

    def __str__(self):
        return (
            f"{self.style_session.get_theme_display()} "
            f"- Option {self.option_number}"
        )