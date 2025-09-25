from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.conf import settings
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import requests

# Gemini client using API key from .env
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Folder for saving images
IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

FIXED_WEBHOOK_URL = settings.WEBHOOK_URL

@csrf_exempt
def generate_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        prompt = data.get("prompt")
        if not prompt:
            return JsonResponse({"error": "prompt missing"}, status=400)

        # Generate image using Gemini SDK
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt],
        )

        image_saved_paths = []

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image = Image.open(BytesIO(part.inline_data.data))
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{timestamp}.png"
                filepath = os.path.join(IMAGE_DIR, filename)
                image.save(filepath)
                image_saved_paths.append(filepath)

        # Call fixed webhook URL
        if FIXED_WEBHOOK_URL:
            try:
                requests.post(FIXED_WEBHOOK_URL, json={"image_paths": image_saved_paths, "prompt": prompt})
            except Exception as e:
                print("Webhook failed:", e)

        return JsonResponse({"image_paths": image_saved_paths, "prompt": prompt})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def receive_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    try:
        data = json.loads(request.body)
        print("Webhook received:", data)
        return JsonResponse({"status": "received",'data':data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
