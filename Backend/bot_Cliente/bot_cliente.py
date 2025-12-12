import sys, os

# 👇 Añade la carpeta que contiene el directorio 'ml' al PYTHONPATH.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# ✅ Importa desde ml.predict
from ml.predict import recomendar_ml, recomendar_popularidad

# 👇 Resto de tus imports
import logging
import requests
import pytz
import asyncio
import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ----------------------------------------------------
# ⚙️ Configuración
# ----------------------------------------------------
ORDERS_URL = "http://127.0.0.1:8000/orders/"
GUSTOS_URL = "http://127.0.0.1:8000/gustos/"
HISTORIAL_URL = "http://127.0.0.1:8000/historial/"
POPULARIDAD_URL = "http://127.0.0.1:8000/popularidad/"
RATING_URL = "http://127.0.0.1:8000/rating/"

BOT_TOKEN_CLIENTE = "8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU"
CHEF_CHAT_ID = 5719602467

logging.basicConfig(level=logging.INFO)

# ----------------------------------------------------
# 🗂️ Función para guardar orden en Django
# ----------------------------------------------------
def save_order(telegram_id, item):
    data = {"telegram_id": telegram_id, "item": item, "status": "pendiente"}
    try:
        response = requests.post(ORDERS_URL, json=data, timeout=8)
        return response.status_code in (200, 201)
    except Exception as e:
        logging.error(f"[ERROR] No se pudo conectar al backend: {e}")
        return False

# ----------------------------------------------------
# 🧹 Limpieza de texto
# ----------------------------------------------------
def clean_order_text(text: str) -> str:
    cleaned_text = text.replace('*', '')
    cleaned_text = cleaned_text.replace('--------------------------------', '')
    cleaned_text = cleaned_text.replace("Quiero pedir.", "")
    cleaned_text = cleaned_text.replace("Por favor, confirma mi pedido.", "")
    return cleaned_text.strip()

# ----------------------------------------------------
# ✅ MENÚ DEL DÍA
# ----------------------------------------------------
async def menu_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 *Menú del día:*\n"
        "- Pasta al pesto\n"
        "- Pollo a la plancha\n"
        "- Ensalada César\n"
        "- Jugo natural\n",
        parse_mode="Markdown"
    )

# ----------------------------------------------------
# ✅ MENÚ PERSONALIZADO (gustos desde BD)
# ----------------------------------------------------
async def menu_personalizado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name

    try:
        response = requests.get(f"{GUSTOS_URL}{telegram_id}/", timeout=5)
        gustos = response.json().get("gustos", []) if response.status_code == 200 else []
    except:
        gustos = []

    if not gustos:
        await update.message.reply_text(
            f"⚠️ {nombre}, aún no tengo tus gustos registrados.\n"
            "Puedes configurarlos enviando: *Me gusta [plato]*",
            parse_mode="Markdown"
        )
        return

    texto_menu = "⭐ *Tu menú personalizado basado en tus gustos:*\n\n"
    for plato in gustos:
        texto_menu += f"• {plato}\n"

    await update.message.reply_text(texto_menu, parse_mode="Markdown")

