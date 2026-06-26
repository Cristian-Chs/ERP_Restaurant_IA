import requests
import json
import logging
from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TELEGRAM_PHOTO_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
ADMIN_CHAT_ID = settings.ADMIN_CHAT_ID

def notificar_pedido_listo(telegram_id, plato, invoice_path=None):
    #  Primer mensaje: Pedido listo + calificación
    mensaje = (
        f"🎉 Tu pedido está listo. \n *{plato}* \n\n"
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
    
    #  Segundo mensaje: Pregunta sobre comentario
    keyboard_comentario = [
        [
            InlineKeyboardButton("✍️ Sí, dejar comentario", callback_data="dejar_comentario"),
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
    
    #  Tercer mensaje: Enviar factura si existe
    if invoice_path:
        try:
            import os
            if os.path.exists(invoice_path):
                with open(invoice_path, 'rb') as photo_file:
                    files = {'photo': photo_file}
                    payload_factura = {
                        "chat_id": telegram_id,
                        "caption": "📄 *Tu Factura Fiscal*\n\nGracias por tu compra. 🙏",
                        "parse_mode": "Markdown"
                    }
                    requests.post(TELEGRAM_PHOTO_URL, data=payload_factura, files=files)
                    logger.info(f"Factura enviada al cliente {telegram_id}")
            else:
                logger.warning(f"Factura no encontrada: {invoice_path}")
        except Exception as e:
            logger.error(f"Error enviando factura: {e}")

def notificar_nuevo_pedido_externo(order):
    """
    Notifica al Admin/Chef sobre un nuevo pedido que no es 'Comer Aquí'
    Incluye la foto del comprobante si existe.
    """
    payment_method = 'Desconocido'
    if order.payment_data and 'payment_method' in order.payment_data:
        method_map = {
            'cash': 'EFECTIVO 💵',
            'zelle': 'ZELLE 🟣',
            'pago_movil': 'PAGO MÓVIL 📱',
            'transfer': 'TRANSFERENCIA 🏦'
        }
        raw_method = order.payment_data.get('payment_method')
        payment_method = method_map.get(raw_method, raw_method.upper())

    mensaje = (
        f"🔔 *NUEVO PEDIDO EXTERNO*\n\n"
        f"📋 #ORDEN: {order.id}\n"
        f"👤 Cliente: {order.customer_name or order.telegram_id}\n"
        f"🍽️ Detalle: {order.item}\n"
        f"💵 Total: ${order.precio}\n"
        f"💳 Método: {payment_method}\n"
        f"📍 Modalidad: {order.get_delivery_mode_display() if order.delivery_mode else 'N/A'}\n"
        f"🗺️ Ubicación: {order.location or 'N/A'}\n"
    )

    if order.status == 'fraude_sospecha':
        mensaje = f" *POSIBLE FRAUDE DETECTADO*\n\n" + mensaje
        mensaje += f"\n\n *ALERTA*: El comprobante parece duplicado."
        
    # Mensaje especial para efectivo
    if order.payment_data and order.payment_data.get('payment_method') == 'cash':
        mensaje += "\n💰 *PAGO EN EFECTIVO* - Cobrar al entregar"

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
        # Enviar como mensaje (para efectivo o sin comprobante)
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        requests.post(TELEGRAM_API_URL, json=payload)
 
def notificar_pago_aprobado(telegram_id, order_id, invoice_path=None):
    """
    Notifica al cliente que su pago fue aprobado.
    Si se proporciona invoice_path, envía la factura como imagen.
    """
    mensaje = f" *¡Pago Aprobado!* (Orden #{order_id})\n\nTu pedido ha sido enviado a cocina y estará listo pronto. "
    
    if invoice_path:
        # Enviar factura como foto con caption
        try:
            import os
            if os.path.exists(invoice_path):
                with open(invoice_path, 'rb') as photo_file:
                    files = {'photo': photo_file}
                    payload = {
                        "chat_id": telegram_id,
                        "caption": mensaje + "\n\n *Tu Factura Fiscal*",
                        "parse_mode": "Markdown"
                    }
                    import requests
                    requests.post(TELEGRAM_PHOTO_URL, data=payload, files=files)
                    return
        except Exception as e:
            logger.error(f"Error enviando factura por Telegram: {e}")
            # Si falla, enviar solo el mensaje de texto
    
    # Fallback: enviar solo mensaje de texto
    payload = {
        "chat_id": telegram_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    import requests
    requests.post(TELEGRAM_API_URL, json=payload)

def notificar_pago_rechazado(telegram_id, order_id):
    mensaje = f" *Pago Rechazado* (Orden #{order_id})\n\nHubo un problema con tu comprobante. Por favor, contacta a soporte o intenta de nuevo con una captura legible. ‍"
    payload = {
        "chat_id": telegram_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(TELEGRAM_API_URL, json=payload)

def notificar_puntos_ganados(telegram_id, puntos_ganados, total_puntos):
    mensaje = (
        f" *¡Has ganado {puntos_ganados} puntos!*\n\n"
        f"Tu saldo actual es de *{total_puntos} puntos*.\n"
        f"¡Sigue acumulando para canjear por premios y descuentos! "
    )
    payload = {
        "chat_id": telegram_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(TELEGRAM_API_URL, json=payload)

