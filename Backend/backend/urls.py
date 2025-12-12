from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Autenticación
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),

    # Apps
    path("bot/", include("bot.urls")),
    path("core/", include("core.urls")),

    # Admin
    path("admin/", admin.site.urls),
]
