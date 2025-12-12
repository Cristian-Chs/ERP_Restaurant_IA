from django.db import models

# Definición de las opciones de categorías (Sincronizado con Menu.jsx)
CATEGORY_CHOICES = [
    ('promociones', 'promociones'), 
    ('entradas', 'entradas'),
    ('principales', 'principales'),
    ('postres', 'postres'),
    ('bebidas', 'bebidas'),
]

from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    rol = models.CharField(default='cliente', max_length=20)


class Product(models.Model):
    # Campos de Datos
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campo para el nombre del archivo de la imagen (lo que espera React)
    imagen = models.CharField(
        max_length=100,
        blank=True,  # Permite que el campo esté vacío en el formulario de Admin
        null=True    # Permite valores NULL en la base de datos
    )
    
    # Campo de categoría
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='promociones', 
    )
    
    # Campo de estado (para activar/desactivar el producto)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        # Esto asegura un orden lógico cuando se recuperan los datos
        ordering = ['category', 'name']


class Ingredient(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Product(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    ingredientes = models.ManyToManyField(Ingredient, related_name="productos")

    def __str__(self):
        return self.nombre

    def __str__(self):
        # Muestra el nombre del producto en el panel de administración
        return self.name