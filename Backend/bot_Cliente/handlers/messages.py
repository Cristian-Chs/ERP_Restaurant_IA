"""
Message Handlers
Manejo de mensajes de texto con enfoque proactivo y conversacional.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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
    # 0. Manejo de ESTADOS (Dirección, Puntos, etc.)
    # -------------------------------------------------------------
    state = context.user_data.get("state")
    
    if state == "waiting_for_address":
        context.user_data["location"] = texto_usuario
        context.user_data["state"] = None
        from bot_Cliente.handlers.callbacks import show_payment_info
        await show_payment_info(update, context)
        return

    if state == "waiting_for_points":
        try:
            puntos = int(texto_usuario)
            from bot.models import LoyaltyPoints
            loyalty = LoyaltyPoints.objects.filter(telegram_id=telegram_id).first()
            
            if not loyalty or loyalty.puntos < puntos:
                await update.message.reply_text(
                    f"❌ No tienes suficientes puntos. Tu saldo actual es de *{loyalty.puntos if loyalty else 0}* puntos.",
                    parse_mode="Markdown"
                )
                return
            
            if puntos < 25:
                await update.message.reply_text("❌ El canje mínimo es de 25 puntos ($1).")
                return

            # Calcular descuento
            discount = puntos / 25.0
            context.user_data["points_to_redeem"] = puntos
            context.user_data["discount_amount"] = discount
            context.user_data["state"] = None
            
            from bot_Cliente.handlers.callbacks import show_payment_info
            await show_payment_info(update, context)
            return
            
        except ValueError:
            await update.message.reply_text("❌ Por favor, ingresa un número válido de puntos.")
            return

    # -------------------------------------------------------------
    # 1. Intentar interpretar como PEDIDO
    # -------------------------------------------------------------
    resultado_pedido = await interpretar_pedido(texto_usuario)
    
    if resultado_pedido["es_pedido_valido"]:
        pedido_final = resultado_pedido["pedido_final"]
        producto_base = resultado_pedido["producto"]
        
        # Guardar en contexto temporal por si confirma
        context.user_data["ultimo_pedido_interpretado"] = resultado_pedido
        
        msg = f"¡Qué rico! 😋 Entendí que quieres:\n\n"
        msg += f"🍽️ **{pedido_final}**\n\n"
        
        # Pregunta proactiva de confirmación
        pregunta = get_random_message(ORDER_CONFIRMATION_QUESTIONS)
        msg += f"*{pregunta}*"
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar y Pedir", callback_data=f"pedido:{producto_base}")],
            [InlineKeyboardButton("📝 Modificar Ingredientes", callback_data="ayuda_pedido")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
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
