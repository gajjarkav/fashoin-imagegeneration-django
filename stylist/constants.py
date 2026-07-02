from django.db import models


class ThemeChoices(models.TextChoices):
    CASUAL = "CASUAL", "Casual"
    OFFICE = "OFFICE", "Office"
    PARTY = "PARTY", "Party"
    DATE_NIGHT = "DATE_NIGHT", "Date Night"
    COLLEGE = "COLLEGE", "College"
    VACATION = "VACATION", "Vacation"
    WINTER = "WINTER", "Winter"
    SUMMER = "SUMMER", "Summer"
    TRADITIONAL = "TRADITIONAL", "Traditional"

IMAGE_EXTENSION = ".png"

DEFAULT_ASPECT_RATIO = "3:4"

DEFAULT_TIMEOUT = 180

DEFAULT_PROVIDER = "cloudflare"