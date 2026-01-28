"""
Proactive Messages Utility
Módulo para generar mensajes proactivos y variaciones conversacionales.
"""
import random
from datetime import datetime
import pytz

# ==============================================================================
# VARIACIONES DE MENSAJES
# ==============================================================================

GREETINGS = [
    "¡Hola {nombre}! 👋 ¿Qué tal todo hoy? ¿Tienes hambre?",
    "¡Bienvenido {nombre}! 😊 Me alegra verte. ¿Listo para pedir algo delicioso?",
    "¡Hola {nombre}! �️ ¿En qué puedo ayudarte hoy? ¿El menú o vas directo al grano?",
    "¡Epa {nombre}! 👋 ¿Qué se te antoja hoy? Estoy aquí para tomar tu orden.",
    "¡Hola {nombre}! 😊 Espero que estés teniendo un gran día. ¿Te provoca comer algo rico?"
]

MENU_FOLLOWUPS = [
    "¿Algo te llamó la atención del menú? 👀",
    "¿Qué se te antoja de todo esto? 🤔",
    "¿Ya sabes qué vas a pedir o quieres una recomendación? 😊",
    "Todo se ve rico, ¿verdad? 😋 ¿Por cuál te decides hoy?",
    "¿Viste algo que te guste? Cuéntame y tomamos nota. 📝"
]

ORDER_CONFIRMATION_QUESTIONS = [
    "¿Así está perfecto o quieres modificar algo? ✨",
    "¿Le agregamos algo más a tu pedido? 🤔",
    "¿Eso es todo o te provoca algo más para acompañar? 😊",
    "¡Anotado! ✅ ¿Te falta algo más o cerramos la cuenta?",
    "¿Listo o quieres agregar algún postre o bebida? 🥤🍰"
]

DELIVERY_OPTIONS = [
    "¡Excelente! 🚀 ¿Cómo prefieres recibir tu pedido: Delivery 🛵, Para Llevar 🛍️ o Comer Aquí 🍽️?",
    "¡Listo! Ahora cuéntame, ¿te lo enviamos (Delivery), pasas buscando (Pick Up) o comes acá?",
    "¡Entendido! ✅ ¿Cuál será el método de entrega: Delivery, Pick Up o Comer en el local?",
]

UNKNOWN_INTENT_RESPONSES = [
    "Mmm, no estoy seguro de haberte entendido �. ¿Podrías decirlo de otra forma?",
    "Disculpa, me perdí un poco 😅. ¿Me repites eso?",
    "Creo que no te entendí bien. ¿Te refieres a algo del menú?",
    "Ups, mis circuitos se cruzaron 🤖. ¿Qué tratabas de decirme?",
]

# ==============================================================================
# FUNCIONES HELPER
# ==============================================================================

def get_time_based_greeting(nombre: str) -> str:
    """Devuelve un saludo basado en la hora del día + variaciones."""
    tz = pytz.timezone('America/Caracas') # Ajustar zona horaria si es necesario
    now = datetime.now(tz)
    hour = now.hour
    
    base_greeting = ""
    if 5 <= hour < 12:
        base_greeting = "¡Buenos días"
    elif 12 <= hour < 19:
        base_greeting = "¡Buenas tardes"
    else:
        base_greeting = "¡Buenas noches"
        
    # Mezclar con mensajes proactivos
    variations = [
        f"{base_greeting} {nombre}! ☀️ ¿Listo para desayunar/almorzar algo rico?",
        f"{base_greeting} {nombre}! 👋 ¿Qué tal si comemos algo delicioso?",
        f"{base_greeting} {nombre}! 😊 ¿En qué puedo servirte hoy?",
        f"{base_greeting} {nombre}! 🍽️ ¿Tienes hambre? ¡Yo también (si pudiera comer)!",
    ]
    
    return random.choice(variations)

def get_random_message(message_list: list, **kwargs) -> str:
    """Selecciona un mensaje aleatorio y formatea si es necesario."""
    msg = random.choice(message_list)
    if kwargs:
        return msg.format(**kwargs)
    return msg

def get_suggestive_question(context: dict = None) -> str:
    """Genera una pregunta sugestiva basada en el contexto (opcional)."""
    suggestions = [
        "¿Te provoca una hamburguesa hoy? 🍔 Son nuestras favoritas.",
        "¿Has probado nuestras pizzas? 🍕 Están recién salidas del horno.",
        "Si tienes sed, nuestros batidos son increíbles. 🥤",
        "¿Qué tal un postre para alegrar el día? 🍰",
    ]
    return random.choice(suggestions)

def get_proactive_followup(last_action: str) -> str:
    """
    Devuelve una pregunta de seguimiento basada en la última acción del usuario.
    Esto es clave para mantener la iniciativa.
    """
    if last_action == "view_menu":
        return get_random_message(MENU_FOLLOWUPS)
    elif last_action == "add_item":
        return get_random_message(ORDER_CONFIRMATION_QUESTIONS)
    elif last_action == "greeting":
        return get_suggestive_question()
    
    return "¿En qué más puedo ayudarte? 😊"
