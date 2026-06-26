"""
Callback Handlers
Manejo de interacciones con botones inline de forma proactiva.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot_Cliente.utils.proactive_messages import (
    get_random_message,
    MENU_FOLLOWUPS,
    DELIVERY_OPTIONS
)
from bot_Cliente.handlers.commands import soporte as soporte_command
from bot_Cliente.handlers.payments import handle_payment_approval, handle_payment_rejection
from bot_Cliente.config import ORDERS_URL, EXCHANGE_RATE_FIXED
import requests
import logging

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Centraliza el manejo de todos los callbacks del bot.
    """
    query = update.callback_query
    telegram_id = query.from_user.id
    nombre = query.from_user.first_name

    # Siempre responder al callback para quitar el relojito
    await query.answer()
    
    data = query.data
    
    # --------------------------------------------------------------------------
    # 1. AYUDA PEDIDO (Desde /start)
    # --------------------------------------------------------------------------
    if data == "ayuda_pedido":
        texto = (
            f"¡Excelente {nombre}! 😃 Para pedir es súper fácil:\n\n"
            "Solo escríbeme lo que quieres como si hablaras con un mesero real. 🗣️\n"
            "_Ejemplo: \"Quiero una hamburguesa con queso y una coca cola\"_\n\n"
            "¿Ya sabes qué pedir o prefieres ver el menú primero? 👇"
        )
        
        keyboard = [
            [InlineKeyboardButton("📜 Ver el Menú", callback_data="ver_menu_proactivo")],
            [InlineKeyboardButton("🍔 Ya sé qué quiero", callback_data="pedir_directo")]
        ]
        
        await query.edit_message_text(
            texto, 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --------------------------------------------------------------------------
    # 2. MENU PROACTIVO (Invocado desde ayuda o flujo)
    # --------------------------------------------------------------------------
    if data == "ver_menu_proactivo":
        # Aquí redirigimos al comando de menú pero editando el mensaje
        # Importamos aquí para evitar ciclos si fuera necesario, o usamos el helper
        from bot_Cliente.handlers.commands import menu
        await menu(update, context) # Reutiliza lógica de commands.py
        
        # Ojo: commands.menu usa reply_text, aquí queremos quizás editar.
        # Por simplicidad, dejamos que menu mande mensaje nuevo y borramos el anterior si queremos,
        # o simplemente dejamos que fluya. commands.menu es async.
        return

    if data == "pedir_directo":
        await query.edit_message_text(
            f"¡Esa es la actitud! 😎\n\n"
            "Soy todo oídos 👂. Escribe tu pedido aquí abajo 👇\n"
            "_Ejemplo: \"Dame 2 pizzas de pepperoni\"_",
            parse_mode="Markdown"
        )
        return

    # --------------------------------------------------------------------------
    # 3. ESTADO PEDIDO (Consulta Real al Backend)
    # --------------------------------------------------------------------------
    if data == "estado_pedido":
        try:
            # Consultar pedidos del usuario
            response = requests.get(f"{ORDERS_URL}?telegram_id={telegram_id}", timeout=5)
            
            if response.status_code == 200:
                pedidos = response.json()
                
                # Filtrar pedidos activos (no completados ni cancelados)
                pedidos_activos = [p for p in pedidos if p.get('status') not in ['completado', 'cancelado', 'rechazado']]
                
                if not pedidos_activos:
                    await query.edit_message_text(
                        "No tienes pedidos activos en este momento.\n\n"
                        "Puedes hacer un nuevo pedido escribiendo lo que deseas.",
                        parse_mode="Markdown"
                    )
                    return
                
                # Mostrar el pedido más reciente
                pedido = pedidos_activos[0]
                order_id = pedido.get('id')
                item = pedido.get('item', 'Pedido')
                status = pedido.get('status', 'pendiente')
                precio = pedido.get('precio', 0)
                fecha = pedido.get('fecha', '')
                
                # Mapeo de estados a mensajes
                status_messages = {
                    'pendiente': 'Tu pedido está pendiente de confirmación',
                    'esperando_pago': 'Esperando confirmación de pago',
                    'payment_submitted': 'Pago enviado, esperando aprobación',
                    'payment_approved': 'Pago aprobado, enviado a cocina',
                    'en_preparacion': 'Tu pedido se está preparando en cocina',
                    'listo': 'Tu pedido está listo para recoger/entregar',
                    'en_camino': 'Tu pedido está en camino'
                }
                
                status_msg = status_messages.get(status, f'Estado: {status}')
                
                msg = (
                    f"*Estado de tu Pedido #{order_id}*\n\n"
                    f"Pedido: {item}\n"
                    f"Total: ${precio:.2f}\n"
                    f"Estado: {status_msg}\n\n"
                )
                
                # Agregar tiempo estimado según el estado
                if status in ['en_preparacion', 'payment_approved']:
                    msg += "Tiempo estimado: 15-20 minutos\n"
                elif status == 'listo':
                    msg += "Tu pedido ya está listo!\n"
                elif status == 'en_camino':
                    msg += "Llegará en aproximadamente 10 minutos\n"
                
                await query.edit_message_text(msg, parse_mode="Markdown")
            else:
                await query.edit_message_text(
                    "No pude consultar tus pedidos en este momento.\n"
                    "Por favor intenta de nuevo más tarde."
                )
                
        except Exception as e:
            logging.error(f"Error consultando estado pedido: {e}")
            await query.edit_message_text(
                "Ocurrió un error al consultar tu pedido.\n"
                "Por favor intenta de nuevo."
            )
        return

    # --------------------------------------------------------------------------
    # 4. SOPORTE
    # --------------------------------------------------------------------------
    if data == "soporte":
        await soporte_command(update, context)
        return

    # --------------------------------------------------------------------------
    # 5. CONFIRMACIÓN / PAGO (Lógica simplificada por ahora)
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # 6. CONFIRMAR PEDIDO MÚLTIPLE
    # --------------------------------------------------------------------------
    if data == "confirmar_pedido_multiple":
        # NUEVO: Verificar DISPONIBILIDAD DE MESAS
        from core.models import Table
        from asgiref.sync import sync_to_async
        
        # Helper wrappers for async DB access
        @sync_to_async
        def check_availability():
            return Table.objects.count(), Table.objects.filter(is_occupied=True).count()
        
        total_tables, occupied_tables = await check_availability()
        
        if total_tables > 0 and occupied_tables >= total_tables:
            await query.edit_message_text(
                "Lo siento pero en estos momento no hay lugares disponible por favor intentelo mas tarde."
            )
            return

        resultado = context.user_data.get("ultimo_pedido_interpretado", {})
        items = resultado.get("items", [])
        total = resultado.get("total", 0)
        pedido_final = resultado.get("pedido_final", "")
        
        if not items:
            await query.edit_message_text("Error: No se encontraron items en el pedido.")
            return
        
        # Guardar en contexto
        context.user_data["pending_order_items"] = items
        context.user_data["pending_order_item"] = pedido_final  # String para mostrar
        context.user_data["pending_order_price"] = total
        
        # Preguntar tipo de servicio
        msg_servicio = get_random_message(DELIVERY_OPTIONS)
        
        keyboard = [
            [InlineKeyboardButton("Delivery", callback_data="sel_serv:DELIVERY")],
            [InlineKeyboardButton("Retiro en Local", callback_data="sel_serv:RETIRO")],
            [InlineKeyboardButton("Comer Aquí", callback_data="sel_serv:AQUI")]
        ]
        
        await context.bot.send_message(
            chat_id=telegram_id,
            text=msg_servicio,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Editar mensaje anterior
        await query.edit_message_text(
            f"Perfecto! Tu pedido:\n\n{pedido_final}\n\nTotal: ${total:.2f}",
            parse_mode="Markdown"
        )
        return
    
    # --------------------------------------------------------------------------
    # 7. CONFIRMAR PEDIDO (Legacy - Un Solo Item)
    # --------------------------------------------------------------------------
    if data.startswith("pedido:"):
        producto = data.split(":", 1)[1]
        
        # Guardar temporalmente en context.user_data
        context.user_data["pending_order_item"] = producto
        context.user_data["pending_order_price"] = 10.0  # Precio dummy o calcular si es posible
        
        await query.edit_message_text(f"¡Excelente Choice! 🤤\nElección: *{producto}*\n\nAhora, ¿cómo lo quieres?")
            
        msg = get_random_message(DELIVERY_OPTIONS)
        
        keyboard = [
            [InlineKeyboardButton("🛵 Delivery", callback_data="sel_serv:DELIVERY")],
            [InlineKeyboardButton("🛍️ Retiro en Local", callback_data="sel_serv:RETIRO")],
            [InlineKeyboardButton("🍽️ Comer Aquí", callback_data="sel_serv:AQUI")]
        ]
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --------------------------------------------------------------------------
    # 7. SELECCIÓN DE SERVICIO (Delivery, Pickup, Here)
    # --------------------------------------------------------------------------
    if data.startswith("sel_serv:"):
        service_type = data.split(":")[1]
        context.user_data["service_type"] = service_type
        
        if service_type == "DELIVERY":
            context.user_data["state"] = "waiting_for_address"
            await query.edit_message_text(
                "📍 *¡Perfecto! Necesito tu dirección para el envío.*\n\n"
                "Por favor, escríbela aquí abajo lo más detallado posible (Calle, edificio, punto de referencia):",
                parse_mode="Markdown"
            )
        else:
            await show_payment_info(update, context)
        return

    if data.startswith("proceder_pago"):
        # Extraer key si es necesario
        msg = get_random_message(DELIVERY_OPTIONS)
        
        keyboard = [
            [InlineKeyboardButton("🛵 Delivery", callback_data="sel_serv:DELIVERY")],
            [InlineKeyboardButton("🛍️ Retiro en Local", callback_data="sel_serv:RETIRO")],
            [InlineKeyboardButton("🍽️ Comer Aquí", callback_data="sel_serv:AQUI")]
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
        


    # ----------------------------------------------------
    #  7. Aprobar/Rechazar Pago (ADMIN)
    # ----------------------------------------------------
    if query.data.startswith("aprobar_pago:"):
        await handle_payment_approval(update, context)
        return
    
    if query.data.startswith("rechazar_pago:"):
        await handle_payment_rejection(update, context)
        return

    # Otros callbacks se irán agregando aquí...
    
    await query.edit_message_text("¡Entendido! 👍")


async def show_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Crea la orden en el backend y muestra datos de pago.
    """
    query = update.callback_query
    telegram_id = update.effective_user.id
    
    item = context.user_data.get("pending_order_item", "Producto desconocido")
    precio_base = context.user_data.get("pending_order_price", 10.0)
    service_type = context.user_data.get("service_type", "AQUI")
    location = context.user_data.get("location", "Dirección por defecto")
    
    precio_final_usd = precio_base
    
    # Mapeo simple para el backend
    final_service = 'LLEVAR' if service_type in ['DELIVERY', 'RETIRO'] else 'AQUI'
    delivery_mode = service_type if service_type in ['DELIVERY', 'RETIRO'] else None
    
    # Preparar items para el backend if available
    items_list = []
    raw_items = context.user_data.get("pending_order_items", [])
    for i in raw_items:
        # Calcular unitario (precio total / cantidad) o usar base si estuviera guardado
        # Aquí asumimos que i['precio'] es el total de esa línea
        cant = i.get("cantidad", 1)
        total_line = i.get("precio", 0)
        unitario = total_line / cant if cant > 0 else total_line
        
        if i.get("id"):
            items_list.append({
                "product_id": i.get("id"),
                "cantidad": cant,
                "precio_unitario": unitario
            })
    
    # Crear payload
    payload = {
        "telegram_id": telegram_id,
        "customer_name": update.effective_user.first_name,
        "item": item,
        "precio": precio_final_usd,
        "status": "esperando_pago",
        "service_type": final_service,
        "location": location,
        "delivery_mode": delivery_mode,
        "items": items_list
    }
    
    # Enviar al backend
    try:
        url = ORDERS_URL if ORDERS_URL.endswith("/") else f"{ORDERS_URL}/"
        resp = requests.post(url, json=payload, timeout=5)
        
        if resp.status_code in (200, 201):
            data_resp = resp.json()
            order_id = data_resp.get("id")
            context.user_data["pending_order_id"] = order_id
        else:
            error_msg = f"Error creando orden: {resp.text}"
            if query:
                await query.edit_message_text(error_msg)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=error_msg)
            return
            
    except Exception as e:
        print(f"Error backend: {e}")
        error_msg = "Hubo un error de conexión creando tu orden. 😓"
        if query:
            await query.edit_message_text(error_msg)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=error_msg)
        return

    # Mostrar datos de pago
    tasa = EXCHANGE_RATE_FIXED
    monto_bs = precio_final_usd * tasa
    
    msg_pago = (
        f"✅ *Orden #{context.user_data.get('pending_order_id', '???')} Creada*\n"
        f"📦 Pedido: {item}\n"
        f"🛵 Servicio: {service_type}\n"
        f"📍 Entrega: {location}\n"
        f"💵 Total a pagar: *${precio_final_usd:.2f}* (Bs. {monto_bs:,.2f})\n\n"
        "💳 *Datos de Pago (Pago Móvil):*\n"
        "• Banco: BANESCO (0134)\n"
        "• Teléfono: 0424-0000000\n"
        "• Cédula: V-12345678\n\n"
        "📸 *Envía la FOTO del comprobante para verificar.*"
    )

    if query:
        await query.edit_message_text(msg_pago, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg_pago, parse_mode="Markdown")
