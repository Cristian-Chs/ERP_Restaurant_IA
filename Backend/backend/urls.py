from core.views import check_user_and_get_reset_link

urlpatterns = [
    # Autenticación
    path('api/auth/check-recovery', check_user_and_get_reset_link, name="check_recovery"),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),

    # Apps
    path("bot/", include("bot.urls")),
    path("core/", include("core.urls")),
    path("api/", include("core.urls")), # ✅ Fix para React (Menu.jsx busca /api/products/)

    # Admin
    path("admin/", admin.site.urls),
]
