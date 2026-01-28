from django.contrib import admin
from .models import Product, Ingredient, Flavor, Employee, PayrollPayment, Recipe, InventoryMovement



@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)

@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "is_active")
    search_fields = ("nombre",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "is_active")
    search_fields = ("name", "description")
    list_filter = ("category", "is_active")
    filter_horizontal = ("ingredientes", "sabores")

#  RRHH
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "salary_base", "is_active")
    search_fields = ("name",)
    list_filter = ("role", "is_active")

@admin.register(PayrollPayment)
class PayrollPaymentAdmin(admin.ModelAdmin):
    list_display = ("employee", "amount", "payment_date")
    search_fields = ("employee__name",)
    list_filter = ("payment_date",)

#  Inventario
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("product", "ingredient", "quantity")
    search_fields = ("product__name", "ingredient__nombre")
    list_filter = ("product__category",)

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "movement_type", "quantity", "cost_per_unit", "date")
    search_fields = ("ingredient__nombre",)
    list_filter = ("movement_type", "date")
    date_hierarchy = "date"

