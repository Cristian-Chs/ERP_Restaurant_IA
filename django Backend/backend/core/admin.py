from django.contrib import admin

# Register your models here.

from .models import Product # Asegúrate de que el nombre del modelo es correcto (Product)

# Opción Sencilla (Recomendada para empezar):
admin.site.register(Product)