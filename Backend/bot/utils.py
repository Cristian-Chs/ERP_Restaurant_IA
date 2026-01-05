import requests
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

TELEGRAM_API_URL = "https://api.telegram.org/bot8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU/sendMessage"
TELEGRAM_PHOTO_URL = "https://api.telegram.org/bot8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU/sendPhoto"
ADMIN_CHAT_ID = 5719602467

def notificar_pedido_listo(telegram_id, plato):
    # ✅ Primer mensaje: Pedido listo + calificación
    mensaje = (
        f"✅ Tu pedido está listo. \n *{plato}* \n\n"
        "¿Qué te pareció?\n"
        "Califícalo con una estrella:"
    )

    keyboard = [
        [
            InlineKeyboardButton("⭐ 1", callback_data=f"rating:{plato}:1"),
            InlineKeyboardButton("⭐ 2", callback_data=f"rating:{plato}:2"),
            InlineKeyboardButton("⭐ 3", callback_data=f"rating:{plato}:3"),
            InlineKeyboardButton("⭐ 4", callback_data=f"rating:{plato}:4"),
            InlineKeyboardButton("⭐ 5", callback_data=f"rating:{plato}:5"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    payload = {
        "chat_id": telegram_id,
        "text": mensaje,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(reply_markup.to_dict())
    }

    requests.post(TELEGRAM_API_URL, json=payload)
    
    # ✅ Segundo mensaje: Pregunta sobre comentario
    keyboard_comentario = [
        [
            InlineKeyboardButton("📝 Sí, dejar comentario", callback_data="dejar_comentario"),
            InlineKeyboardButton("❌ No, gracias", callback_data="no_comentario")
        ]
    ]
    
    reply_markup_comentario = InlineKeyboardMarkup(keyboard_comentario)
    
    payload_comentario = {
        "chat_id": telegram_id,
        "text": "¿Te gustaría dejar un comentario sobre tu experiencia?",
        "reply_markup": json.dumps(reply_markup_comentario.to_dict())
    }
    
    requests.post(TELEGRAM_API_URL, json=payload_comentario)

def notificar_nuevo_pedido_externo(order):
    """
    Notifica al Admin/Chef sobre un nuevo pedido que no es 'Comer Aquí'
    Incluye la foto del comprobante si existe.
    """
    mensaje = (

        f"🚨 *NUEVO PEDIDO EXTERNO*\n\n"
        f"🆔 #ORDEN: {order.id}\n"
        f"👤 Cliente: {order.telegram_id}\n"
        f"🍽️ Detalle: {order.item}\n"
        f"💰 Total: ${order.precio}\n"
        f"📦 Modalidad: {order.get_delivery_mode_display() if order.delivery_mode else 'N/A'}\n"
        f"📍 Ubicación: {order.location or 'N/A'}\n"
    )

    if order.payment_proof:
        # Enviar como foto
        files = {'photo': order.payment_proof.open('rb')}
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "caption": mensaje,
            "parse_mode": "Markdown"
        }
        requests.post(TELEGRAM_PHOTO_URL, data=payload, files=files)
    else:
        # Enviar como mensaje
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        requests.post(TELEGRAM_API_URL, json=payload)

