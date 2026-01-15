from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
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
    # Admin de Cupones (Panel Separado)
    path("admin/coupons/", include('bot.coupon_urls')),

    # Frontend React (Catch-all)
    path("", TemplateView.as_view(template_name="index.html")),
    re_path(r'^(?!api|admin|static|media).*$', TemplateView.as_view(template_name='index.html')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
