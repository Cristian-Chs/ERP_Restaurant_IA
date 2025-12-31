# core/urls.py 
from django.urls import path
from .views import MenuListView, listar_ingredientes, filtrar_productos, productos_view, check_user_and_get_reset_link

urlpatterns = [
    path("products/", MenuListView.as_view(), name="menu-list-grouped"),
    path("ingredientes/", listar_ingredientes, name="listar_ingredientes"),
    path("productos/", filtrar_productos, name="filtrar_productos"),
    path("productos/", productos_view),
    path("auth/check-recovery", check_user_and_get_reset_link, name="check_recovery"),
]