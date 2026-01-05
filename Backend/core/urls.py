# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuListView, listar_ingredientes, filtrar_productos,
    productos_view, check_user_and_get_reset_link,
    ProductViewSet, IngredientViewSet, FlavorViewSet, AdminStatsView, SalesPredictionView, TelegramLoginView
)

router = DefaultRouter()
router.register(r'products-admin', ProductViewSet, basename='product-admin')
router.register(r'ingredients-admin', IngredientViewSet, basename='ingredient-admin')
router.register(r'flavors-admin', FlavorViewSet, basename='flavor-admin')

urlpatterns = [
    path('', include(router.urls)),
    path("products/", MenuListView.as_view(), name="menu-list-grouped"),
    path("ingredientes/", listar_ingredientes, name="listar_ingredientes"),
    path("productos/", filtrar_productos, name="filtrar_productos"),
    path("productos/", productos_view),

    # Dashboard stats
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("admin/prediction/", SalesPredictionView.as_view(), name="admin-prediction"),
    path("auth/telegram/", TelegramLoginView.as_view(), name="telegram-auth"),
]