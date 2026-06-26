from .order_views import OrderViewSet
from .kitchen_views import (
    api_cocina_orders,
    api_cocina_payments_all,
    api_cocina_approve_payment,
    api_cocina_reject_payment,
    api_cocina_mark_ready,
    api_cocina_reject,
    api_get_invoice,
)
from .recommendation_views import (
    historial,
    guardar_rating,
    gustos,
    popularidad,
    recomendacion_ml_view,
    recomendacion_similar_view,
    recomendacion_hibrida_view,
    guardar_pedido_personalizado,
)
from .session_views import (
    get_or_create_session,
    update_session,
    reset_session,
    get_loyalty_points,
)
from .coupon_views import (
    coupon_list_create,
    coupon_detail,
    coupon_redemptions,
    validate_coupon,
)
from .route_views import calculate_route_view
