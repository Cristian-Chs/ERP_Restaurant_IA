from django.contrib import admin
from .models import Order
from telegram import Bot

# ⚙️ Configuración
BOT_TOKEN_CLIENTE = "TU_TOKEN_DEL_BOT_CLIENTE"   # 👈 pon aquí el token real del bot cliente
CHEF_CHAT_ID = 1234567890                        # 👈 reemplaza con el ID real del chef

def notificar_cliente(order):
    """
    Envía un mensaje al cliente en Telegram cuando su pedido está listo.
    """
    bot = Bot(token=BOT_TOKEN_CLIENTE)
    bot.send_message(
        chat_id=order.telegram_id,
        text=f"🍽️ Tu pedido '{order.item}' está listo para recoger o servir. ¡Buen provecho!"
    )

def notificar_chef(order):
    """
    Envía un mensaje al chef para informarle que el pedido está listo.
    """
    bot = Bot(token=BOT_TOKEN_CLIENTE)
    mensaje = (
        f"👨‍🍳 Pedido marcado como LISTO:\n\n"
        f"{order.item}\n\n"
        f"📲 Cliente ID: {order.telegram_id}\n"
        f"🕒 Hora: {order.created_at.strftime('%d/%m/%Y %H:%M')}"
    )
    bot.send_message(chat_id=CHEF_CHAT_ID, text=mensaje)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("resumen_item", "telegram_id", "status", "created_at")
    list_filter = ("status",)
    actions = ["marcar_listo"]

    def resumen_item(self, obj):
        """
        Muestra una versión limpia y corta del campo 'item' en el panel.
        """
        texto = obj.item
        texto = texto.replace("Quiero pedir.", "")
        texto = texto.replace("Aquí está mi resumen:", "")
        texto = texto.replace("Por favor, confirma mi pedido.", "")
        texto = texto.replace("*", "")
        texto = texto.strip()
        return texto[:80] + "..." if len(texto) > 80 else texto

    resumen_item.short_description = "Resumen del Pedido"

    def marcar_listo(self, request, queryset):
        """
        Acción en el panel de administración para marcar pedidos como listos
        y notificar automáticamente al cliente y al chef.
        """
        for order in queryset:
            order.status = "listo"
            order.save()
            notificar_cliente(order)  # ✅ Notifica al cliente
            notificar_chef(order)     # ✅ Notifica al chef
        self.message_user(request, "Pedidos marcados como listos.")

    marcar_listo.short_description = "Marcar pedidos seleccionados como listos"
