from django.contrib import admin
from telegram import Bot
from .models import Order, Rating, GustoCliente

# ⚙️ Configuración
BOT_TOKEN_CLIENTE = "537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU"
CHEF_CHAT_ID = 1234567890


def notificar_cliente(order):
    bot = Bot(token=BOT_TOKEN_CLIENTE)
    bot.send_message(
        chat_id=order.telegram_id,
        text=f"🍽️ Tu pedido '{order.item}' está listo. ¡Buen provecho!"
    )


def notificar_chef(order):
    bot = Bot(token=BOT_TOKEN_CLIENTE)
    mensaje = (
        f"👨‍🍳 Pedido LISTO:\n\n"
        f"{order.item}\n\n"
        f"📲 Cliente: {order.telegram_id}\n"
        f"🕒 Hora: {order.fecha.strftime('%d/%m/%Y %H:%M')}"
    )
    bot.send_message(chat_id=CHEF_CHAT_ID, text=mensaje)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("item", "telegram_id", "status", "fecha")
    list_filter = ("status", "fecha")
    search_fields = ("item", "telegram_id")
    actions = ["marcar_listo"]

    def marcar_listo(self, request, queryset):
        for order in queryset:
            order.status = "listo"
            order.save()
            notificar_cliente(order)
            notificar_chef(order)
        self.message_user(request, "Pedidos marcados como listos.")

    marcar_listo.short_description = "Marcar pedidos seleccionados como listos"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("plato", "telegram_id", "estrellas", "fecha")
    list_filter = ("estrellas", "fecha")
    search_fields = ("plato", "telegram_id")


@admin.register(GustoCliente)
class GustoClienteAdmin(admin.ModelAdmin):
    list_display = ("telegram_id",)
    search_fields = ("telegram_id",)
