from django.contrib import admin
from django.urls import path, include
from core.views import check_user_and_get_reset_link

urlpatterns = [
    # Autenticación
    path('api/auth/check-recovery', check_user_and_get_reset_link, name="check_recovery"),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),

    # Apps
    path("api/bot/", include("bot.urls")),
    path("api/", include("core.urls")),

    # Admin
    path("admin/", admin.site.urls),
    
    # Admin de Cupones (Panel Separado)
    path("admin/coupons/", include('bot.coupon_urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
