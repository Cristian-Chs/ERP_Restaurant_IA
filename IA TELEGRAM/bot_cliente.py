import logging
import requests
import re
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ----------------------------------------------------
# ⚙️ Configuración
# ----------------------------------------------------
PREFERENCES_URL = "http://127.0.0.1:8000/preferences/"
ORDERS_URL = "http://127.0.0.1:8000/orders/"
BOT_TOKEN_CLIENTE = "TU_TOKEN_AQUI"  # 👈 reemplaza con tu token real

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
# 🔮 Función de recomendación con SVD
# ----------------------------------------------------
def recomendar_items(telegram_id, top_n=3):
    modelo_path = Path("modelo_recomendacion_scipy_svd.pkl")
    if not modelo_path.exists():
        return []

    with open(modelo_path, "rb") as f:
        modelo = pickle.load(f)

    U = modelo["U"]
    Sigma_diag = modelo["Sigma_diag"]
    Vt = modelo["Vt"]
    user_ids = modelo["user_ids"]
    item_names = modelo["item_names"]

    R_pred = np.dot(np.dot(U, Sigma_diag), Vt)

    if telegram_id not in user_ids:
        return []

    user_index = list(user_ids).index(telegram_id)
    user_predictions = R_pred[user_index]

    pred_df = pd.DataFrame({
        "item": item_names,
        "pred_score": user_predictions
    }).sort_values("pred_score", ascending=False)

    return pred_df.head(top_n)["item"].tolist()

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
        for item in pedido["items"]:
            save_order(telegram_id, item["nombre"])

        recomendaciones = recomendar_items(telegram_id, top_n=3)

        mensaje = (
            f"📝 {nombre}, tu pedido fue registrado: {pedido['resumen']}.\n"
            f"💰 Total: ${pedido['total']:.2f}\nEstado: pendiente.\n"
        )
        if recomendaciones:
            mensaje += "✨ Te recomiendo también probar:\n"
            for rec in recomendaciones:
                mensaje += f"🍽️ {rec}\n"

        await update.message.reply_text(mensaje)

    elif text.lower().startswith("quiero pedir "):
        item = text.replace("quiero pedir ", "")
        if save_order(telegram_id, item):
            recomendaciones = recomendar_items(telegram_id, top_n=3)
            mensaje = f"📝 {nombre}, tu pedido fue registrado: {item}. Estado: pendiente.\n"
            if recomendaciones:
                mensaje += "✨ Te recomiendo también probar:\n"
                for rec in recomendaciones:
                    mensaje += f"🍽️ {rec}\n"
            await update.message.reply_text(mensaje)
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
