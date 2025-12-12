from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import notificar_pedido_listo


# ✅ Modelo principal de pedidos
class Order(models.Model):
    telegram_id = models.BigIntegerField()
    item = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="pendiente")
    fecha = models.DateTimeField(auto_now_add=True)

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