# ----------------------------------------------------
# ✅ START + TECLADO INFERIOR
# ----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name

    keyboard = [
        [KeyboardButton("/menu")],
        [
            KeyboardButton("🍽️ Menú del día"),
            KeyboardButton("⭐ Menú personalizado")
        ],
        [KeyboardButton("/pedido")],
        [KeyboardButton("/recomendacion")],
        [" "]  
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await update.message.reply_text(
        f"👋 Hola {nombre}, bienvenido al restaurante digital.\n"
        "Usa /menu para ver opciones, o elige un menú abajo.",
        reply_markup=reply_markup
    )

# ----------------------------------------------------
# ✅ SISTEMA DE RECOMENDACIÓN HÍBRIDO
# ----------------------------------------------------
async def recomendaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name

    # ✅ 1. Historial del cliente (rating)
    try:
        r_hist = requests.get(f"{HISTORIAL_URL}{telegram_id}/", timeout=5)
        historial = r_hist.json().get("historial", []) if r_hist.status_code == 200 else []
    except:
        historial = []

    historial_ordenado = sorted(historial, key=lambda x: x.get("rating", 0), reverse=True)
    platos_por_rating = [item["plato"] for item in historial_ordenado]

    # ✅ 2. Popularidad global
    try:
        r_pop = requests.get(POPULARIDAD_URL, timeout=5)
        popularidad = r_pop.json().get("populares", []) if r_pop.status_code == 200 else []
    except:
        popularidad = []

    # ✅ 3. ML
    try:
        ml_recs = await asyncio.to_thread(recomendar_ml, telegram_id, 5)
    except:
        ml_recs = []

    # ✅ 4. Combinar todo
    recomendacion_final = []

    for plato in ml_recs:
        if plato not in recomendacion_final:
            recomendacion_final.append(plato)

    for plato in platos_por_rating:
        if plato not in recomendacion_final:
            recomendacion_final.append(plato)

    for plato in popularidad:
        if plato not in recomendacion_final:
            recomendacion_final.append(plato)

    recomendacion_final = recomendacion_final[:5]

    if not recomendacion_final:
        await update.message.reply_text(
            f"⚠️ {nombre}, aún no tengo suficiente información para recomendarte platos.\n"
            "Pide algunos platos y califícalos con: ⭐ 1–5."
        )
        return

    texto = f"✨ *Menú personalizado para ti, {nombre}:*\n\n"

    for plato in recomendacion_final:
        rating = next((x["rating"] for x in historial if x["plato"] == plato), None)
        if rating:
            texto += f"• {plato} — {rating} ⭐\n"
        else:
            texto += f"• {plato}\n"

    keyboard = [
        [InlineKeyboardButton(plato, callback_data=f"pedido:{plato}")]
        for plato in recomendacion_final
    ]
    keyboard.append([InlineKeyboardButton("🚫 No gracias", callback_data="rechazar_recomendacion")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        texto,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ----------------------------------------------------
# ✅ GUARDAR RATING ⭐
# ----------------------------------------------------
async def guardar_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.startswith("⭐"):
        return

    try:
        partes = text.split(" ", 2)
        rating = int(partes[1])
        plato = partes[2]
    except:
        await update.message.reply_text("Formato inválido. Usa: ⭐ 5 Nombre del plato")
        return

    if rating < 1 or rating > 5:
        await update.message.reply_text("La puntuación debe ser entre 1 y 5 estrellas.")
        return

    telegram_id = update.effective_user.id

    data = {"telegram_id": telegram_id, "plato": plato, "rating": rating}

    try:
        requests.post(RATING_URL, json=data, timeout=5)
        await update.message.reply_text(f"✅ Rating guardado: {plato} — {rating} ⭐")
    except:
        await update.message.reply_text("⚠️ No pude guardar tu rating.")

# ----------------------------------------------------
# ✅ LÓGICA DE PEDIDOS
# ----------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    text = (update.message.text or "").strip()
    item_a_confirmar = ""

    if text.lower().startswith("quiero pedir.") or text.lower().startswith("quiero pedir "):
        item_a_confirmar = text
    elif "resumen del pedido:" in text.lower():
        item_a_confirmar = text
    elif text.lower().startswith("quiero pedir "):
        item_a_confirmar = text[len("quiero pedir "):].strip()

    if item_a_confirmar:
        pedido_key = "pedido_carrito"
        context.user_data[pedido_key] = item_a_confirmar

        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=f"confirmar:{pedido_key}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"{nombre}, ¿quieres confirmar tu pedido?",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Usa los formatos:\n"
            "1. 'quiero pedir [Plato]'\n"
            "2. El resumen completo de tu carrito."
        )

# ----------------------------------------------------
# ✅ CONFIRMAR PEDIDO
# ----------------------------------------------------
async def handle_confirmacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    nombre = query.from_user.first_name

    if query.data.startswith("confirmar:"):
        pedido_key = query.data.replace("confirmar:", "").strip()
        item_formato = context.user_data.pop(pedido_key, None)

        if item_formato is None:
            await query.edit_message_text("⚠️ Error: El pedido no se encontró o expiró.")
            return

        item_limpio = clean_order_text(item_formato)

        if save_order(telegram_id, item_limpio):
            mensaje_final = f"✅ {nombre}, tu pedido fue registrado.\n\n**Resumen:**\n{item_limpio}"

            mensaje_chef = (
                f"👨‍🍳 Nuevo pedido recibido:\n\n"
                f"{item_limpio}\n\n"
                f"📲 Cliente ID: {telegram_id}\n"
                f"🕒 Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            try:
                await context.bot.send_message(chat_id=CHEF_CHAT_ID, text=mensaje_chef)
            except Exception as e:
                logging.error(f"[ERROR] No se pudo notificar al chef: {e}")

            await query.edit_message_text(text=mensaje_final, parse_mode="Markdown")
        else:
            await query.edit_message_text(
                text=f"⚠️ {nombre}, no pude registrar tu pedido, intenta de nuevo."
            )

# ----------------------------------------------------
# ✅ CANCELAR / RECHAZAR
# ----------------------------------------------------
async def handle_cancelacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Pedido cancelado.")

async def handle_recomendacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    nombre = query.from_user.first_name

    if query.data.startswith("pedido:"):
        plato = query.data.replace("pedido:", "").strip()
        if save_order(telegram_id, plato):
            await query.edit_message_text(
                text=f"📝 {nombre}, tu pedido fue registrado: {plato}. Estado: pendiente."
            )
        else:
            await query.edit_message_text(
                text=f"⚠️ {nombre}, no se pudo registrar el pedido recomendado."
            )

async def handle_rechazo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("👌 Entendido. No se agregaron recomendaciones adicionales.")

# ----------------------------------------------------
# 🚀 MAIN
# ----------------------------------------------------
def main():
    print("Bot Cliente corriendo y atendiendo órdenes...")
    app = ApplicationBuilder().token(BOT_TOKEN_CLIENTE).build()
    app.job_queue.scheduler.configure(timezone=pytz.UTC)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("recomendacion", recomendaciones))

    app.add_handler(MessageHandler(filters.Regex("^🍽️ Menú del día$"), menu_dia))
    app.add_handler(MessageHandler(filters.Regex("^⭐ Menú personalizado$"), menu_personalizado))

    app.add_handler(MessageHandler(filters.Regex("^⭐"), guardar_rating))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CallbackQueryHandler(handle_confirmacion, pattern=r"^confirmar:"))
    app.add_handler(CallbackQueryHandler(handle_cancelacion, pattern=r"^cancelar$"))
    app.add_handler(CallbackQueryHandler(handle_recomendacion, pattern=r"^pedido:"))
    app.add_handler(CallbackQueryHandler(handle_rechazo, pattern=r"^rechazar_recomendacion$"))

    app.run_polling()

if __name__ == "__main__":
    main()
