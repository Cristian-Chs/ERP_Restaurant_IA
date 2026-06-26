"""
Payment Handlers
Procesamiento de comprobantes de pago y notificaciones al administrador.
"""
import logging
import os
import datetime
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from bot_Cliente.config import ORDERS_URL, ADMIN_CHAT_ID, EXCHANGE_RATE_FIXED, OCR_API_URL
from bot_Cliente.services.payment_service import extraer_datos_comprobante
from bot.factura import InvoiceGenerator
from bot.models import Order as OrderModel

logging.basicConfig(level=logging.INFO)

async def handle_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe el comprobante de pago del cliente, lo analiza y lo envía al administrador.
    """
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name
    
    # Verificar que tenemos datos de orden pendiente
    order_id = context.user_data.get("pending_order_id")
    pedido_item = context.user_data.get("pending_order_item")
    
    if not order_id:
        logging.warning(f"Usuario {telegram_id} mandó foto pero no hay order_id pendiente.")
        await update.message.reply_text(
            "❌ *No encontré un pedido pendiente.*\n\n"
            "Por favor, realiza tu pedido primero antes de enviar el comprobante.",
            parse_mode="Markdown"
        )
        return

    # Extraer el file_id
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("📸 Por favor envía una foto clara del comprobante de pago.")
        return
    
    await update.message.reply_text("🔍 *Analizando tu comprobante con IA...*", parse_mode="Markdown")
    
    try:
        # Descargar temporalmente para OCR si es necesario
        file = await context.bot.get_file(file_id)
        file_path = f"temp_payment_{telegram_id}_{order_id}.jpg"
        await file.download_to_drive(file_path)
        
        # Extraer datos vía OCR Service
        payment_data = await extraer_datos_comprobante(file_path)
        
        # Eliminar archivo temporal
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Actualizar la orden en el backend
        update_payload = {
            "payment_receipt_file_id": file_id,
            "payment_status": "payment_submitted",
            "payment_data": payment_data
        }
        
        url = f"{ORDERS_URL}{order_id}/" if ORDERS_URL.endswith("/") else f"{ORDERS_URL}/{order_id}/"
        resp = requests.patch(url, json=update_payload, timeout=10)
        
        if resp.status_code in (200, 204):
            # Obtener datos para la notificación al admin
            precio = context.user_data.get("pending_order_price", 0.0)
            
            await update.message.reply_text(
                f"✅ *Comprobante recibido, {nombre}.*\n\n"
                "Estamos verificando tu pago. Te avisaremos en cuanto el restaurante lo apruebe. 🙌",
                parse_mode="Markdown"
            )
            
            # Notificar al Administrador
            await notify_admin_new_order(context, order_id, telegram_id, nombre, pedido_item, precio, payment_data, file_id)
            
            # Limpiar datos temporales de la orden
            context.user_data.pop("pending_order_id", None)
            context.user_data.pop("pending_order_item", None)
            context.user_data.pop("pending_order_price", None)
        else:
            logging.error(f"Error backend update status: {resp.status_code} - {resp.text}")
            await update.message.reply_text("⚠️ Hubo un error al registrar tu comprobante. Por favor intenta de nuevo.")
            
    except Exception as e:
        logging.error(f"Error procesando comprobante: {e}")
        await update.message.reply_text("❌ Ocurrió un error al procesar la imagen. Por favor intenta enviarla de nuevo.")

async def notify_admin_new_order(context, order_id, telegram_id, nombre, pedido_item, precio, payment_data, file_id):
    """
    Envía el comprobante al grupo/chat de administración.
    """
    # Formatear datos OCR al estilo del recibo móvil
    datos_ocr = ""
    if payment_data and "error" not in payment_data:
        datos_ocr = "\n━━━━━━━━━━━━━━━━━━━━\n*DATOS DEL COMPROBANTE*\n\n"
        
        # Mapeo de campos con formato específico
        field_map = {
            "numero_referencia": "NÚMERO DE REFERENCIA",
            "fecha": "FECHA",
            "telefono_origen": "NÚMERO CELULAR DE ORIGEN",
            "telefono_destino": "NÚMERO CELULAR DE DESTINO",
            "banco_emisor": "BANCO EMISOR",
            "banco_receptor": "BANCO RECEPTOR",
            "monto": "MONTO DE LA OPERACIÓN",
            "tipo_operacion": "TIPO DE OPERACIÓN"
        }
        
        for key, label in field_map.items():
            if key in payment_data and payment_data[key]:
                value = payment_data[key]
                datos_ocr += f"*{label}*\n{value}\n\n"
        
        datos_ocr += "━━━━━━━━━━━━━━━━━━━━\n"

    tasa = EXCHANGE_RATE_FIXED
    monto_bs = float(precio) * tasa

    msg_admin = (
        f"💰 *NUEVO COMPROBANTE DE PAGO*\n\n"
        f"👤 *Cliente:* {nombre} (ID: {telegram_id})\n"
        f"📦 *Pedido:* {pedido_item}\n"
        f"🆔 *Order ID:* {order_id}\n"
        f"💵 *Monto Esperado:* ${precio:.2f} (Bs. {monto_bs:,.2f})\n"
        f"{datos_ocr}\n"
        f"🕒 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_pago:{order_id}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_pago:{order_id}")
        ]
    ]

    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=file_id,
        caption=msg_admin,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_payment_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback para cuando el admin aprueba el pago.
    """
    query = update.callback_query
    order_id = query.data.split(":")[1]
    
    url = f"{ORDERS_URL}{order_id}/" if ORDERS_URL.endswith("/") else f"{ORDERS_URL}/{order_id}/"
    update_data = {
        "payment_status": "payment_approved",
        "status": "pendiente" # Pasa a Cocina
    }
    
    try:
        resp = requests.patch(url, json=update_data, timeout=5)
        if resp.status_code in (200, 204):
            # Notificar al cliente si tenemos su ID
            order_data = requests.get(url).json()
            client_id = order_data.get("telegram_id")
            
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ *PAGO APROBADO*",
                parse_mode="Markdown"
            )
            
            if client_id:
                # Generar factura automáticamente
                invoice_path = None
                try:
                    
                    # Obtener el objeto Order completo del backend
                    order_obj = OrderModel.objects.get(id=order_id)
                    
                    # Generar factura
                    generator = InvoiceGenerator()
                    invoice_path = generator.generate(order_obj)
                    
                    # Guardar ruta en el pedido
                    order_obj.invoice_path = invoice_path
                    order_obj.save()
                    
                    logging.info(f"Factura generada: {invoice_path}")
                except Exception as e:
                    logging.error(f"Error generando factura: {e}")
                
                # Enviar mensaje de aprobación
                await context.bot.send_message(
                    chat_id=client_id,
                    text=f"🥳 *¡Pago Aprobado!* (Orden #{order_id})\n\nTu pedido ya está en preparación. Te avisaremos cuando esté listo. 👩‍🍳",
                    parse_mode="Markdown"
                )
                
                # Enviar factura si se generó correctamente
                if invoice_path and os.path.exists(invoice_path):
                    try:
                        await context.bot.send_photo(
                            chat_id=client_id,
                            photo=open(invoice_path, 'rb'),
                            caption="*Tu Factura Fiscal*\n\nGracias por tu compra. Disfruta de tu comida. Esperamos verte pronto.",
                            parse_mode="Markdown"
                        )
                        logging.info(f"Factura enviada al cliente {client_id}")
                    except Exception as e:
                        logging.error(f"Error enviando factura: {e}")
        else:
            await query.answer(f"Error al actualizar orden: {resp.status_code}", show_alert=True)
    except Exception as e:
        logging.error(f"Error aprobando pago: {e}")
        await query.answer("Error de conexión con el servidor.", show_alert=True)

async def handle_payment_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback para cuando el admin rechaza el pago.
    """
    query = update.callback_query
    order_id = query.data.split(":")[1]
    
    url = f"{ORDERS_URL}{order_id}/" if ORDERS_URL.endswith("/") else f"{ORDERS_URL}/{order_id}/"
    update_data = {"payment_status": "payment_rejected"}
    
    try:
        resp = requests.patch(url, json=update_data, timeout=5)
        if resp.status_code in (200, 204):
            order_data = requests.get(url).json()
            client_id = order_data.get("telegram_id")
            
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ *PAGO RECHAZADO*",
                parse_mode="Markdown"
            )
            
            if client_id:
                await context.bot.send_message(
                    chat_id=client_id,
                    text=f"⚠️ *Pago Rechazado* (Orden #{order_id})\n\nHubo un problema con tu comprobante. Por favor, verifica los datos e intenta de nuevo o contacta a soporte.",
                    parse_mode="Markdown"
                )
        else:
            await query.answer("Error al actualizar orden.", show_alert=True)
    except Exception as e:
        logging.error(f"Error rechazando pago: {e}")
        await query.answer("Error de conexión.", show_alert=True)
