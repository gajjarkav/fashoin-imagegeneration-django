from django import forms

from .models import Upload


class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = [
            "original_image",
        ]

        widgets = {
            "original_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".jpg, .jpeg, .png, .webp",
                }
            )
        }

        def clean_original_image(self):
            image = self.cleaned_data["original_image"]

            allowed_extensions = (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            )

            filename = image.name.lower()

            if not filename.endswith(allowed_extensions):
                raise forms.ValidationError(
                    "only JPG, JPEG, PNG, WEBP images are allowed"
                )

            max_size = 10 * 1024 * 1024

            if image.size > max_size:
                raise forms.ValidationError(
                    "maximum allowed image size is 10 MB"
                )

            return image