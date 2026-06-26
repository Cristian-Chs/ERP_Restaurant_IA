import logging
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)

def analizar_sentimiento_groq(comentario):
    if not comentario or len(comentario.strip()) < 3:
        return "Neutral"

    api_key = settings.GROQ_API_KEY
    if not api_key:
        logger.warning("GROQ_API_KEY no configurada, usando fallback Neutral")
        return "Neutral"
    client = Groq(api_key=api_key)

    prompt = f"""
    Analiza el sentimiento del siguiente comentario de un cliente de un restaurante.
    Responde ÚNICAMENTE con una de estas tres palabras: Positivo, Neutral, Negativo.

    Comentario: "{comentario}"
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        resultado = completion.choices[0].message.content.strip().capitalize()

        if "Positivo" in resultado: return "Positivo"
        if "Negativo" in resultado: return "Negativo"
        return "Neutral"
    except Exception as e:
        logger.error(f"Error analizando sentimiento: {e}")
        return "Neutral"
