from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet,
    cocina_panel,
    historial,
    guardar_rating,
    gustos,
    popularidad,
    recomendacion_ml_view, 
    recomendacion_similar_view,
    recomendacion_hibrida_view,
    guardar_pedido_personalizado,
)
from core.views import productos_view
from .payment_views import payment_dashboard, export_payments_csv, export_payments_excel

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),

    # Panel cocina
    path("cocina_panel/", cocina_panel, name="cocina_panel"),
    
    # Dashboard de pagos
    path("payment-dashboard/", payment_dashboard, name="payment_dashboard"),
    path("export-payments-csv/", export_payments_csv, name="export_payments_csv"),
    path("export-payments-excel/", export_payments_excel, name="export_payments_excel"),

    # IA
    path("historial/<int:telegram_id>/", historial, name="historial"),
    path("rating/", guardar_rating, name="guardar_rating"),
    path("gustos/<int:telegram_id>/", gustos, name="gustos"),
    path("popularidad/", popularidad, name="popularidad"),
    path("recomendacion_ml/<int:telegram_id>/", recomendacion_ml_view, name="recomendacion_ml"),
    path("recomendacion_similar/<int:telegram_id>/", recomendacion_similar_view),
    path("recomendacion_hibrida/<int:telegram_id>/", recomendacion_hibrida_view),
    path("productos/", productos_view),
    path("guardar_pedido_personalizado/", guardar_pedido_personalizado),
]
