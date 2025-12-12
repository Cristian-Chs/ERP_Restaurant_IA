from django.db import models
from django.contrib.auth.models import AbstractUser

# ✅ Categorías sincronizadas con React
CATEGORY_CHOICES = [
    ('promociones', 'promociones'),
    ('entradas', 'entradas'),
    ('principales', 'principales'),
    ('postres', 'postres'),
    ('bebidas', 'bebidas'),
]


# ✅ Usuario personalizado (si lo usas)
'''class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    rol = models.CharField(default='cliente', max_length=20)
'''

# ✅ Ingredientes
class Ingredient(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


# ✅ Producto unificado (React + Ingredientes)
class Product(models.Model):
    # Campos del panel React
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.CharField(max_length=100, blank=True, null=True)

    # Categoría
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='promociones',
    )

    # Estado
    is_active = models.BooleanField(default=True)

    # Ingredientes (para filtros e IA)
    ingredientes = models.ManyToManyField(Ingredient, related_name="productos", blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name
