import sys, os


# 👇 Añade la carpeta que contiene el directorio 'ml' al PYTHONPATH.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

# 👇 Resto de tus imports
import logging
import requests
import pytz
import asyncio
import datetime
import aiohttp

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
from asgiref.sync import sync_to_async
from rapidfuzz import process, fuzz

# Importaciones de modelos Django
from core.models import Product, Ingredient
from bot.models import PedidoPersonalizado, PreferenciaIngrediente, Order

# Importaciones de ML
from ml.predict import recomendar_ml, recomendar_popularidad

# Importaciones de Intents (Mesero Inteligente)
from bot_Cliente.intents import INTENTS, RESPONSES
import random


# ----------------------------------------------------
# ⚙️ Configuración
# ----------------------------------------------------
ORDERS_URL = "http://127.0.0.1:8000/bot/orders/"
GUSTOS_URL = "http://127.0.0.1:8000/bot/gustos/"
HISTORIAL_URL = "http://127.0.0.1:8000/bot/historial/"
POPULARIDAD_URL = "http://127.0.0.1:8000/bot/popularidad/"
RATING_URL = "http://127.0.0.1:8000/bot/rating/"
SIMILAR_URL = "http://127.0.0.1:8000/bot/recomendacion_similar/"
HIBRIDA_URL = "http://127.0.0.1:8000/bot/recomendacion_hibrida/"
PRODUCTOS_URL = "http://127.0.0.1:8000/bot/productos/"
RECOMENDACION_URL = "http://127.0.0.1:8000/bot/recomendacion/"



BOT_TOKEN_CLIENTE = "8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU"
CHEF_CHAT_ID = 5719602467
ADMIN_CHAT_ID = 5719602467  # Admin que aprueba/rechaza pagos


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
# ----------------------------------------------------
# 🧹 Limpieza de texto y Extracción de Cantidad
# ----------------------------------------------------
def extraer_cantidad_y_producto(texto: str) -> tuple[int | None, str]:
    texto = texto.strip()
    
    # 1. Regex para detectar números al inicio (ej: "2 hamburguesas", "3x pizza")
    match_numero = re.search(r'^(\d+)\s*(?:x\s*)?', texto, re.IGNORECASE)
    if match_numero:
        cantidad = int(match_numero.group(1))
        producto = texto[match_numero.end():].strip()
        return cantidad, producto
    
    # 2. Regex para palabras de cantidad (básico)
    mapa_numeros = {
        "una": 1, "un": 1, "uno": 1,
        "dos": 2, "dós": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6
    }
    
    palabras = texto.split(" ", 1)
    primera_palabra = palabras[0].lower()
    
    if primera_palabra in mapa_numeros:
        cantidad = mapa_numeros[primera_palabra]
        producto = palabras[1].strip() if len(palabras) > 1 else ""
        return cantidad, producto
        
    return None, texto


def parsear_resumen_web(texto: str) -> dict | None:
    """
    Intenta parsear un resumen de pedido pegado desde la web.
    Ejemplo:
    *🛒 Resumen del Pedido:*
    1. *Arepitas dulces* (1 x $3.50)
    ...
    *💰 TOTAL FINAL: $100.49*
    """
    if "Resumen del Pedido" not in texto and "TOTAL FINAL" not in texto:
        return None

    # 1. Extraer items:  1. *Nombre* (Cant x $Precio)
    # Regex: \d+\.\s*\*(.+?)\*\s*\((\d+)\s*x
    items_found = re.findall(r'\d+\.\s*\*(.+?)\*\s*\((\d+)\s*x', texto)
    
    if not items_found:
        return None

    # Construir string de pedido final
    # Ej: "1 x Arepitas dulces, 1 x Hamburguesa"
    partes_pedido = []
    for nombre, cant in items_found:
        partes_pedido.append(f"{cant} x {nombre}")
    
    pedido_final_str = ", ".join(partes_pedido)

    # 2. Extraer Total
    match_total = re.search(r'TOTAL FINAL:\s*\$([\d\.]+)', texto)
    precio_total = float(match_total.group(1)) if match_total else 0.0

    return {
        "producto_base": "Pedido Web", # Marcador genérico
        "cantidad": 1,
        "removidos": [],
        "agregados": [],
        "pedido_final": pedido_final_str,
        "texto_original": texto,
        "precio": precio_total
    }


def clean_order_text(text: str) -> str:
    # Eliminar frases comunes (Case Insensitive)
    # Orden importa: frases largas primero
    frases = [
        "quiero pedir", "me gustaría ordenar", "por favor confirma", "hay disponible",
        "quiero una", "quiero un", "dame una", "dame un",
        "quisiera una", "quisiera un", "me gustaría una", "me gustaría un",
        "me gustaria", "quisiera", "ordenar", "pedir",
        "quiero", "dame", "por favor", "necesito",
        "ordenas", "tienes", "tendras", "me das", "me da", "disponible",
        "mejor", "solo", "solamente", "cambia a", "cambiar a", "son", "serian"
    ]
    
    cleaned_text = text
    for frase in frases:
        # \b para asegurar que son palabras completas (opcional, pero recomendando)
        # Aquí usamos simple sustitución, pero limpiamos espacios múltiples después
        cleaned_text = re.sub(frase, "", cleaned_text, flags=re.IGNORECASE)
        
    # Eliminar símbolos y espacios extra
    cleaned_text = cleaned_text.replace("*", "").replace("-", "").strip()
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text) # Colapsar espacios
    
    return cleaned_text

# ----------------------------------------------------
# ✅ OCR PARA LEER COMPROBANTES DE PAGO
# ----------------------------------------------------
# ----------------------------------------------------
# ✅ OCR PARA LEER COMPROBANTES DE PAGO
# ----------------------------------------------------
import re

OCR_API_URL = "https://api.ocr.space/parse/image"
OCR_API_KEY = "K83178149188957"  # Regístrate en ocr.space y coloca tu API key aquí

BANCOS = [
    "BANESCO", "BOD", "MERCANTIL", "PROVINCIAL", "BNC", "VENEZUELA",
    "BANCARIBE", "BANCO DEL TESORO", "BANCO PLAZA"
]

def extraer_referencia(text):
    match = re.search(r'\b\d{8,12}\b', text)
    return match.group() if match else "N/A"

def extraer_fecha(text):
    match = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', text)
    return match.group() if match else "N/A"

def extraer_monto(text):
    match = re.search(r'(\d+[.,]\d{2})', text)
    return match.group() if match else "N/A"

def extraer_telefono(text):
    match = re.search(r'\b(04\d{9})\b', text)
    return match.group() if match else "N/A"

def extraer_banco(text):
    banco, score, _ = process.extractOne(text, BANCOS)
    return banco if score > 70 else "N/A"

