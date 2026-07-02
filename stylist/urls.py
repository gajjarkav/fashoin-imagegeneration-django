from django.urls import path

from . import views


app_name = "stylist"

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload_image, name="upload"),
    path("analysis/<uuid:uuid>/", views.analysis, name="analysis"),
    path("results/<uuid:uuid>/", views.results, name="results"),
    path("chat/<uuid:uuid>/", views.chat, name="chat"),
    path("generate-image/<uuid:uuid>/", views.generate_image, name="generate_image")
]
