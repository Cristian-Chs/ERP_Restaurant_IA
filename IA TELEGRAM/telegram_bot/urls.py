from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("recomendacion/", include("recomendacion.urls")),
    path('', include('bot.urls')),  # 👈 Incluye las rutas de tu app 'bot'
]
