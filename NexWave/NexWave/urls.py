from django.contrib import admin
from django.urls import path,include
from ADMIN.api.routing import websocket_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/',include('USER.api.urls')),
    path('admins/',include('ADMIN.api.urls')),
    path('ws/', include(websocket_urlpatterns)),
]