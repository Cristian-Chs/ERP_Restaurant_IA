"""
Recommendation Service
Manejo de recomendaciones (similares, híbridas, etc.)
"""
import aiohttp
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot_Cliente.config import SIMILAR_URL, HIBRIDA_URL
from bot_Cliente.utils.proactive_messages import get_suggestive_question

async def aplicar_memoria_personalizada(telegram_id, plato):
    """
    Simulación de memoria personalizada.
    Idealmente esto consulta BBDD para ver si el usuario modificó ingredientes antes.
    Por ahora devuelve el plato tal cual para no bloquear.
    """
    return plato

async def recomendacion_similar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /recomendacion_similar - Recomienda platos parecidos al último pedido.
    """
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name
    
    # Deteminar destinatario del mensaje (Comando o Callback)
    if update.message:
        message_target = update.message
    elif update.callback_query:
        message_target = update.callback_query.message
    else:
        return

    try:
        # Usamos aiohttp para ser async
        async with aiohttp.ClientSession() as session:
            # Asegurar slash
            url = f"{SIMILAR_URL}{telegram_id}/" if SIMILAR_URL.endswith("/") else f"{SIMILAR_URL}/{telegram_id}/"
            
            async with session.get(url, timeout=5) as r:
                if r.status != 200:
                    text_error = await r.text()
                    print(f"Error backend similar: {r.status} {text_error}")
                    await message_target.reply_text("😓 Tuve un pequeño problema conectando con mis neuronas culinarias. Intenta en un ratico.")
                    return
                data = await r.json()
    except Exception as e:
        print(f"Error en recomendacion_similar: {e}")
        await message_target.reply_text("📶 Parece que hay un error de conexión con la cocina.")
        return

    similares = data.get("similares", [])
    plato_base = data.get("plato_base", None)

    if not similares:
        await message_target.reply_text(
            f"🤔 {nombre}, aún no tengo suficiente info para buscar parecidos.\n\n"
            "¡Pide algo rico y aprenderé de tus gustos! 😋"
        )
        return

    # Mensaje Proactivo
    texto = f"👀 Vi que te gustó *{plato_base}*...\n\n"
    texto += "✨ *Creo que estos te van a encantar:*\n"
    
    keyboard = []

    for plato in similares:
        # Aplicar memoria personalizada
        plato_personalizado = await aplicar_memoria_personalizada(telegram_id, plato)
        
        texto += f"• {plato_personalizado}\n"

        keyboard.append([
            InlineKeyboardButton(
                f"🤤 Pedir {plato_personalizado}",
                callback_data=f"pedido:{plato_personalizado}"
            )
        ])
    
    # Pregunta de cierre proactiva
    close_q = get_suggestive_question()
    texto += f"\n_{close_q}_"

    keyboard.append([InlineKeyboardButton("🙅‍♂️ No gracias", callback_data="rechazar_recomendacion")])

    await message_target.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
