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

# Folder for saving images received via webhook
IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

@csrf_exempt
def generate_image(request):
    """
    Generate image using Gemini API and return image data in JSON response.
    This endpoint does NOT save images or call any webhook.
    """
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

        # Prepare image data in memory (base64 or similar)
        image_data_list = []
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_bytes = part.inline_data.data
                image_data_list.append(image_bytes.hex())  # convert to hex string for JSON

        return JsonResponse({"images": image_data_list, "prompt": prompt})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def receive_webhook(request):
    """
    Receive webhook POST with image data and save images to MEDIA folder.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        image_hex_list = data.get("image_data", [])
        prompt = data.get("prompt", "unknown_prompt")

        saved_paths = []

        for hex_str in image_hex_list:
            image_bytes = bytes.fromhex(hex_str)
            image = Image.open(BytesIO(image_bytes))
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}.png"
            filepath = os.path.join(IMAGE_DIR, filename)
            image.save(filepath)
            saved_paths.append(filepath)

        return JsonResponse({"status": "received", "saved_paths": saved_paths, "prompt": prompt})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
