from django.db import models

# Definición de las opciones de categorías (Sincronizado con Menu.jsx)
CATEGORY_CHOICES = [
    ('promociones', 'promociones'), 
    ('entradas', 'entradas'),
    ('principales', 'principales'),
    ('postres', 'postres'),
    ('bebidas', 'bebidas'),
]

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
    
    def __str__(self):
        # Muestra el nombre del producto en el panel de administración
        return self.name