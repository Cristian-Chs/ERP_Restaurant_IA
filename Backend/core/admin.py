from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Columnas que se muestran en la lista del admin
    list_display = ("name", "price", "category", "is_active")

    # Filtros laterales
    list_filter = ("category", "is_active")

    # Barra de búsqueda
    search_fields = ("name", "description")

    # Orden por defecto
    ordering = ("category", "name")
