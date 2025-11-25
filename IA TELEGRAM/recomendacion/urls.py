from django.urls import path
from .views import recomendaciones_cliente

urlpatterns = [
    path("cliente/<int:telegram_id>/", recomendaciones_cliente, name="recomendaciones_cliente"),
]
