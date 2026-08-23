from django.urls import path

from .views import upload_preview


urlpatterns = [
    path("", upload_preview, name="upload_preview"),
]