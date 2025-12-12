from django.contrib import admin
from .models import Product, Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "is_active")
    search_fields = ("name", "description")
    list_filter = ("category", "is_active", "ingredientes")
    filter_horizontal = ("ingredientes",)
