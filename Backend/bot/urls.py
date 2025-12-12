from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet,
    cocina_panel,
    historial,
    guardar_rating,
    gustos,
    popularidad,
    recomendacion_ml_view
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),

    # Panel cocina
    path("cocina_panel/", cocina_panel, name="cocina_panel"),

    # IA
    path("historial/<int:telegram_id>/", historial, name="historial"),
    path("rating/", guardar_rating, name="guardar_rating"),
    path("gustos/<int:telegram_id>/", gustos, name="gustos"),
    path("popularidad/", popularidad, name="popularidad"),
    path("recomendacion_ml/<int:telegram_id>/", recomendacion_ml_view, name="recomendacion_ml"),
]
