from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import notificar_pedido_listo  # 👈 import limpio

class UserPreference(models.Model):
    telegram_id = models.BigIntegerField()
    preference = models.CharField(max_length=255)
    liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserKnowledge(models.Model):
    telegram_id = models.BigIntegerField()
    topic = models.CharField(max_length=255)
    content = models.TextField()
    learned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    telegram_id = models.BigIntegerField()
    item = models.CharField(max_length=255)
    status = models.CharField(
        max_length=50,
        choices=[("pendiente", "Pendiente"), ("preparando", "Preparando"), ("listo", "Listo")],
        default="pendiente"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item} - Cliente {self.telegram_id}"

@receiver(post_save, sender=Order)
def enviar_notificacion(sender, instance, **kwargs):
    if instance.status == "listo":
        notificar_pedido_listo(instance.telegram_id, instance.item)
