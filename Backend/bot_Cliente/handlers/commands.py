"""
Command Handlers
Manejadores de comandos del bot (/start, /menu, /soporte, etc.)
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async
import requests

from core.models import Product
from bot_Cliente.config import GUSTOS_URL


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /start - Mensaje de bienvenida con botones principales.
    """
    nombre = update.effective_user.first_name

    # Saludo proactivo basado en la hora y variaciones
    from bot_Cliente.utils.proactive_messages import get_time_based_greeting, get_suggestive_question
    
    texto_bienvenida = get_time_based_greeting(nombre) + "\n\n"
    texto_bienvenida += "Voy a ser tu mesero hoy. 🤵\n\n"
    texto_bienvenida += "*Selecciona lo que quieras hacer:* 👇"

    keyboard = [
        [InlineKeyboardButton("🍔 Hacer un pedido", callback_data="ayuda_pedido")],
        [InlineKeyboardButton("🧾 Consultar mi pedido", callback_data="estado_pedido")],
        [InlineKeyboardButton("💬 Hablar con soporte", callback_data="soporte")]
    ]

    await update.message.reply_text(
        texto_bienvenida,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /menu - Muestra todos los productos activos agrupados por categoría.
    """
    # Obtener productos de la base de datos usando sync_to_async
    productos = await sync_to_async(list)(
        Product.objects.filter(is_active=True).prefetch_related('ingredientes').order_by('category', 'name')
    )
    
    # Deteminar destinatario del mensaje (Comando o Callback)
    if update.message:
        message_target = update.message
    elif update.callback_query:
        message_target = update.callback_query.message
    else:
        return
    
    if not productos:
        await message_target.reply_text(
            " No hay productos disponibles en este momento.",
            parse_mode="Markdown"
        )
        return
    
    # Agrupar productos por categoría
    categorias = {
        'promociones': [],
        'entradas': [],
        'principales': [],
        'postres': [],
        'bebidas': []
    }
    
    for producto in productos:
        categoria = producto.category
        if categoria in categorias:
            categorias[categoria].append(producto)
    
    # Construir mensaje
    mensaje = "*Los Cuatros Sabores de Paraguaná\n\nMENÚ DEL RESTAURANTE*\n\n"
    
    # Emojis y nombres por categoría
    emojis = {
        'promociones': '',
        'entradas': '',
        'principales': '',
        'postres': '',
        'bebidas': ''
    }
    
    nombres_categorias = {
        'entradas': 'ENTRADAS',
        'principales': 'PLATOS PRINCIPALES',
        'postres': 'POSTRES',
        'bebidas': 'BEBIDAS',
        'promociones': 'PROMOCIONES'
    }
    
    for categoria_key in ['entradas', 'principales', 'postres', 'bebidas', 'promociones']:
        items = categorias[categoria_key]
        
        if items:
            emoji = emojis.get(categoria_key, '')
            nombre_categoria = nombres_categorias.get(categoria_key, categoria_key.upper())
            
            mensaje += f"{emoji} *{nombre_categoria}*\n"
            
            for producto in items:
                precio = f"${float(producto.price):.2f}"
                mensaje += f"  • {producto.name} - {precio}\n"
                
                # Obtener ingredientes del producto
                ingredientes = await sync_to_async(list)(
                    producto.ingredientes.all().values_list('nombre', flat=True)
                )
                
                if ingredientes:
                    ingredientes_texto = ", ".join(ingredientes)
                    mensaje += f"    _({ingredientes_texto})_\n"
            
            mensaje += "\n"
    
    from bot_Cliente.utils.proactive_messages import get_random_message, MENU_FOLLOWUPS

    mensaje += "📝 *¿Qué tal? ¿Viste algo que te guste?*\n\n"
    mensaje += "Para pedir, solo escríbeme:\n"
    mensaje += "_'Quiero una hamburguesa sin cebolla'_\n"
    mensaje += "_'Dame una pizza con bacon'_\n\n"
    
    # Pregunta proactiva al final
    pregunta = get_random_message(MENU_FOLLOWUPS)
    mensaje += f"*{pregunta}*"

    await message_target.reply_text(mensaje, parse_mode="Markdown")


async def menu_personalizado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /menu_personalizado - Muestra menú basado en gustos del usuario.
    """
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name
    
    try:
        response = requests.get(f"{GUSTOS_URL}{telegram_id}/", timeout=5)
        gustos = response.json().get("gustos", []) if response.status_code == 200 else []
    except:
        gustos = []

    # Deteminar destinatario del mensaje (Comando o Callback)
    if update.message:
        message_target = update.message
    elif update.callback_query:
        message_target = update.callback_query.message
    else:
        return

    if not gustos:
        await message_target.reply_text(
            f" {nombre}, aún no tengo tus gustos registrados.\n"
            "Puedes configurarlos enviando: *Me gusta [plato]*",
            parse_mode="Markdown"
        )
        return

    texto_menu = "🍽️ *Tu menú personalizado (cosas que te encantan):*\n\n"
    for plato in gustos:
        texto_menu += f"• {plato}\n"
    
    texto_menu += "\n*¿Te provoca alguno de estos ahora?* 😋"

    await message_target.reply_text(texto_menu, parse_mode="Markdown")


async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /soporte - Información de contacto para soporte.
    """
    texto = (
        " *Soporte al Cliente*\n\n"
        "Si necesitas ayuda, contáctanos:\n"
        "• Teléfono: +58 269 34 567 890\n"
        "• Email: soporte@restaurante.com\n"
        "• Horario: Lun-Dom 9:00 - 22:00\n\n"
    )

    if update.callback_query:
        # Si viene de un botón
        await update.callback_query.message.reply_text(texto + "\n¿En qué te puedo ayudar específicamente? 🤔", parse_mode="Markdown")
        await update.callback_query.answer()
    else:
        # Si viene de comando /soporte
        await update.message.reply_text(texto + "\n¿Tienes alguna duda con tu pedido? Estoy aquí. 👂", parse_mode="Markdown")
