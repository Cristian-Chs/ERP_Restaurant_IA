import logging
import requests
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ----------------------------------------------------
# ⚙️ Configuración
# ----------------------------------------------------
PREFERENCES_URL = "http://127.0.0.1:8000/preferences/"
ORDERS_URL = "http://127.0.0.1:8000/orders/"
BOT_TOKEN_CLIENTE = "8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU"  # 👈 reemplaza con tu token real

logging.basicConfig(level=logging.INFO)

# ----------------------------------------------------
# 🧩 Funciones auxiliares
# ----------------------------------------------------
def save_order(telegram_id, item):
    data = {"telegram_id": telegram_id, "item": item, "status": "pendiente"}
    response = requests.post(ORDERS_URL, json=data)
    return response.status_code in [200, 201]

def get_orders(telegram_id):
    response = requests.get(ORDERS_URL, params={"telegram_id": telegram_id})
    if response.status_code == 200 and response.json():
        return response.json()
    return []

def parse_pedido(texto):
    # Buscar líneas con formato: "1. *Sushi* (1 x $120.00)"
    patron = r"\d+\.\s\*(.+?)\*\s\((\d+)\s+x\s\$(\d+\.\d{2})\)"
    items = []
    for match in re.findall(patron, texto):
        nombre, cantidad, precio = match
        cantidad = int(cantidad)
        precio = float(precio)
        subtotal = cantidad * precio
        items.append({
            "nombre": nombre,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "subtotal": subtotal
        })

    # Buscar el total final
    total_match = re.search(r"TOTAL FINAL:\s*\$(\d+\.\d{2})", texto)
    total = float(total_match.group(1)) if total_match else sum(i["subtotal"] for i in items)

    if items:
        return {
            "items": items,
            "total": total,
            "resumen": ", ".join([f"{i['cantidad']}x {i['nombre']}" for i in items])
        }
    return None

# ----------------------------------------------------
# 🤖 Handlers del bot
# ----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    await update.message.reply_text(
        f"🍽️ Bienvenido {nombre} al restaurante digital.\n"
        "Dime 'quiero pedir X' o envíame tu resumen de pedido."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name
    text = update.message.text

    pedido = parse_pedido(text)

    if pedido:
        # Guardar cada item en la base de datos
        for item in pedido["items"]:
            save_order(telegram_id, item["nombre"])
        await update.message.reply_text(
            f"📝 {nombre}, tu pedido fue registrado: {pedido['resumen']}.\n"
            f"💰 Total: ${pedido['total']:.2f}\nEstado: pendiente."
        )
    elif text.lower().startswith("quiero pedir "):
        item = text.replace("quiero pedir ", "")
        if save_order(telegram_id, item):
            await update.message.reply_text(
                f"📝 {nombre}, tu pedido fue registrado: {item}. Estado: pendiente."
            )
        else:
            await update.message.reply_text(
                f"⚠️ {nombre}, no pude registrar tu pedido, intenta de nuevo."
            )
    else:
        await update.message.reply_text(
            f"{nombre}, puedes decir 'quiero pedir X' o enviar un resumen de pedido."
        )

async def ver_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name
    orders = get_orders(telegram_id)
    if orders:
        mensaje = f"🧾 {nombre}, estos son tus pedidos:\n"
        for o in orders:
            mensaje += f"- {o['item']} (Estado: {o['status']})\n"
        await update.message.reply_text(mensaje)
    else:
        await update.message.reply_text(f"{nombre}, no encontré pedidos registrados.")

# ----------------------------------------------------
# 🚀 Main
# ----------------------------------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN_CLIENTE).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pedidos", ver_pedidos))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot Cliente corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
