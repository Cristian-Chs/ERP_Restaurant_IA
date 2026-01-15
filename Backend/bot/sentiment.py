from groq import Groq
import os

def analizar_sentimiento_groq(comentario):
    """
    Analiza el sentimiento de un comentario usando Groq (Llama 3.3).
    Retorna: 'Positivo', 'Neutral' o 'Negativo'.
    """
    if not comentario or len(comentario.strip()) < 3:
        return "Neutral"

    api_key = os.environ.get("GROQ_API_KEY", "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") # Fallback key from context if env missing
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
        print(f"Error analizando sentimiento: {e}")
        return "Neutral"