def extraer_tipo_operacion(text):
    if "pago móvil" in text.lower():
        return "Pago Móvil"
    elif "transferencia" in text.lower():
        return "Transferencia"
    elif "depósito" in text.lower():
        return "Depósito"
    else:
        return "N/A"

async def extraer_datos_comprobante(file_path: str) -> dict:
    try:
        with open(file_path, 'rb') as f:
            payload = {
                'apikey': OCR_API_KEY,
                'language': 'spa',
                'isOverlayRequired': False,
                'OCREngine': '2'
            }
            response = requests.post(OCR_API_URL, files={'file': f}, data=payload)
            result = response.json()

        if result.get("IsErroredOnProcessing"):
            return {"error": result.get("ErrorMessage", "Error en OCR")}

        text = result['ParsedResults'][0]['ParsedText']

        data = {
            "numero_referencia": extraer_referencia(text),
            "fecha": extraer_fecha(text),
            "monto": extraer_monto(text),
            "banco_emisor": extraer_banco(text),
            "banco_receptor": extraer_banco(text),
            "telefono_origen": extraer_telefono(text),
            "telefono_destino": extraer_telefono(text),
            "tipo_operacion": extraer_tipo_operacion(text),
        }

        return data

    except Exception as e:
        logging.error(f"Error en OCR: {e}")
        return {"error": str(e)}



# ----------------------------------------------------
# 📝 Formatear pedido
# ----------------------------------------------------


