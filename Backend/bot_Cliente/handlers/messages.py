"""
Message Handlers
Manejo de mensajes de texto con enfoque proactivo y conversacional.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from bot_Cliente.intents import INTENTS, RESPONSES
from bot_Cliente.services.order_service import interpretar_pedido, save_order
from bot_Cliente.utils.proactive_messages import (
    get_random_message, 
    get_suggestive_question,
    get_proactive_followup,
    UNKNOWN_INTENT_RESPONSES,
    ORDER_CONFIRMATION_QUESTIONS
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler principal de mensajes de texto.
    1. Interpreta si es pedido.
    2. Si no, busca intención (Saludo, Hambre, etc.).
    3. Si no, respuesta fallback proactiva.
    """
    texto_usuario = update.message.text
    nombre = update.effective_user.first_name
    telegram_id = update.effective_user.id
    
    # -------------------------------------------------------------
    # 0. Manejo de ESTADOS (Dirección, etc.)
    # -------------------------------------------------------------
    state = context.user_data.get("state")
    
    if state == "waiting_for_address":
        context.user_data["location"] = texto_usuario
        context.user_data["state"] = None
        from bot_Cliente.handlers.callbacks import show_payment_info
        await show_payment_info(update, context)
        return

    # -------------------------------------------------------------
    # 1. Intentar interpretar como PEDIDO
    # -------------------------------------------------------------
    
    # -------------------------------------------------------------
    # 1. Intentar interpretar como PEDIDO
    # -------------------------------------------------------------
    
    # Helper async para consultar DB (Movido fuera para reutilizar)
    @sync_to_async
    def check_table_availability():
        from core.models import Table
        total = Table.objects.count()
        occupied = Table.objects.filter(is_occupied=True).count()
        return total, occupied

    resultado_pedido = await interpretar_pedido(texto_usuario)

    if resultado_pedido["es_pedido_valido"]:
        # SOLO si es un pedido válido verificamos mesas para COMER AQUI
        # Nota: Idealmente preguntar si es para llevar, pero por seguridad validamos de entrada
        # o advertimos.
        
        total_tables, occupied_tables = await check_table_availability()
        
        # Si están llenas, advertimos pero permitimos pedir para llevar (futura mejora)
        # Por ahora mantenemos la lógica restrictiva solo para pedidos nuevos
        if total_tables > 0 and occupied_tables >= total_tables:
             await update.message.reply_text(
                "⚠️ *Estimado cliente*\n\n"
                "En este momento todas nuestras mesas están ocupadas. 😓\n"
                "Solo estamos tomando pedidos para **Delivery** o **Para Llevar**.\n\n"
                "¿Deseas continuar con tu pedido?",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Sí, para llevar/delivery", callback_data="confirmar_pedido_multiple")],
                    [InlineKeyboardButton("Cancelar", callback_data="cancelar")]
                ])
            )
             # Guardamos contexto igual por si dice que sí
             context.user_data["ultimo_pedido_interpretado"] = resultado_pedido
             return

        items = resultado_pedido.get("items", [])
        total = resultado_pedido.get("total", 0)
        pedido_final = resultado_pedido["pedido_final"]
        
        # Guardar en contexto temporal por si confirma
        context.user_data["ultimo_pedido_interpretado"] = resultado_pedido
        
        msg = f"Qué rico! Entendí que quieres:\n\n"
        
        # Listar cada item
        for item in items:
            msg += f"• {item['cantidad']} x {item['producto']}\n"
        
        msg += f"\nTotal: ${total:.2f}\n\n"
        msg += "Le agregamos algo más a tu pedido?"
        
        keyboard = [
            [InlineKeyboardButton("Confirmar y Pedir", callback_data="confirmar_pedido_multiple")],
            [InlineKeyboardButton("Modificar Ingredientes", callback_data="ayuda_pedido")],
            [InlineKeyboardButton("Cancelar", callback_data="cancelar")]
        ]
        
        await update.message.reply_text(
            msg, 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # -------------------------------------------------------------
    # 2. Buscar INTENCIONES (NLP Básico)
    # -------------------------------------------------------------
    texto_lower = texto_usuario.lower()
    
    intent_encontrado = None
    for intent, keywords in INTENTS.items():
        if any(kw in texto_lower for kw in keywords):
            intent_encontrado = intent
            break
            
    if intent_encontrado:
        # LOGICA ESPECIAL PARA RESERVA
        if intent_encontrado == "RESERVA":
            total_tables, occupied_tables = await check_table_availability()
            available = total_tables - occupied_tables
            
            if available > 0:
                 await update.message.reply_text(
                    f"✅ ¡Sí! Tenemos **{available} mesas disponibles** en este momento.\n\n"
                    "Trabajamos por orden de llegada, ¡así que vente antes de que se llenen! 🏃‍♂️💨\n\n"
                    "¿Te gustaría ir viendo el menú?",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📜 Ver Menú", callback_data="ver_menu_proactivo")]])
                )
            else:
                await update.message.reply_text(
                    "❌ Lo siento, en este momento **estamos full** (todas las mesas ocupadas).\n\n"
                    "Pero puedes pedir para **Llevar** o **Delivery**. 🛵",
                    parse_mode="Markdown"
                )
            return

        # Obtener respuesta base del diccionario
        respuesta_base = get_random_message(RESPONSES[intent_encontrado])
        
        # Enriquecer con proactividad si es necesario
        if intent_encontrado == "SALUDO":
            # Ya el diccionario tiene buenas preguntas, pero aseguramos
            pass
        elif intent_encontrado == "HAMBRE":
             # Sugerir algo específico
             sugerencia = get_suggestive_question()
             respuesta_base += f"\n\n{sugerencia}"
             
        await update.message.reply_text(respuesta_base, parse_mode="Markdown")
        return

    # -------------------------------------------------------------
    # 3. Fallback PROACTIVO (No entendí)
    # -------------------------------------------------------------
    # En lugar de solo decir "no entendí", guiamos al usuario
    msg = get_random_message(UNKNOWN_INTENT_RESPONSES)
    
    msg += "\n\nSi quieres ver lo que tenemos, puedes tocar aquí 👇"
    
    keyboard = [[InlineKeyboardButton("📜 Ver Menú", callback_data="ver_menu_proactivo")]]
    
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
