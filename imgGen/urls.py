from django.urls import path
from .views import generate_image, receive_webhook

urlpatterns = [
    path("generate/", generate_image),
    path("webhook/", receive_webhook),
]
