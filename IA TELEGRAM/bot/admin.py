from django.contrib import admin
from .models import Order
from telegram import Bot

def notificar_cliente(order):
    """
    Envía un mensaje al cliente en Telegram cuando su pedido está listo.
    """
    bot = Bot(token="8265846340:AAFNOqStooRqkiwxV-GdYG8EaEd-r8mPsHw")  # 👈 Usa el token del bot cocina
    bot.send_message(
        chat_id=order.telegram_id,
        text=f"🍽️ Tu pedido '{order.item}' está listo para recoger o servir. ¡Buen provecho!"
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("item", "telegram_id", "status", "created_at")
    list_filter = ("status",)
    actions = ["marcar_listo"]

    def marcar_listo(self, request, queryset):
        """
        Acción en el panel de administración para marcar pedidos como listos
        y notificar automáticamente al cliente.
        """
        for order in queryset:
            order.status = "listo"
            order.save()
            notificar_cliente(order)  # 👈 aquí notificas al cliente
        self.message_user(request, "Pedidos marcados como listos.")

    marcar_listo.short_description = "Marcar pedidos seleccionados como listos"
