from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import notificar_pedido_listo


# ✅ Modelo principal de pedidos
class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending_payment', 'Esperando Pago'),
        ('payment_submitted', 'Pago Enviado'),
        ('payment_approved', 'Pago Aprobado'),
        ('payment_rejected', 'Pago Rechazado'),
    ]
    
    telegram_id = models.BigIntegerField()
    item = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=50, default="pendiente")
    fecha = models.DateTimeField(auto_now_add=True)
    
    # ✅ Campos de verificación de pago
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending_payment'
    )
    payment_receipt_file_id = models.CharField(max_length=255, blank=True, null=True)
    payment_verified_at = models.DateTimeField(blank=True, null=True)
    payment_verified_by = models.BigIntegerField(blank=True, null=True)
    payment_data = models.JSONField(blank=True, null=True)  # Datos extraídos del comprobante

    def __str__(self):
        return f"{self.item} - Cliente {self.telegram_id}"


# ✅ Rating de platos (para IA)
class Rating(models.Model):
    telegram_id = models.BigIntegerField()
    plato = models.CharField(max_length=255)
    estrellas = models.IntegerField(choices=[(i, f"{i} ⭐") for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plato} - {self.estrellas}⭐ - {self.telegram_id}"


# ✅ Gustos del cliente (para IA personalizada)
class GustoCliente(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    gustos = models.JSONField(default=list)  # Ej: ["pollo", "queso", "pasta"]

    def __str__(self):
        return f"Gustos de {self.telegram_id}"


# ✅ Notificación automática cuando un pedido cambia a "listo"
@receiver(post_save, sender=Order)
def enviar_notificacion(sender, instance, **kwargs):
    if instance.status == "listo":
        notificar_pedido_listo(instance.telegram_id, instance.item)

class PedidoPersonalizado(models.Model):
    telegram_id = models.BigIntegerField()
    producto = models.CharField(max_length=255)
    removidos = models.JSONField(default=list)   # ["Tomate", "Mostaza"]
    agregados = models.JSONField(default=list)   # ["Cebolla extra"]
    pedido_final = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.producto} ({self.telegram_id})"
    
class PreferenciaIngrediente(models.Model):
    telegram_id = models.BigIntegerField()
    ingrediente = models.CharField(max_length=100)
    gusta = models.BooleanField()  # True = le gusta, False = no le gusta
    contador = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.ingrediente} ({'gusta' if self.gusta else 'no gusta'})"



