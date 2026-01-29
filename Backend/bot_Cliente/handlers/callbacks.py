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
    # 3. ESTADO PEDIDO
    # --------------------------------------------------------------------------
    if data == "estado_pedido":
        # Simulación de respuesta proactiva
        await query.edit_message_text(
            f"Déjame revisar en la cocina... 👨‍🍳\n\n"
            "📝 Si pediste hace poco, seguro lo están preparando con mucho cariño.\n"
            "🚚 Si ya salió, ¡debe estar por llegar!\n\n"
            "¿Te puedo ayudar con algo más mientras esperas? 😊",
            parse_mode="Markdown"
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
    # 6. CONFIRMAR PEDIDO -> GUARDAR -> TRIGGER PAGO
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
            [InlineKeyboardButton("🛍️ Pick Up (Para llevar)", callback_data="sel_serv:PICKUP")],
            [InlineKeyboardButton("🍽️ Comer Aquí", callback_data="sel_serv:HERE")]
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
            [InlineKeyboardButton("🛍️ Pick Up (Para llevar)", callback_data="sel_serv:PICKUP")],
            [InlineKeyboardButton("🍽️ Comer Aquí", callback_data="sel_serv:HERE")]
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
        
    if data == "canjear_puntos":
        context.user_data["state"] = "waiting_for_points"
        await query.edit_message_text(
            "💎 *Canje de Puntos de Fidelidad*\n\n"
            "Recuerda: *25 puntos = $1.00* de descuento.\n\n"
            "¿Cuántos puntos deseas canjear? (Escribe el número aquí abajo) 👇",
            parse_mode="Markdown"
        )
        return

    if data == "cancelar_canje":
        context.user_data["points_to_redeem"] = 0
        context.user_data["discount_amount"] = 0
        await show_payment_info(update, context)
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
    service_type = context.user_data.get("service_type", "HERE")
    location = context.user_data.get("location", "Dirección por defecto")
    
    # Lógica de Puntos
    discount = context.user_data.get("discount_amount", 0)
    points_to_redeem = context.user_data.get("points_to_redeem", 0)
    precio_final_usd = max(0, precio_base - discount)
    
    # Mapeo simple para el backend
    final_service = 'TOGO' if service_type in ['DELIVERY', 'PICKUP'] else 'HERE'
    delivery_mode = service_type if service_type in ['DELIVERY', 'PICKUP'] else None
    
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
        "payment_data": {
            "points_redeemed": points_to_redeem,
            "discount_applied": discount
        }
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
            await query.edit_message_text(f"Error creando orden: {resp.text}")
            return
            
    except Exception as e:
        print(f"Error backend: {e}")
        await query.edit_message_text("Hubo un error de conexión creando tu orden. 😓")
        return

    # Obtener puntos del cliente
    try:
        from bot.models import LoyaltyPoints
        with open("points_debug.log", "a") as f:
            f.write(f"DEBUG [Points] {datetime.datetime.now()} - Buscando para: {telegram_id} (type: {type(telegram_id)})\n")
        
        loyalty = LoyaltyPoints.objects.filter(telegram_id=telegram_id).first()
        if loyalty:
            puntos_actuales = loyalty.puntos
            with open("points_debug.log", "a") as f:
                f.write(f"DEBUG [Points] Encontrados: {puntos_actuales} para {telegram_id}\n")
        else:
            puntos_actuales = 0
            with open("points_debug.log", "a") as f:
                f.write(f"DEBUG [Points] NO ENCONTRADO para {telegram_id}\n")
    except Exception as e:
        with open("points_debug.log", "a") as f:
            f.write(f"DEBUG [Points] ERROR: {e}\n")
        puntos_actuales = 0

    # Mostrar datos de pago
    tasa = EXCHANGE_RATE_FIXED
    monto_bs = precio_final_usd * tasa
    
    msg_pago = (
        f"✅ *Orden #{context.user_data.get('pending_order_id', '???')} Creada*\n"
        f"📦 Pedido: {item}\n"
        f"🛵 Servicio: {service_type}\n"
        f"📍 Entrega: {location}\n"
    )

    if discount > 0:
        msg_pago += f"💎 Descuento aplicado: -${discount:.2f}\n"

    msg_pago += (
        f"💵 Total a pagar: *${precio_final_usd:.2f}* (Bs. {monto_bs:,.2f})\n\n"
        f"🌟 Tus puntos actuales: *{puntos_actuales}*\n"
        "💳 *Datos de Pago (Pago Móvil):*\n"
        "• Banco: BANESCO (0134)\n"
        "• Teléfono: 0424-0000000\n"
        "• Cédula: V-12345678\n\n"
        "📸 *Envía la FOTO del comprobante para verificar.*"
    )

    keyboard = []
    if discount == 0 and puntos_actuales >= 25:
        keyboard.append([InlineKeyboardButton("💎 Canjear Puntos por Descuento", callback_data="canjear_puntos")])
    elif discount > 0:
        keyboard.append([InlineKeyboardButton("❌ Quitar Descuento", callback_data="cancelar_canje")])

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query:
            await query.edit_message_text(msg_pago, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=msg_pago, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        if query:
            await query.edit_message_text(msg_pago, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=msg_pago, parse_mode="Markdown")
