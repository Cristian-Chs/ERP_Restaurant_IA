"""
PROTOTIPO: Chatbot Híbrido con Groq (Llama 3.3 70B)
Combina el sistema de intents actual con IA ultra-rápida como fallback

VENTAJAS DE GROQ:
- 14,400 requests gratis por día (vs. 50 de Gemini)
- Respuestas en 0.3-0.8 segundos (vs. 1-3 seg de Gemini)
- API compatible con OpenAI (fácil de usar)

INSTRUCCIONES:
1. Obtén tu API key gratis en: https://console.groq.com/keys
2. Configura tu API key en la línea 24
3. Ejecuta: python test_chatbot_groq.py
"""

import os
import sys
import django
import time

# Configurar Django
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

#  CONFIGURACIÓN - COLOCA TU API KEY DE GROQ AQUÍ
GROQ_API_KEY = "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"  # ← Obtén tu key en https://console.groq.com/keys

from groq import Groq
from core.models import Product, Ingredient
from bot_Cliente.intents import INTENTS, RESPONSES
import random
import re

# Configurar cliente de Groq
client = Groq(api_key=GROQ_API_KEY)

# ----------------------------------------------------
#  SISTEMA DE INTENTS ACTUAL (del bot_cliente.py)
# ----------------------------------------------------

def detectar_intent(texto: str) -> str | None:
    """
    Detecta el intent usando el sistema actual de patrones.
    Retorna el nombre del intent o None si no encuentra coincidencia.
    """
    texto_lower = texto.lower()
    
    for intent_name, keywords in INTENTS.items():
        for keyword in keywords:
            if keyword in texto_lower:
                return intent_name
    
    return None

def responder_con_intent(intent_name: str) -> str:
    """
    Genera una respuesta basada en el intent detectado.
    """
    if intent_name in RESPONSES:
        return random.choice(RESPONSES[intent_name])
    return random.choice(RESPONSES["DEFAULT"])

# ----------------------------------------------------
#  CHATBOT CON GROQ (NUEVO)
# ----------------------------------------------------

def obtener_contexto_restaurante():
    """
    Obtiene información del restaurante desde la base de datos.
    """
    # Obtener productos activos
    productos = Product.objects.filter(is_active=True).values('name', 'price', 'category', 'description')
    
    # Organizar por categorías
    menu_por_categoria = {
        'entradas': [],
        'principales': [],
        'postres': [],
        'bebidas': [],
        'promociones': []
    }
    
    for producto in productos:
        categoria = producto['category']
        if categoria in menu_por_categoria:
            menu_por_categoria[categoria].append({
                'nombre': producto['name'],
                'precio': float(producto['price']),
                'descripcion': producto['description'] or ''
            })
    
    # Obtener ingredientes disponibles como extras
    ingredientes_extra = list(
        Ingredient.objects.filter(disponible_como_extra=True).values_list('nombre', flat=True)
    )
    
    return {
        'menu': menu_por_categoria,
        'ingredientes_extra': ingredientes_extra
    }

def chatbot_groq(pregunta_usuario: str) -> str:
    """
    Usa Groq (Llama 3.3 70B) para responder preguntas que el sistema de intents no entiende.
    """
    try:
        # Obtener contexto del restaurante
        contexto = obtener_contexto_restaurante()
        
        # Construir prompt con información del restaurante
        system_prompt = f"""Eres un asistente virtual amigable del restaurante "4 Sabores de Paraguaná".

INFORMACIÓN DEL RESTAURANTE:
- Nombre: 4 Sabores de Paraguaná
- Horario: Lunes a Domingo de 9:00 AM a 10:00 PM
- Ubicación: Calle Principal #123, Paraguaná, Falcón, Venezuela
- Servicios: Comer en local, Para llevar, Delivery
- Delivery: Disponible en un radio de 5km, costo $3.00
- Métodos de pago: Efectivo, Pago Móvil, Transferencia, Zelle
- WiFi: Sí, gratis para clientes
- Estacionamiento: Sí, 10 espacios disponibles

MENÚ ACTUAL:

Entradas:
{chr(10).join([f"- {p['nombre']}: ${p['precio']:.2f}" for p in contexto['menu']['entradas']]) if contexto['menu']['entradas'] else "- No hay entradas disponibles"}

Platos Principales:
{chr(10).join([f"- {p['nombre']}: ${p['precio']:.2f}" for p in contexto['menu']['principales']]) if contexto['menu']['principales'] else "- No hay platos principales disponibles"}

Postres:
{chr(10).join([f"- {p['nombre']}: ${p['precio']:.2f}" for p in contexto['menu']['postres']]) if contexto['menu']['postres'] else "- No hay postres disponibles"}

Bebidas:
{chr(10).join([f"- {p['nombre']}: ${p['precio']:.2f}" for p in contexto['menu']['bebidas']]) if contexto['menu']['bebidas'] else "- No hay bebidas disponibles"}

Promociones:
{chr(10).join([f"- {p['nombre']}: ${p['precio']:.2f}" for p in contexto['menu']['promociones']]) if contexto['menu']['promociones'] else "- No hay promociones disponibles"}

Ingredientes disponibles como extras:
{', '.join(contexto['ingredientes_extra']) if contexto['ingredientes_extra'] else 'No hay extras disponibles'}

INSTRUCCIONES:
1. Responde de forma amigable y conversacional en español
2. Usa emojis cuando sea apropiado 
3. Si te preguntan por precios, usa la información del menú
4. Si te preguntan por horarios, ubicación o servicios, usa la información proporcionada
5. Si te preguntan algo que no sabes, sé honesto y sugiere contactar al restaurante
6. Mantén las respuestas concisas (máximo 3-4 líneas)
7. Si mencionas productos, incluye el precio
"""
        
        # Llamar a Groq con streaming desactivado para simplicidad
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Modelo más potente y rápido
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pregunta_usuario}
            ],
            temperature=0.7,
            max_tokens=300,
            top_p=1,
            stream=False
        )
        
        return completion.choices[0].message.content.strip()
        
    except Exception as e:
        return f" Error al conectar con Groq: {str(e)}"

