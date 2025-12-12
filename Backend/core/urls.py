# core/urls.py 
from django.urls import path
from .views import MenuListView, listar_ingredientes, filtrar_productos

urlpatterns = [
    path("products/", MenuListView.as_view(), name="menu-list-grouped"),
    path("ingredientes/", listar_ingredientes, name="listar_ingredientes"),
    path("productos/", filtrar_productos, name="filtrar_productos"),
]
