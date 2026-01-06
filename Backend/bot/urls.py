from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet,
    api_cocina_orders,
    api_cocina_mark_ready,
    api_cocina_reject,
    api_cocina_approve_payment, # 🆕
    api_cocina_reject_payment,  # 🆕
    historial,
    guardar_rating,
    gustos,
    popularidad,
    recomendacion_ml_view, 
    recomendacion_similar_view,
    recomendacion_hibrida_view,
    guardar_pedido_personalizado,
    get_or_create_session, update_session, reset_session
)
from core.views import productos_view, productos_view # Ensure it is available
from .payment_views import payment_dashboard, export_payments_csv, export_payments_excel

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),

    # Panel cocina
    # API Cocina
    path("api/cocina/orders/", api_cocina_orders, name="api_cocina_orders"),
    path("api/cocina/orders/<int:order_id>/ready/", api_cocina_mark_ready, name="api_cocina_mark_ready"),
    path("api/cocina/orders/<int:order_id>/reject/", api_cocina_reject, name="api_cocina_reject"),
    path("api/cocina/orders/<int:order_id>/approve-payment/", api_cocina_approve_payment, name="api_cocina_approve_payment"),
    path("api/cocina/orders/<int:order_id>/reject-payment/", api_cocina_reject_payment, name="api_cocina_reject_payment"),
    
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
    path("guardar_pedido_personalizado/", guardar_pedido_personalizado),
    path("productos/", productos_view, name="productos"),
    # Session API
    path("session/<int:telegram_id>/", get_or_create_session),
    path("session/update/<int:telegram_id>/", update_session),
    path("session/reset/<int:telegram_id>/", reset_session),
]
