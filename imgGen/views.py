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

# Gemini client using API key from .env
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Folder for saving images received via webhook
IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

@csrf_exempt
def generate_image(request):
    """
    Only generate image using Gemini API.
    Returns raw image bytes (hex string) in JSON.
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

        # Only send back raw image hex to webhook (no saving here)
        image_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_bytes = part.inline_data.data
                break  # only 1 image

        if not image_bytes:
            return JsonResponse({"error": "No image generated"}, status=500)

        # Send image hex in response
        return JsonResponse({
            "image_data": image_bytes.hex(),
            "prompt": prompt
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def receive_webhook(request):
    """
    Receive webhook POST with image data and save image to MEDIA folder.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        image_hex = data.get("image_data")
        prompt = data.get("prompt", "unknown_prompt")

        if not image_hex:
            return JsonResponse({"error": "No image data received"}, status=400)

        # Convert hex to image and save
        image_bytes = bytes.fromhex(image_hex)
        image = Image.open(BytesIO(image_bytes))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}.png"
        filepath = os.path.join(IMAGE_DIR, filename)
        image.save(filepath)

        return JsonResponse({
            "status": "received",
            "saved_path": filepath,
            "prompt": prompt
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
