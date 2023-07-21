from django.contrib import admin
from django.urls import path,include
from ADMIN.api.routing import websocket_urlpatterns
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/',include('USER.api.urls')),
    path('admins/',include('ADMIN.api.urls')),
    path('ws/', include(websocket_urlpatterns)),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)