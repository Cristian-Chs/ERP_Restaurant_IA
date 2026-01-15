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


# ✅ Ingredientes
class Ingredient(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    disponible_como_extra = models.BooleanField(default=False)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    UNIT_CHOICES = [
        ('kg', 'Kilogramo (kg)'),
        ('und', 'Unidad (und)'),
        ('l', 'Litro (l)'),
    ]
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES, default='und')
    
    def __str__(self):
        return self.nombre


# ✅ Sabores (Ej: Pollo, Cazón, Queso)
class Flavor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


# ✅ Producto unificado (React + Ingredientes)
class Product(models.Model):
    # Campos del panel React
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # ✅ Nuevo: Precio de Costo
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
    
    # Sabores disponibles para este producto
    sabores = models.ManyToManyField(Flavor, related_name="productos", blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

# ✅ RRHH: Empleados
class Employee(models.Model):
    ROLE_CHOICES = [
        ('CHEF', 'Cocinero/Chef'),
        ('WAITER', 'Mesero'),
        ('DELIVERY', 'Repartidor'),
        ('MANAGER', 'Gerente'),
        ('OTHER', 'Otro'),
    ]
    
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OTHER')
    phone = models.CharField(max_length=20, blank=True, null=True)
    salary_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

# ✅ RRHH: Pagos de Nómina
class PayrollPayment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Pago {self.amount} a {self.employee.name} ({self.payment_date})"

# ✅ INVENTARIO: Recetas (Relación Producto-Ingrediente con Cantidades)
class Recipe(models.Model):
    """
    Define la receta de un producto: qué ingredientes lleva y en qué cantidad.
    Permite calcular el costo real de cada producto dinámicamente.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recetas")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="recetas")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, help_text="Cantidad del ingrediente necesaria")
    # La unidad se toma del ingrediente (ingredient.unit)
    
    class Meta:
        unique_together = ('product', 'ingredient')
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.ingredient.unit} de {self.ingredient.nombre}"
    
    def get_cost(self):
        """Calcula el costo de este ingrediente en la receta"""
        return self.ingredient.cost * self.quantity

# ✅ INVENTARIO: Movimientos de Inventario
class InventoryMovement(models.Model):
    """
    Registra todos los movimientos de inventario (compras, uso, ajustes).
    Permite análisis histórico con Pandas para proyección de compras.
    """
    MOVEMENT_TYPES = [
        ('PURCHASE', 'Compra'),
        ('USAGE', 'Uso en Producción'),
        ('ADJUSTMENT', 'Ajuste de Inventario'),
        ('WASTE', 'Desperdicio'),
    ]
    
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="movimientos")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Costo por unidad en este movimiento")
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.quantity} {self.ingredient.unit} de {self.ingredient.nombre} ({self.date.strftime('%Y-%m-%d')})"
    
    def get_total_cost(self):
        """Calcula el costo total de este movimiento"""
        return self.quantity * self.cost_per_unit

# ✅ CONFIGURACIONES GLOBALES (Tasa de cambio, etc)
class GlobalSetting(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default