# ----------------------------------------------------
# ✅ MENÚ COMPLETO (desde base de datos)
# ----------------------------------------------------
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra todos los productos activos agrupados por categoría.
    """
    # Obtener productos de la base de datos usando sync_to_async
    productos = await sync_to_async(list)(
        Product.objects.filter(is_active=True).prefetch_related('ingredientes').order_by('category', 'name')
    )
    
    if not productos:
        await update.message.reply_text(
            "⚠️ No hay productos disponibles en este momento.",
            parse_mode="Markdown"
        )
        return
    
    # Agrupar productos por categoría
    categorias = {
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
    mensaje = "🍽️*Los Cuatros Sabores de Paraguaná\n\nMENÚ DEL RESTAURANTE*\n\n"
    # Emojis por categoría
    emojis = {
        'entradas': '🥗',
        'principales': '🍖',
        'postres': '🍰',
        'bebidas': '🥤'
    }
    
    # Nombres de categorías
    nombres_categorias = {
        'entradas': 'ENTRADAS',
        'principales': 'PLATOS PRINCIPALES',
        'postres': 'POSTRES',
        'bebidas': 'BEBIDAS'
    }
    
    for categoria_key in ['entradas', 'principales', 'postres', 'bebidas']:
        items = categorias[categoria_key]
        
        if items:
            emoji = emojis.get(categoria_key, '📌')
            nombre_categoria = nombres_categorias.get(categoria_key, categoria_key.upper())
            
            mensaje += f"{emoji} *{nombre_categoria}*\n"
            
            for producto in items:
                precio = f"${float(producto.price):.2f}"
                mensaje += f"  • {producto.name} - {precio}\n"
                
                # ✅ Obtener ingredientes del producto
                ingredientes = await sync_to_async(list)(
                    producto.ingredientes.all().values_list('nombre', flat=True)
                )
                
                if ingredientes:
                    ingredientes_texto = ", ".join(ingredientes)
                    mensaje += f"    _({ingredientes_texto})_\n"
            
            mensaje += "\n"
    
    mensaje += "💬 Para pedir, escribe:\n"
    mensaje += "_'Quiero una hamburguesa sin cebolla'_\n"
    mensaje += "_'Dame una pizza con bacon'_"
    
    await update.message.reply_text(mensaje, parse_mode="Markdown")

# ----------------------------------------------------
# ✅ INTERPRETAR PEDIDO CON MODIFICACIONES
# ----------------------------------------------------

async def interpretar_pedido(texto_usuario: str):
    # 1. Limpieza inicial
    texto_limpio = clean_order_text(texto_usuario)
    
    # 2. Extraer cantidad y texto restante
    cantidad, texto_sin_cantidad = extraer_cantidad_y_producto(texto_limpio)
    
    # Si no se especificó cantidad, asumimos 1 por defecto para interpretar la orden base
    cantidad_final = cantidad if cantidad is not None else 1
    
    # 3. Detectar producto base usando el texto sin cantidad
    producto_base = extraer_producto_base(texto_sin_cantidad)
    
    if not producto_base:
        # Retornamos la cantidad detectada (puede ser None o un número) para que handle_message lo use
        return None, cantidad, [], [], None

    # 4. Obtener ingredientes del plato + extras globales
    ingredientes_menu = await obtener_ingredientes_producto(producto_base)

    # 5. Detectar removidos y agregados (Usamos texto_sin_cantidad para evitar ruido)
    removidos = extraer_ingredientes_removidos(texto_sin_cantidad, ingredientes_menu)
    agregados = extraer_ingredientes_agregados(texto_sin_cantidad, ingredientes_menu)

    # 6. Construir pedido final
    # Formato: "2 x Hamburguesa sin cebolla"
    pedido_str = construir_pedido_final(producto_base, removidos, agregados)
    
    if cantidad_final > 1:
        pedido_final = f"{cantidad_final} x {pedido_str}"
    else:
        pedido_final = pedido_str

    print("\n===== DEBUG interpretar_pedido =====")
    print("Texto original:", texto_usuario)
    print("Cantidad detectada:", cantidad)
    print("Producto base:", producto_base)
    print("Pedido final:", pedido_final)
    print("====================================\n")

    return producto_base, cantidad_final, removidos, agregados, pedido_final


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
# ✅ SOPORTE
# ----------------------------------------------------
async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📞 *Soporte al Cliente*\n\n"
        "Si necesitas ayuda, contáctanos:\n"
        "• Teléfono: +58 269 34 567 890\n"
        "• Email: soporte@restaurante.com\n"
        "• Horario: Lun-Dom 9:00 - 22:00\n\n"
    )

    if update.callback_query:
        # Si viene de un botón
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
        await update.callback_query.answer()
    else:
        # Si viene de comando /soporte
        await update.message.reply_text(texto, parse_mode="Markdown")

# ----------------------------------------------------
# ✅ START + TECLADO INFERIOR    (Arreglar botones)
# ----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name

    # ✅ Mensaje de Bienvenida "Mesero"
    texto_bienvenida = (
        f"¡Hola {nombre}! 👋\n"
        f"Soy tu mesero virtual en *4 Sabores*.\n\n"
        f"Selecciona una opción para comenzar:"
    )

    # ✅ Botones principales
    keyboard = [
        [InlineKeyboardButton("🍔 Hacer un pedido", callback_data="ayuda_pedido")],
        [InlineKeyboardButton("📦 Consultar mi pedido", callback_data="estado_pedido")],
        [InlineKeyboardButton("📞 Hablar con soporte", callback_data="soporte")]
    ]

    await update.message.reply_text(
        texto_bienvenida,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ----------------------------------------------------
# ✅ OBTENER INGREDIENTES DE UN PRODUCTO
# ----------------------------------------------------

async def obtener_ingredientes_producto(producto_base: str) -> list[str]:
    ingredientes_finales = []

    # ✅ 1. Ingredientes del plato desde el backend
    try:
        r = requests.get(f"{PRODUCTOS_URL}?detalle={producto_base}", timeout=5)
        data = r.json()

        # Tu backend probablemente devuelve algo como:
        # { "nombre": "hamburguesa", "ingredientes": ["tomate", "queso"] }
        ingredientes_plato = data.get("ingredientes", [])
    except Exception as e:
        print("ERROR obteniendo ingredientes del plato:", e)
        ingredientes_plato = []

    # Normalizar
    for ing in ingredientes_plato:
        if isinstance(ing, dict):
            ingredientes_finales.append(ing.get("nombre", "").lower())
        else:
            ingredientes_finales.append(str(ing).lower())

    # ✅ 2. Ingredientes globales extra desde Django ORM (async-safe)
    try:
        # Usar sync_to_async para llamadas al ORM desde contexto asíncrono
        extras = await sync_to_async(list)(
            Ingredient.objects.filter(disponible_como_extra=True).values_list("nombre", flat=True)
        )
        for ing in extras:
            ing = ing.strip().lower()
            if ing not in ingredientes_finales:
                ingredientes_finales.append(ing)
    except Exception as e:
        print("ERROR obteniendo ingredientes extra:", e)

    print("DEBUG ingredientes_finales:", ingredientes_finales)
    return ingredientes_finales

# ----------------------------------------------------
# ✅ FUZZY MATCHING DE INGREDIENTES
# ----------------------------------------------------

def fuzzy_match_ingrediente(texto: str, ingredientes_menu: list[str], threshold=70):
    """
    Devuelve el ingrediente más parecido dentro del texto.
    """
    if not ingredientes_menu:
        return None
    
    texto = texto.lower()

    result = process.extractOne(
        texto,
        ingredientes_menu,
        scorer=fuzz.token_set_ratio
    )
    
    # process.extractOne puede devolver None si no hay coincidencias
    if result is None:
        return None
    
    mejor_match, score, _ = result

    if score >= threshold:
        return mejor_match

    return None


# ----------------------------------------------------
# ✅ RECOMENDACIÓN POR SIMILITUD SEMÁNTICA (EMBEDDINGS)
# ----------------------------------------------------
async def recomendacion_similar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name

    try:
        r = requests.get(f"{SIMILAR_URL}{telegram_id}/", timeout=5)
        data = r.json()
    except Exception as e:
        await update.message.reply_text("⚠️ No pude obtener recomendaciones similares.")
        return

    similares = data.get("similares", [])
    plato_base = data.get("plato_base", None)

    if not similares:
        await update.message.reply_text(
            f"⚠️ {nombre}, aún no tengo suficientes datos para recomendar platos similares.\n"
            "Califica algunos platos con ⭐ para mejorar tus recomendaciones."
        )
        return

    texto = f"🔍 *Platos similares a:* _{plato_base}_\n\n"
    keyboard = []

    for plato in similares:
    # ✅ Aplicar memoria personalizada (AHORA SÍ CON await)
        plato_personalizado = await aplicar_memoria_personalizada(telegram_id, plato)

        if not producto_es_valido(plato):
            continue

        texto += f"• {plato_personalizado}\n"

        keyboard.append([
            InlineKeyboardButton(
                plato_personalizado,
                callback_data=f"pedido:{plato_personalizado}"
            )
        ])

    keyboard.append([InlineKeyboardButton("🚫 No gracias", callback_data="rechazar_recomendacion")])

    await update.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ----------------------------------------------------
# ✅ SISTEMA DE RECOMENDACIÓN HÍBRIDO
# ----------------------------------------------------

async def recomendacion_hibrida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name

    # ✅ Consultar endpoint con ID en la URL
    try:
        # Aseguramos que la URL termine en / para concatenar el ID
        base_url = HIBRIDA_URL if HIBRIDA_URL.endswith("/") else f"{HIBRIDA_URL}/"
        r = requests.get(f"{base_url}{telegram_id}/", timeout=5)
        
        if r.status_code != 200:
            await update.message.reply_text("⚠️ No pude obtener recomendaciones en este momento.")
            return
            
        data = r.json()
        recomendaciones = data.get("recomendaciones", [])
        
    except Exception as e:
        print(f"Error recomendacion hibrida: {e}")
        await update.message.reply_text("⚠️ Error de conexión.")
        return

    if not recomendaciones:
        await update.message.reply_text(f"🤷‍♂️ {nombre}, aún no tengo suficientes datos para recomendarte algo.")
        return

    # ✅ Construir mensaje
    texto = f"🍽️ *Recomendaciones para ti, {nombre}*\n\n"
    
    # Podemos inferir el contexto según las fuentes, pero simplifiquemos el mensaje
    fuentes = data.get("fuentes", {})
    personal = fuentes.get("personal", [])
    
    if personal:
       texto += "💖 *Porque te encantan:*\n"
    else:
       texto += "🔥 *Tendencias del momento:*\n"
       
    keyboard = []
    for plato in recomendaciones:
        texto += f"• {plato}\n"
        keyboard.append([
            InlineKeyboardButton(f"Pedir {plato}", callback_data=f"pedido:{plato}")
        ])
        
    texto += "\n_Selecciona uno para pedirlo 👇_"

    await update.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ----------------------------------------------------
# ✅ RECOMENDACIONES 
#----------------------------------------------------

async def recomendaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    texto = update.message.text

    plato = clean_order_text(texto)

    # ✅ Aplicar memoria personalizada con ORM seguro
    plato_personalizado = await aplicar_memoria_personalizada(telegram_id, plato)

    # ✅ Obtener recomendación del backend
    r = requests.post(RECOMENDACION_URL, json={"plato": plato_personalizado})
    data = r.json()

    recomendacion = data.get("recomendacion", plato_personalizado)

    await update.message.reply_text(f"✅ Te recomiendo: {recomendacion}")

# ----------------------------------------------------
# ✅ EXTRAER INGREDIENTES REMOVIDOS
# ----------------------------------------------------


INGREDIENTES_REMOVIDOS_KEYWORDS = [
    "sin", "no lleva", "quita", "quitar", "no quiero", "sin nada de"
]

def extraer_ingredientes_removidos(texto: str, ingredientes_menu: list[str]) -> list[str]:
    texto = texto.lower()
    removidos = []

    for kw in INGREDIENTES_REMOVIDOS_KEYWORDS:
        if kw in texto:
            # Extraemos la parte después del keyword
            parte = texto.split(kw, 1)[-1]

            # Intentamos detectar cada ingrediente usando fuzzy matching
            match = fuzzy_match_ingrediente(parte, ingredientes_menu)
            if match and match not in removidos:
                removidos.append(match)

    return removidos


# ----------------------------------------------------
# ✅ EXTRAER INGREDIENTES AGREGADOS
# ----------------------------------------------------

INGREDIENTES_AGREGADOS_KEYWORDS = [
    "con", "agrega", "añade", "extra", "ponle", "más"
]

def extraer_ingredientes_agregados(texto: str, ingredientes_menu: list[str]) -> list[str]:
    texto = texto.lower()
    agregados = []

    for kw in INGREDIENTES_AGREGADOS_KEYWORDS:
        if kw in texto:
            parte = texto.split(kw, 1)[-1]

            # Intentamos detectar cada ingrediente usando fuzzy matching
            match = fuzzy_match_ingrediente(parte, ingredientes_menu)
            if match and match not in agregados:
                agregados.append(match)

    return agregados


#   

# ----------------------------------------------------
# ✅ MANEJAR CALLBACK DE RATING
# ----------------------------------------------------

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, plato, estrellas = query.data.split(":")
    except:
        await query.edit_message_text("⚠️ Error al procesar la calificación.")
        return

    telegram_id = query.from_user.id

    payload = {
        "telegram_id": telegram_id,
        "plato": plato,
        "rating": int(estrellas)
    }

    try:
        requests.post(RATING_URL, json=payload, timeout=5)
        await query.edit_message_text(f"✅ Gracias por tu calificación: {plato} — {estrellas} ⭐")
    except Exception as e:
        await query.edit_message_text("⚠️ No pude guardar tu rating.")

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
# ✅ CONSTRUIR PEDIDO FINAL CON MODIFICACIONES
# ----------------------------------------------------
def construir_pedido_final(producto, removidos, agregados):
    pedido = producto

    if removidos:
        pedido += " sin " + ", ".join(removidos)

    if agregados:
        pedido += " con " + ", ".join(agregados)

    return pedido


# ----------------------------------------------------
# ✅ LÓGICA DE MENSAJES DEL USUARIO
# ----------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    telegram_id = update.effective_user.id
    texto_usuario = (update.message.text or "").strip().lower()

    # ✅ 1.0 DETECTAR RESUMEN WEB (Prioridad Máxima)
    # ----------------------------------------------------
    # Verificamos si es un resumen pegado antes de cualquier charla
    pedido_web = parsear_resumen_web(update.message.text or "") # Usamos texto original con case
    if pedido_web:
        producto_base = pedido_web["producto_base"]
        pedido_final = pedido_web["pedido_final"]
        precio_total = pedido_web["precio"]
        
        pedido_key = "pedido_carrito"
        context.user_data[pedido_key] = pedido_web
        
        keyboard = [
            [
                InlineKeyboardButton(f"💸 Pagar ${precio_total:.2f}", callback_data=f"proceder_pago:{pedido_key}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")
            ]
        ]
        
        await update.message.reply_text(
            f"🛒 *Pedido Web Detectado*\n\n"
            f"He leído tu resumen:\n👉 *{pedido_final}*\n\n"
            f"💰 *Total a pagar: ${precio_total:.2f}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 🧠 LEER INTENCIONES PRIMERO (Antes de interpretar pedido)
    # --------------------------------------------------------
    best_intent = None
    best_score = 0
    
    for intent_name, phrases in INTENTS.items():
        match = process.extractOne(texto_usuario, phrases, scorer=fuzz.partial_ratio)
        if match:
            score = match[1]
            if score > 85 and score > best_score:
                best_score = score
                best_intent = intent_name
    
    # Si hay una intención clara (ej: Saludo, Hambre, Ayuda) y NO parece un pedido explícito
    # (Un pedido suele ser más largo o tener palabras clave, pero por ahora priorizamos la charla corta)
    if best_intent:
        response = random.choice(RESPONSES.get(best_intent, RESPONSES["DEFAULT"]))
        await update.message.reply_text(response, parse_mode="Markdown")
        
        # 🚀 PROACTIVIDAD
        if best_intent in ["HAMBRE", "INDECISION"]:
             await update.message.reply_text("💡 _Un momento, déjame buscarte lo mejor del menú..._", parse_mode="Markdown")
             await recomendacion_hibrida(update, context)
        
        return

    # ✅ 2. Interpretar el pedido (Solo si no fue una charla)
    # ----------------------------------------------------
    # (Bloque Web Summary movido arriba)

    # ✅ 2. Interpretar el pedido (Solo si no fue una charla)
    # ----------------------------------------------------
    producto_base, cantidad_detectada, removidos, agregados, pedido_final = await interpretar_pedido(texto_usuario)

    # 🔄 LÓGICA DE CORRECCIÓN / CONTINUACIÓN
    # Si no se detectó un producto nuevo, pero ya había uno en el carrito...
    if not producto_base and "pedido_carrito" in context.user_data:
        pedido_anterior = context.user_data["pedido_carrito"]
        producto_base = pedido_anterior["producto_base"]
        
        # Determine whether to update quantity or keep previous
        if cantidad_detectada is not None:
             cantidad = cantidad_detectada # Update quantity
             await update.message.reply_text(f"🔢 Entendido, cambio la cantidad a {cantidad}.")
        else:
             cantidad = pedido_anterior.get("cantidad", 1) # Keep previous
        
        # Re-interpretamos buscando solo ingredientes para ESTE producto
        ingredientes_menu = await obtener_ingredientes_producto(producto_base)
        nuevos_removidos = extraer_ingredientes_removidos(texto_usuario, ingredientes_menu)
        nuevos_agregados = extraer_ingredientes_agregados(texto_usuario, ingredientes_menu)
        
        # Si detectó cambios de ingredientes O cambio de cantidad
        if nuevos_removidos or nuevos_agregados or cantidad_detectada is not None:
             if nuevos_removidos or nuevos_agregados:
                 removidos = list(set(pedido_anterior["removidos"] + nuevos_removidos))
                 agregados = list(set(pedido_anterior["agregados"] + nuevos_agregados))
                 pedido_str = construir_pedido_final(producto_base, removidos, agregados)
                 await update.message.reply_text(f"👌 Entendido, corrijo tu orden: *{pedido_str}*")
             else:
                 # Si solo cambió la cantidad, mantenemos ingredientes previos
                 removidos = pedido_anterior["removidos"]
                 agregados = pedido_anterior["agregados"]
                 pedido_str = construir_pedido_final(producto_base, removidos, agregados)

             # Reconstruimos el string final con la cantidad
             if cantidad > 1:
                pedido_final = f"{cantidad} x {pedido_str}"
             else:
                pedido_final = pedido_str
        
        else:
             # Fallback original
             await update.message.reply_text(
                "🤔 Mmm, no estoy seguro de haberte entendido.\n\n"
                "Usa los formatos:\n"
                "1. 'quiero pedir [Plato]'\n"
                "2. '2 pizzas con jamón'\n"
                "3. 'hamburguesa sin tomate'\n\n"
                "O escribe *'Ayuda'* para más opciones.",
                parse_mode="Markdown"
            )
             return

    elif not producto_base:
        # Fallback original si no hay contexto
        await update.message.reply_text(
            "🤔 Mmm, no estoy seguro de haberte entendido.\n\n"
            "Usa los formatos:\n"
            "1. 'quiero pedir [Plato]'\n"
            "2. '2 pizzas con jamón'\n"
            "3. 'hamburguesa sin tomate'\n\n"
            "O escribe *'Ayuda'* para más opciones.",
            parse_mode="Markdown"
        )
        return

    # Si estamos aquí es porque tenemos un producto base (nuevo o recuperado del contexto)
    # Asegurar que ‘cantidad’ esté definida si vino de una orden nueva
    if 'cantidad' not in locals():
        cantidad = cantidad_detectada if cantidad_detectada is not None else 1

    # ✅ 1.5 Validar si el producto existe en el menú antes de pedir confirmación
    if not producto_es_valido(producto_base):
        await update.message.reply_text(
            text=f"❌ Lo siento, *{producto_base}* no está en el menú.",
            parse_mode="Markdown"
        )
        return

    # ✅ 2. Aplicar memoria personalizada
    recordatorio = await recordar_pedido_personalizado(telegram_id, producto_base)
    if recordatorio and cantidad_detectada is None: # Solo mostrar recordatorio si es orden nueva sin cantidad explícita (opcional)
        await update.message.reply_text(recordatorio)

    # ✅ 3. Obtener precio del producto y CALCULAR TOTAL
    producto_db = await sync_to_async(lambda: Product.objects.filter(name__iexact=producto_base).first())()
    precio_unitario = float(producto_db.price) if producto_db else 0.0
    precio_total = precio_unitario * cantidad

    # ✅ 4. Guardar datos interpretados para confirmación
    pedido_key = "pedido_carrito"

    context.user_data[pedido_key] = {
        "producto_base": producto_base,
        "cantidad": cantidad,
        "removidos": removidos,
        "agregados": agregados,
        "pedido_final": pedido_final,
        "texto_original": texto_usuario,
        "precio": precio_total  # Guardamos el total
    }

    # ✅ 4. Mostrar botones de confirmación inicial
    keyboard = [
        [
            InlineKeyboardButton(f"💸 Pagar ${precio_total:.2f}", callback_data=f"proceder_pago:{pedido_key}"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")
        ]
    ]

    await update.message.reply_text(
        f"{nombre}, ¿quieres proceder con tu pedido?\n\n"
        f"👉 *{pedido_final}*\n"
        f"💰 *Total: ${precio_total:.2f}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return
    



# ----------------------------------------------------
# ✅ VALIDAR PRODUCTO
# ----------------------------------------------------
def producto_es_valido(nombre_producto: str) -> bool:
    try:
        r = requests.get(PRODUCTOS_URL, timeout=5)
        productos_validos = r.json().get("productos", [])
        productos_validos = [p.strip().lower() for p in productos_validos]
    except:
        return False

    # Buscar si algún producto válido está contenido en el texto
    nombre_normalizado = nombre_producto.strip().lower()
    for producto in productos_validos:
        if producto in nombre_normalizado:
            return True

    return False

# ----------------------------------------------------
# ✅ CONFIRMAR PEDIDO (con memoria de ingredientes)
# ----------------------------------------------------

async def handle_confirmacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Guarda el pedido definitivamente en la DB (con el pago ya procesado) y notifica al admin
    """
    query = update.callback_query
    # await query.answer() # Ya se respondió en el manejador central

    telegram_id = query.from_user.id
    nombre = query.from_user.first_name

    pedido_key = query.data.replace("confirmar:", "").strip()
    data = context.user_data.pop(pedido_key, None)
    
    if data is None:
        await query.edit_message_text("⚠️ Error: No se encontró la información del pedido.")
        return

    pedido_final = data["pedido_final"]
    file_id = data.get("payment_receipt_file_id")
    payment_data = data.get("payment_data")

    # ✅ Guardar pedido FINAL en la base de datos
    try:
        order_data = {
            "telegram_id": telegram_id,
            "item": pedido_final,
            "status": "pendiente",
            "payment_status": "payment_submitted",
            "payment_receipt_file_id": file_id,
            "payment_data": payment_data
        }
        response = requests.post(ORDERS_URL, json=order_data, timeout=8)
        
        if response.status_code in (200, 201):
            order_id = response.json().get("id")
            
            # ✅ Notificar al cliente
            await query.edit_message_text(
                text=f"✅ *¡Pedido Enviado!*\\n\\n"
                     f"Tu pedido de **{pedido_final}** ha sido registrado.\\n"
                     f"⏳ Estamos verificando tu comprobante. Te avisaremos pronto.",
                parse_mode="Markdown"
            )

            # ✅ Notificar al administrador para aprobación
            datos_ocr = ""
            if payment_data and "error" not in payment_data:
                datos_ocr = "\\n📊 *Datos Extraídos:*\\n"
                for k, v in payment_data.items():
                    datos_ocr += f"• {k.replace('_',' ').title()}: {v}\\n"

            keyboard = [
                [
                    InlineKeyboardButton("✅ Aprobar Pago", callback_data=f"aprobar_pago:{order_id}"),
                    InlineKeyboardButton("❌ Rechazar Pago", callback_data=f"rechazar_pago:{order_id}")
                ]
            ]
            
            mensaje_admin = (
                f"💳 *NUEVO PEDIDO POR VERIFICAR*\\n\\n"
                f"👤 Cliente: {nombre} (ID: {telegram_id})\\n"
                f"🍽️ Pedido: {pedido_final}\\n"
                f"🆔 Order ID: {order_id}\\n"
                f"{datos_ocr}n"
                f"⏰ {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )

            # Enviar foto al admin
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=file_id,
                caption=mensaje_admin,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            # ✅ Guardar memoria personalizada opcionalmente
            try:
                payload_mem = {
                    "telegram_id": telegram_id,
                    "producto": data.get("producto_base"),
                    "removidos": data.get("removidos"),
                    "agregados": data.get("agregados"),
                    "pedido_final": pedido_final
                }
                requests.post("http://127.0.0.1:8000/bot/guardar_pedido_personalizado/", json=payload_mem, timeout=2)
            except: pass

        else:
            await query.edit_message_text(text="⚠️ No pude registrar tu pedido en el servidor. Intenta de nuevo.")
    except Exception as e:
        logging.error(f"Error finalizando orden: {e}")
        await query.edit_message_text(text="⚠️ Hubo un error procesando tu confirmación.")



# ----------------------------------------------------
# ✅ GUARDAR PEDIDO PERSONALIZADO EN BACKEND
# ----------------------------------------------------

async def recordar_pedido_personalizado(telegram_id, plato):
    ultimo = await sync_to_async(
        lambda: PedidoPersonalizado.objects.filter(
            telegram_id=telegram_id,
            producto=plato
        ).last()
    )()

    if not ultimo:
        return None

    removidos = ultimo.removidos or []
    agregados = ultimo.agregados or []

    return construir_pedido_final(plato, removidos, agregados)


# ----------------------------------------------------
# ✅ APLICAR MEMORIA PERSONALIZADA AL PEDIDO
# ----------------------------------------------------
async def aplicar_memoria_personalizada(telegram_id, plato):
    # ✅ Ejecutar ORM en modo seguro
    ultimo = await sync_to_async(
        lambda: PedidoPersonalizado.objects.filter(
            telegram_id=telegram_id,
            producto=plato
        ).last()
    )()

    if not ultimo:
        return plato

    removidos = ultimo.removidos or []
    agregados = ultimo.agregados or []

    return construir_pedido_final(plato, removidos, agregados)

# ----------------------------------------------------
# ✅ MANEJADOR CENTRAL DE CALLBACKS
# ----------------------------------------------------

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = query.from_user.id
    nombre = query.from_user.first_name

    await query.answer()

    # ----------------------------------------------------
    # ✅ 1. Proceder al pago (Mostrar info bancaria)
    # ----------------------------------------------------
    if query.data.startswith("proceder_pago:"):
        await handle_proceder_pago(update, context)
        return

    # ----------------------------------------------------
    # ✅ 1.5 Manejar Callback de Rating
    # ----------------------------------------------------
    if query.data.startswith("rating:"):
        await handle_rating_callback(update, context)
        return

    # ----------------------------------------------------
    # ✅ 1.6 Botones del Menú Principal (/start)
    # ----------------------------------------------------
    if query.data == "ayuda_pedido":
        await query.edit_message_text(
            "🍔 *Cómo hacer un pedido*\n\n"
            "Es muy fácil, solo escríbeme lo que quieres. Ejemplos:\n"
            "• _'Quiero una hamburguesa con queso'_\n"
            "• _'Dame una pizza y una coca cola'_\n"
            "• _'Quiero 2 perros calientes'_\n\n"
            "También puedes ver el /menu para inspirarte.",
            parse_mode="Markdown"
        )
        return

    if query.data == "estado_pedido":
        # Simulación o enlace a historial
        telegram_id = query.from_user.id
        await query.edit_message_text(
            f"📦 para ver tus pedidos recientes escribe /historial\n"
            f"Si acabas de pedir, tu orden está siendo procesada en cocina. 👨‍🍳"
        )
        return

    if query.data == "soporte":
        await soporte(update, context)
        return

    # ----------------------------------------------------
    # ✅ 2. Confirmar pedido (Guardar en DB)
    # ----------------------------------------------------
    if query.data.startswith("confirmar:"):
        await handle_confirmacion(update, context)
        return

    # ----------------------------------------------------
    # ✅ 2. Cancelar pedido
    # ----------------------------------------------------
    if query.data == "cancelar":
        await query.edit_message_text("❌ Pedido cancelado.")
        return

    # ----------------------------------------------------
    # ✅ 3. Registrar pedido desde recomendaciones
    # ----------------------------------------------------
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
        return

    # ----------------------------------------------------
    # ✅ 4. Rechazar recomendación
    # ----------------------------------------------------
    if query.data == "rechazar_recomendacion":
        await query.edit_message_text("👌 Entendido. No se agregaron recomendaciones adicionales.")
        return

    # ----------------------------------------------------
    # ✅ 5. Guardar gusto permanente (FASE 7)
    # ----------------------------------------------------
    if query.data.startswith("guardar_gusto:"):
        _, ingrediente, gusto = query.data.split(":")
        gusto = gusto == "True"

        pref, created = await sync_to_async(
            lambda: PreferenciaIngrediente.objects.get_or_create(
                telegram_id=telegram_id,
                ingrediente=ingrediente
            )
        )()
        pref.gusta = gusto
        pref.contador = 999
        await sync_to_async(pref.save)()

        await query.edit_message_text(
            f"✅ Perfecto {nombre}, lo recordaré para todos tus pedidos."
        )
        return

    # ----------------------------------------------------
    # ✅ 6. Rechazar gusto permanente
    # ----------------------------------------------------
    if query.data == "rechazar_gusto":
        await query.edit_message_text("👌 Entendido, no lo guardaré.")
        return

    # ----------------------------------------------------
    # ✅ 7. Aprobar/Rechazar Pago (ADMIN)
    # ----------------------------------------------------
    if query.data.startswith("aprobar_pago:"):
        await handle_payment_approval(update, context)
        return
    
    if query.data.startswith("rechazar_pago:"):
        await handle_payment_rejection(update, context)
        return

    # ----------------------------------------------------
    # ✅ 8. Dejar comentario
    # ----------------------------------------------------
    if query.data == "dejar_comentario":
        await query.edit_message_text(
            "📝 ¡Gracias por tu disposición! Por favor, deja tu comentario en el siguiente enlace:\n\n"
            "https://docs.google.com/forms/d/1AEZDZYcEI2081kemNSIcoIaBKWNh88oqhRsLfcfcWr0/edit"
        )
        return

    # ----------------------------------------------------
    # ✅ 8. No dejar comentario
    # ----------------------------------------------------
    if query.data == "no_comentario":
        await query.edit_message_text(
            f"👌 ¡Perfecto {nombre}! Gracias por tu pedido. ¡Que lo disfrutes! 🍽️"
        )
        return


# ----------------------------------------------------
# ✅ EXTRAER PRODUCTO BASE CON RAPIDFUZZ
#----------------------------------------------------

def extraer_producto_base(texto_usuario: str) -> str | None:
    try:
        r = requests.get(PRODUCTOS_URL, timeout=5)
        r.raise_for_status()  # Lanza excepción si hay error HTTP
        productos = r.json().get("productos", [])
        productos = [p.strip().lower() for p in productos]
        
        print(f"\n===== DEBUG extraer_producto_base =====")
        print(f"URL consultada: {PRODUCTOS_URL}")
        print(f"Productos obtenidos del backend: {productos}")
        print(f"Total de productos: {len(productos)}")
        
    except Exception as e:
        print(f"ERROR al obtener productos del backend: {e}")
        return None

    if not productos:
        print("⚠️ No hay productos en la base de datos")
        return None

    texto = texto_usuario.lower()
    print(f"Texto del usuario (normalizado): '{texto}'")

    # Buscar coincidencia difusa
    try:
        result = process.extractOne(
            texto,
            productos,
            scorer=fuzz.token_set_ratio
        )
        
        # Manejar caso donde no hay coincidencias
        if result is None:
            print("❌ No se encontró ninguna coincidencia")
            print("========================================\n")
            return None
        
        mejor_match, score, _ = result
        
        print(f"Mejor coincidencia: '{mejor_match}' con score: {score}")
        print(f"Umbral mínimo: 70")
        
    except Exception as e:
        print(f"ERROR en fuzzy matching: {e}")
        return None

    # Umbral mínimo para aceptar (70 funciona muy bien)
    if score >= 70:
        print(f"✅ Producto detectado: '{mejor_match}'")
        print("========================================\n")
        return mejor_match
    else:
        print(f"❌ Score {score} es menor que el umbral 70")
        print("========================================\n")

    return None




# ----------------------------------------------------
# ✅ MOSTRAR INFORMACIÓN DE PAGO
# ----------------------------------------------------
async def handle_proceder_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    nombre = query.from_user.first_name
    telegram_id = query.from_user.id
    
    pedido_key = query.data.replace("proceder_pago:", "").strip()
    data = context.user_data.get(pedido_key)
    
    if data is None:
        await query.edit_message_text("⚠️ Error: El pedido no se encontró o expiró.")
        return

    # Crear orden "pendiente" en el backend (USANDO CAMPOS CORRECTOS: telegram_id, status)
    async with aiohttp.ClientSession() as session:
        payload = {
            "telegram_id": telegram_id,
            "item": data["pedido_final"],
            "precio": data.get("precio", 0.0),
            "status": "pendiente"
        }
        try:
            # ORDERS_URL suele no tener barra final en la definición, pero Django la requiere
            url = ORDERS_URL if ORDERS_URL.endswith("/") else f"{ORDERS_URL}/"
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 201):
                    response_data = await resp.json()
                    order_id = response_data.get("id")  # El backend usa "id", no "order_id"
                    
                    # Guardar datos en user_data para el siguiente paso (foto)
                    context.user_data["pending_order_id"] = order_id
                    context.user_data["pending_order_item"] = data["pedido_final"]
                    context.user_data["current_pedido_key"] = pedido_key
                else:
                    error_text = await resp.text()
                    logging.error(f"Error backend post: {resp.status} - {error_text}")
                    await query.edit_message_text("⚠️ Error al crear la orden en el servidor.")
                    return
        except Exception as e:
            logging.error(f"Error de conexión: {e}")
            await query.edit_message_text(f"⚠️ Error de conexión al crear la orden.")
            return

    mensaje_pago = (
        f"💳 *Información de Pago*\n"
        f"Para procesar tu pedido de **{data['pedido_final']}**, por favor realiza el pago:\n\n"
        f"• Banco: BANCO BANESCO (0134)\n"
        f"• Titular: Restaurante Los Cuatros Sabores\n"
        f"• Cédula: V26989747\n"
        f"• Teléfono: 04241869450\n"
        f"• El monto a pagar es de $**{data['precio']}** por el pedido de **{data['pedido_final']}**\n\n"
        
        f"📸 *Instrucción:*\n\n"

        f"Una vez realizado el pago, envía la **foto del comprobante** por aquí mismo."
    )
    
    await query.edit_message_text(text=mensaje_pago, parse_mode="Markdown")


