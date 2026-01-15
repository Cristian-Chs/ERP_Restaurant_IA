"""
Bot Cliente - Configuración Central
Todas las constantes y configuraciones del bot en un solo lugar.
"""
import os
from dotenv import load_dotenv
from groq import Groq

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================
# TOKENS Y CREDENCIALES
# ============================================================
BOT_TOKEN_CLIENTE = os.getenv("BOT_TOKEN_CLIENTE")
if not BOT_TOKEN_CLIENTE:
    raise ValueError("❌ BOT_TOKEN_CLIENTE no configurado en variables de entorno")

CHEF_CHAT_ID = int(os.getenv("CHEF_CHAT_ID", "0"))
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# ============================================================
# API KEYS
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY no configurado en variables de entorno")

OCR_API_KEY = os.getenv("OCR_API_KEY")
if not OCR_API_KEY:
    raise ValueError("❌ OCR_API_KEY no configurado en variables de entorno")

# ============================================================
# BACKEND URLs
# ============================================================
BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api")

ORDERS_URL = f"{BASE_URL}/bot/orders/"
GUSTOS_URL = f"{BASE_URL}/bot/gustos/"
HISTORIAL_URL = f"{BASE_URL}/bot/historial/"
POPULARIDAD_URL = f"{BASE_URL}/bot/popularidad/"
RATING_URL = f"{BASE_URL}/bot/rating/"
SIMILAR_URL = f"{BASE_URL}/bot/recomendacion_similar/"
HIBRIDA_URL = f"{BASE_URL}/bot/recomendacion_hibrida/"
PRODUCTOS_URL = f"{BASE_URL}/bot/productos/"
RECOMENDACION_URL = f"{BASE_URL}/bot/recomendacion/"
CURRENCY_RATES_URL = f"{BASE_URL}/currency/rates/"

# Session URLs
SESSION_URL = f"{BASE_URL}/bot/session/"
SESSION_UPDATE_URL = f"{BASE_URL}/bot/session/update/"
SESSION_RESET_URL = f"{BASE_URL}/bot/session/reset/"

# ============================================================
# OCR CONFIGURATION
# ============================================================
OCR_API_URL = "https://api.ocr.space/parse/image"

BANCOS = [
    "BANESCO", "BOD", "MERCANTIL", "PROVINCIAL", "BNC", "VENEZUELA",
    "BANCARIBE", "BANCO DEL TESORO", "BANCO PLAZA"
]

# ============================================================
# KEYWORDS PARA PROCESAMIENTO DE TEXTO
# ============================================================
INGREDIENTES_REMOVIDOS_KEYWORDS = [
    "sin", "no lleva", "quita", "quitar", "no quiero", "sin nada de"
]

INGREDIENTES_AGREGADOS_KEYWORDS = [
    "con", "agrega", "añade", "extra", "ponle", "más"
]

# ============================================================
# GROQ CLIENT
# ============================================================
groq_client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# DEFAULTS
# ============================================================
DEFAULT_EXCHANGE_RATE = 35.0  # Fallback para VES
