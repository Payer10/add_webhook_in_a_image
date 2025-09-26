
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static



from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "message": "Server is running!"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('imgGen/', include('imgGen.urls')),
    path('', health_check),  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
