import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

ORDERS_URL = "http://127.0.0.1:8000/orders/"
BOT_TOKEN_COCINA = "8265846340:AAFNOqStooRqkiwxV-GdYG8EaEd-r8mPsHw"

logging.basicConfig(level=logging.INFO)

# ------------------------------
# Funciones auxiliares
# ------------------------------

def update_order_status(order_id, telegram_id, item, new_status):
    update_url = f"{ORDERS_URL}{order_id}/"
    data = {
        "telegram_id": telegram_id,
        "item": item,
        "status": new_status
    }
    r = requests.put(update_url, json=data)
    return r.status_code in [200, 204]

def get_all_orders():
    response = requests.get(ORDERS_URL)
    if response.status_code == 200 and response.json():
        return response.json()
    return []

# ------------------------------
# Funciones del bot
# ------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👨‍🍳 Bot de cocina listo. Usa 'pedido listo X' para marcar un pedido como listo.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text.startswith("pedido listo "):
        item = text.replace("pedido listo ", "").strip()
        orders = get_all_orders()

        for order in orders:
            if order["item"].lower() == item.lower() and order["status"] == "pendiente":
                if update_order_status(order["id"], order["telegram_id"], order["item"], "listo"):
                    # Notificar a cocina
                    await update.message.reply_text(f"✅ Pedido '{item}' marcado como listo.")

                    # Notificar al cliente automáticamente
                    await context.bot.send_message(
                        chat_id=order["telegram_id"],
                        text=f"🍽️ Tu pedido '{item}' está listo para recoger o servir. ¡Buen provecho!"
                    )
                return

        await update.message.reply_text("⚠️ No encontré ese pedido pendiente.")
    else:
        await update.message.reply_text("Usa 'pedido listo X' para marcar un pedido como listo.")

# ------------------------------
# Inicializar bot
# ------------------------------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN_COCINA).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot Cocina corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
