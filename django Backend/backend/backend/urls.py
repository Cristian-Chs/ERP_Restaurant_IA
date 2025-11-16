# backend/urls.py (COMPLETO Y CORREGIDO - Archivo principal)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Rutas de Autenticación de la API (Djoser/JWT)
    path('api/auth/', include('djoser.urls')),      # /api/auth/users/ (Registro)
    path('api/auth/', include('djoser.urls.jwt')),  # /api/auth/jwt/create/ (Login)

    # 2. Rutas de la Aplicación Core (Tu ProductViewSet)
    # Esto dirigirá a core/urls.py
    path('api/', include('core.urls')), 
    
    # 3. Panel de Administración
    path('admin/', admin.site.urls),
]