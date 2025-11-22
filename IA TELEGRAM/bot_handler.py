import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Endpoints de tu API Django
PREFERENCES_URL = "http://127.0.0.1:8000/preferences/"
KNOWLEDGE_URL = "http://127.0.0.1:8000/knowledge/"
ORDERS_URL = "http://127.0.0.1:8000/orders/"

# Token del bot
BOT_TOKEN = "8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU"

# Configura logs
logging.basicConfig(level=logging.INFO)

# ------------------------------
# Funciones de almacenamiento
# ------------------------------

def save_preference(telegram_id, preference, liked=True):
    data = {
        "telegram_id": telegram_id,
        "preference": preference,
        "liked": liked
    }
    response = requests.post(PREFERENCES_URL, json=data)
    return response.status_code in [200, 201]

def get_preferences(telegram_id):
    response = requests.get(PREFERENCES_URL, params={"telegram_id": telegram_id})
    if response.status_code == 200 and response.json():
        return response.json()
    return []

def save_order(telegram_id, item):
    data = {
        "telegram_id": telegram_id,
        "item": item,
        "status": "pendiente"
    }
    response = requests.post(ORDERS_URL, json=data)
    return response.status_code in [200, 201]

def get_orders(telegram_id):
    response = requests.get(ORDERS_URL, params={"telegram_id": telegram_id})
    if response.status_code == 200 and response.json():
        return response.json()
    return []

# ------------------------------
# Funciones del bot
# ------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍽️ ¡Bienvenido al restaurante digital! "
        "Dime qué te gusta o qué no te gusta, y te recomendaré platos. "
        "También puedes decir 'quiero pedir X' para registrar un pedido."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    text = update.message.text.lower().strip()

    # Saludos comunes
    saludos = ["hola", "buenas", "qué tal", "hey", "holi"]
    if text in saludos:
        await update.message.reply_text("👋 ¡Hola! ¿Qué te gustaría comer hoy?")
        return

    # Gustos
    if text.startswith("me gusta "):
        tema = text.replace("me gusta ", "")
        save_preference(telegram_id, tema, liked=True)
        await update.message.reply_text(f"✅ Guardé que te gusta {tema}. ¿Quieres que te recomiende un plato relacionado?")
        return

    # No gustos
    if text.startswith("no me gusta "):
        tema = text.replace("no me gusta ", "")
        save_preference(telegram_id, tema, liked=False)
        await update.message.reply_text(f"❌ Ok, no te gusta {tema}. Lo tendré en cuenta.")
        return

    # Recomendaciones
    if text in ["sí", "recomiéndame algo", "dale", "ok"]:
        await recomienda(update, context)
        return

    # Pedidos
    if text.startswith("quiero pedir "):
        item = text.replace("quiero pedir ", "")
        if save_order(telegram_id, item):
            await update.message.reply_text(f"📝 Pedido registrado: {item}. Estado: pendiente.")
        else:
            await update.message.reply_text("⚠️ No pude registrar tu pedido, intenta de nuevo.")
        return

    # Si no coincide con nada
    await update.message.reply_text("🤔 No entendí tu mensaje. Puedes decir 'me gusta X', 'no me gusta Y' o 'quiero pedir Z'.")
    
async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    prefs = get_preferences(telegram_id)
    if prefs:
        mensaje = "📋 Tus preferencias:\n"
        for p in prefs:
            estado = "✅ Te gusta" if p["liked"] else "❌ No te gusta"
            mensaje += f"{estado}: {p['preference']}\n"
        await update.message.reply_text(mensaje)
    else:
        await update.message.reply_text("No encontré preferencias guardadas.")

async def recomienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    prefs = get_preferences(telegram_id)
    if prefs:
        gustos = [p["preference"] for p in prefs if p["liked"]]
        if gustos:
            tema = gustos[-1]  # último gusto
            sugerencia = f"🍝 Ya que te gusta {tema}, te recomiendo probar nuestra especialidad con {tema}. ¿Quieres pedirla?"
            await update.message.reply_text(sugerencia)
        else:
            await update.message.reply_text("No tengo suficientes datos para recomendarte algo.")
    else:
        await update.message.reply_text("No encontré tus preferencias.")

async def ver_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    orders = get_orders(telegram_id)
    if orders:
        mensaje = "🧾 Tus pedidos:\n"
        for o in orders:
            mensaje += f"- {o['item']} (Estado: {o['status']})\n"
        await update.message.reply_text(mensaje)
    else:
        await update.message.reply_text("No encontré pedidos registrados.")


#Marcar listo 

async def marcar_listo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text.startswith("pedido listo "):
        item = text.replace("pedido listo ", "").strip()

        # Buscar el pedido en la API
        response = requests.get(ORDERS_URL, params={"item": item})
        if response.status_code == 200 and response.json():
            order = response.json()[0]  # primer pedido encontrado
            cliente_id = order["telegram_id"]

            # Actualizar estado
            update_url = f"{ORDERS_URL}{order['id']}/"
            data = {
                "telegram_id": cliente_id,
                "item": order["item"],
                "status": "listo"
            }
            r = requests.put(update_url, json=data)

            if r.status_code in [200, 204]:
                # Notificar a cocina
                await update.message.reply_text(f"✅ El pedido '{item}' está marcado como listo.")

                # Notificar al cliente
                await context.bot.send_message(
                    chat_id=cliente_id,
                    text=f"🍽️ Tu pedido '{item}' está listo para recoger o servir. ¡Buen provecho!"
                )
            else:
                await update.message.reply_text("⚠️ No pude actualizar el pedido.")
        else:
            await update.message.reply_text("⚠️ No encontré ese pedido.")






# ------------------------------
# Inicializar bot
# ------------------------------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ver", ver))
    app.add_handler(CommandHandler("pedidos", ver_pedidos))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