# ----------------------------------------------------
#  CHATBOT HÍBRIDO (Intents + Groq)
# ----------------------------------------------------

def chatbot_hibrido(pregunta_usuario: str) -> tuple[str, str]:
    """
    Intenta primero con intents, si no encuentra coincidencia usa Groq.
    Retorna: (respuesta, fuente)
    """
    # 1. Intentar con sistema de intents
    intent = detectar_intent(pregunta_usuario)
    
    if intent:
        respuesta = responder_con_intent(intent)
        return respuesta, "INTENTS"
    
    # 2. Si no encuentra intent, usar Groq
    respuesta = chatbot_groq(pregunta_usuario)
    return respuesta, "GROQ"

# ----------------------------------------------------
#  MODO INTERACTIVO DE PRUEBA
# ----------------------------------------------------

def test_interactivo():
    """
    Modo interactivo para probar el chatbot.
    """
    print("=" * 60)
    print(" PROTOTIPO: Chatbot Híbrido (Intents + Groq Llama 3.3)")
    print("=" * 60)
    print()
    print("Escribe tus preguntas para probar el bot.")
    print("Escribe 'salir' para terminar.")
    print()
    print("-" * 60)
    print()
    
    while True:
        try:
            pregunta = input(" Tú: ").strip()
            
            if not pregunta:
                continue
            
            if pregunta.lower() in ['salir', 'exit', 'quit']:
                print("\n ¡Hasta luego!")
                break
            
            # Medir tiempo de respuesta
            inicio = time.time()
            respuesta, fuente = chatbot_hibrido(pregunta)
            tiempo = time.time() - inicio
            
            # Mostrar respuesta con indicador de fuente y tiempo
            if fuente == "INTENTS":
                print(f" Bot [Intents] ({tiempo:.2f}s): {respuesta}")
            else:
                print(f" Bot [Groq AI] ({tiempo:.2f}s): {respuesta}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n Error: {e}\n")

# ----------------------------------------------------
#  MODO DE PRUEBAS AUTOMÁTICAS
# ----------------------------------------------------

def test_automatico():
    """
    Ejecuta una serie de preguntas de prueba.
    """
    print("=" * 60)
    print(" PRUEBAS AUTOMÁTICAS")
    print("=" * 60)
    print()
    
    preguntas_prueba = [
        # Preguntas que DEBEN funcionar con intents
        "Hola",
        "Tengo hambre",
        "No sé qué pedir",
        "Gracias",
        
        # Preguntas que DEBEN usar Groq (no están en intents)
        "¿Cuál es el horario del restaurante?",
        "¿Tienen opciones vegetarianas?",
        "¿Cuánto cuesta una hamburguesa?",
        "¿Hacen delivery?",
        "¿Dónde están ubicados?",
        "¿Tienen WiFi?",
        "¿Puedo pagar con tarjeta?",
        "¿Cuánto costarían 3 pizzas para delivery?",
        "¿Tienen opciones sin gluten?",
        "¿Cuál es el plato más barato?"
    ]
    
    tiempos_groq = []
    
    for i, pregunta in enumerate(preguntas_prueba, 1):
        print(f"{i}.  Pregunta: {pregunta}")
        
        inicio = time.time()
        respuesta, fuente = chatbot_hibrido(pregunta)
        tiempo = time.time() - inicio
        
        if fuente == "INTENTS":
            print(f"    [Intents] ({tiempo:.2f}s): {respuesta}")
        else:
            print(f"    [Groq AI] ({tiempo:.2f}s): {respuesta}")
            tiempos_groq.append(tiempo)
        
        print()
        
        # Pequeña pausa entre requests (opcional con Groq, tiene límites muy altos)
        if i < len(preguntas_prueba):
            time.sleep(0.5)
    
    # Estadísticas
    if tiempos_groq:
        print("=" * 60)
        print(" ESTADÍSTICAS DE GROQ")
        print("=" * 60)
        print(f"Requests a Groq: {len(tiempos_groq)}")
        print(f"Tiempo promedio: {sum(tiempos_groq)/len(tiempos_groq):.2f}s")
        print(f"Tiempo más rápido: {min(tiempos_groq):.2f}s")
        print(f"Tiempo más lento: {max(tiempos_groq):.2f}s")

# ----------------------------------------------------
#  MAIN
# ----------------------------------------------------

if __name__ == "__main__":
    print()
    print("Selecciona el modo de prueba:")
    print("1. Interactivo (escribe tus propias preguntas)")
    print("2. Automático (ejecuta preguntas de prueba)")
    print()
    
    modo = input("Elige (1 o 2): ").strip()
    
    print()
    
    if modo == "1":
        test_interactivo()
    elif modo == "2":
        test_automatico()
    else:
        print(" Opción inválida. Ejecutando modo interactivo por defecto.")
        print()
        test_interactivo()