# ----------------------------------------------------
# ✅ MANEJAR COMPROBANTE DE PAGO (FOTO)
# ----------------------------------------------------
async def handle_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe el comprobante de pago del cliente, lo analiza con Gemini y lo envía al admin
    """
    telegram_id = update.effective_user.id
    nombre = update.effective_user.first_name
    
    # Verificar que tenemos datos guardados
    order_id = context.user_data.get("pending_order_id")
    pedido_item = context.user_data.get("pending_order_item")
    pedido_key = context.user_data.get("current_pedido_key")
    data = context.user_data.get(pedido_key) if pedido_key else None

    if not order_id or not pedido_item:
        await update.message.reply_text(
            "⚠️ No tienes ningún pedido pendiente de pago.\n"
            "Primero realiza un pedido usando /menu"
        )
        return

    # Obtener la foto o documento
    if update.message.photo:
        photo = update.message.photo[-1]  # La foto de mayor resolución
        file_id = photo.file_id
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("⚠️ Por favor envía una foto clara del comprobante de pago.")
        return
    
    try:
        # Descargar el archivo para OCR
        file = await context.bot.get_file(file_id)
        file_path = f"comprobante_{telegram_id}_{order_id}.jpg"
        await file.download_to_drive(file_path)
        
        # Extraer datos del comprobante con OCR
        await update.message.reply_text("🔍 Analizando tu comprobante con IA...")
        payment_data = await extraer_datos_comprobante(file_path)
        
        # Actualizar la orden en el backend (PATCH)
        async with aiohttp.ClientSession() as session:
            update_data = {
                "payment_receipt_file_id": file_id,
                "payment_status": "payment_submitted",
                "payment_data": payment_data
            }
            
            # Asegurar URL correcta con barra final
            url = f"{ORDERS_URL}{order_id}/" if ORDERS_URL.endswith("/") else f"{ORDERS_URL}/{order_id}/"
            
            try:
                async with session.patch(url, json=update_data) as resp:
                    if resp.status in (200, 204):
                        # Limpiar datos temporales
                        context.user_data.pop("pending_order_id", None)
                        context.user_data.pop("pending_order_item", None)
                        
                        # Confirmar al cliente
                        await update.message.reply_text(
                            f"✅ {nombre}, hemos recibido tu comprobante.\n\n"
                            f"⏳ Estamos verificando tu pago. Te notificaremos pronto."
                        )
                        
                        # Preparar datos extraídos para el admin
                        datos_extraidos = ""
                        if payment_data and "error" not in payment_data:
                            datos_extraidos = "\n📊 *Datos Extraídos:* \n"
                            for key, value in payment_data.items():
                                key_es = key.replace("_", " ").title()
                                datos_extraidos += f"• {key_es}: {value}\n"
                        
                        # Teclado para el admin
                        keyboard = [
                            [
                                InlineKeyboardButton("✅ Aprobar Pago", callback_data=f"aprobar_pago:{order_id}"),
                                InlineKeyboardButton("❌ Rechazar Pago", callback_data=f"rechazar_pago:{order_id}")
                            ]
                        ]
                        
                        mensaje_admin = (
                            f"💳 *NUEVO COMPROBANTE DE PAGO*\n\n"
                            f"👤 Cliente: {nombre} (ID: {telegram_id})\n"
                            f"🍽️ Pedido: {pedido_item}\n"
                            f"🆔 Order ID: {order_id}\n"
                            f"💰 Precio: ${data['precio']}\n"
                            f"{datos_extraidos}\n"
                            f"⏰ {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
                        )
                        
                        # Enviar al admin
                        await context.bot.send_photo(
                            chat_id=ADMIN_CHAT_ID,
                            photo=file_id,
                            caption=mensaje_admin,
                            parse_mode="Markdown",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        
                        # Limpiar archivo temporal
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    else:
                        error_text = await resp.text()
                        logging.error(f"Error Actualizando Orden: {resp.status} - {error_text}")
                        await update.message.reply_text("⚠️ Error al procesar tu comprobante en el servidor.")
            except Exception as e:
                logging.error(f"Error de conexión PATCH: {e}")
                await update.message.reply_text("⚠️ Error de conexión al procesar el pago.")
                
    except Exception as e:
        logging.error(f"Error procesando comprobante: {e}")
        await update.message.reply_text("⚠️ Hubo un error inesperado al procesar tu comprobante.")


# ----------------------------------------------------
# ✅ APROBAR PAGO (ADMIN)
# ----------------------------------------------------
async def handle_payment_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    El admin aprueba el pago y el pedido se procesa
    """
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("aprobar_pago:", "")
    
    try:
        # Obtener información de la orden
        response = requests.get(f"{ORDERS_URL}{order_id}/", timeout=5)
        if response.status_code != 200:
            await query.edit_message_caption(caption="⚠️ No se pudo encontrar la orden.")
            return
        
        order_data = response.json()
        telegram_id = order_data.get("telegram_id")
        pedido_item = order_data.get("item")
        
        # Actualizar estado del pago
        update_data = {
            "payment_status": "payment_approved",
            "payment_verified_at": datetime.datetime.now().isoformat(),
            "payment_verified_by": query.from_user.id,
            "status": "confirmado"
        }
        
        requests.patch(f"{ORDERS_URL}{order_id}/", json=update_data, timeout=8)
        
        # Notificar al cliente
        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"✅ *¡Pago Aprobado!*\n\n"
                f"Tu pago ha sido verificado exitosamente.\n"
                f"Tu pedido está siendo preparado:\n\n"
                f"🍽️ {pedido_item}\n\n"
                f"💰 Precio: ${order_data.get('precio')}\n"
                f"Te notificaremos cuando esté listo."
            ),
            parse_mode="Markdown"
        )
        
        # Notificar al chef
        mensaje_chef = (
            f"👨‍🍳 *NUEVO PEDIDO CONFIRMADO*\n\n"
            f"✅ Pago verificado\n"
            f"🍽️ {pedido_item}\n\n"
            f"📲 Cliente ID: {telegram_id}\n"
            f"🕒 Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        await context.bot.send_message(chat_id=CHEF_CHAT_ID, text=mensaje_chef, parse_mode="Markdown")
        
        # Actualizar mensaje del admin
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n✅ *PAGO APROBADO* por {query.from_user.first_name}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logging.error(f"Error aprobando pago: {e}")
        await query.edit_message_caption(caption="⚠️ Error al aprobar el pago.")


# ----------------------------------------------------
# ✅ RECHAZAR PAGO (ADMIN)
# ----------------------------------------------------
async def handle_payment_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    El admin rechaza el pago y el pedido se cancela
    """
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("rechazar_pago:", "")
    
    try:
        # Obtener información de la orden
        response = requests.get(f"{ORDERS_URL}{order_id}/", timeout=5)
        if response.status_code != 200:
            await query.edit_message_caption(caption="⚠️ No se pudo encontrar la orden.")
            return
        
        order_data = response.json()
        telegram_id = order_data.get("telegram_id")
        pedido_item = order_data.get("item")
        
        # Actualizar estado del pago
        update_data = {
            "payment_status": "payment_rejected",
            "payment_verified_at": datetime.datetime.now().isoformat(),
            "payment_verified_by": query.from_user.id,
            "status": "cancelado"
        }
        
        requests.patch(f"{ORDERS_URL}{order_id}/", json=update_data, timeout=8)
        
        # Notificar al cliente
        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"❌ *Pago Rechazado*\n\n"
                f"Lo sentimos, tu comprobante de pago no pudo ser verificado.\n\n"
                f"Por favor, verifica la información y envía un nuevo comprobante válido.\n"
                f"Si tienes dudas, contacta a /soporte \n\n"
                f"*Recuarda esto es una version de prueba y puede a estar propensa a tener errores* Agradecemos su paciencia*"
            ),
            parse_mode="Markdown"
        )
        
        # Actualizar mensaje del admin
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n❌ *PAGO RECHAZADO* por {query.from_user.first_name}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logging.error(f"Error rechazando pago: {e}")
        await query.edit_message_caption(caption="⚠️ Error al rechazar el pago.")


# ----------------------------------------------------
# 🚀 MAIN
# ----------------------------------------------------
def main():
    print("Bot Cliente corriendo y atendiendo órdenes...")
    app = ApplicationBuilder().token(BOT_TOKEN_CLIENTE).build()
    app.job_queue.scheduler.configure(timezone=pytz.UTC)

    

    # ✅ Comandos principales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("menu_personalizado", menu_personalizado))
    app.add_handler(CommandHandler("recomendacion", recomendaciones))
    app.add_handler(CommandHandler("recomendacion_similar", recomendacion_similar))
    app.add_handler(CommandHandler("recomendacion_hibrida", recomendacion_hibrida))
    app.add_handler(CommandHandler("soporte", soporte))
    
    # ✅ Rating con emoji (mantener para compatibilidad)
    app.add_handler(MessageHandler(filters.Regex("^⭐"), guardar_rating))
    
    # ✅ Handler para comprobantes de pago (fotos y documentos)
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_payment_receipt))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CallbackQueryHandler(handle_callback_query))

    app.run_polling()

if __name__ == "__main__":
    main()
