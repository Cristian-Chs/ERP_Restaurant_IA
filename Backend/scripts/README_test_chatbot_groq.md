# Instrucciones para Probar el Chatbot Híbrido con Groq

##  Por qué Groq es Mejor que Gemini

| Característica      | Gemini  | Groq               |
| ------------------- | ------- | ------------------ |
| Requests gratis/día | ~50     | **14,400**       |
| Velocidad           | 1-3 seg | **0.3-0.8 seg**  |
| Límite por minuto   | 2-15    | **30**             |
| Estabilidad         | Media   | **Alta**           |

##  Pasos para Ejecutar

### 1. Obtener API Key de Groq (GRATIS)

1. Ve a: https://console.groq.com/keys
2. Crea una cuenta (gratis)
3. Genera una API key
4. Copia la key

### 2. Configurar API Key

Abre `Backend/scripts/test_chatbot_groq.py` y en la línea 24 reemplaza:

```python
GROQ_API_KEY = "TU_API_KEY_DE_GROQ_AQUI"
```

Con tu API key de Groq.

### 3. Instalar Groq

```bash
pip install groq
```

### 4. Ejecutar el Script

```bash
cd Backend
..\.venv\Scripts\python.exe scripts\test_chatbot_groq.py
```

### 5. Seleccionar Modo de Prueba

- **Modo 1 (Interactivo)**: Escribe tus propias preguntas
- **Modo 2 (Automático)**: Ejecuta 14 preguntas de prueba predefinidas

##  Ventajas de Groq

1. **Cuota Generosa**: 14,400 requests gratis por día (vs. 50 de Gemini)
2. **Ultra Rápido**: Respuestas en 0.3-0.8 segundos (vs. 1-3 seg de Gemini)
3. **Modelo Potente**: Llama 3.3 70B (comparable a GPT-4)
4. **API Simple**: Compatible con OpenAI (fácil de usar)
5. **Sin Problemas de Cuota**: Casi imposible agotar el límite en pruebas

##  Modelos Disponibles en Groq

- `llama-3.3-70b-versatile`  (Recomendado - balance perfecto)
- `llama-3.1-70b-versatile` (Alternativa)
- `mixtral-8x7b-32768` (Más rápido, menos preciso)
- `gemma2-9b-it` (Muy rápido, menos potente)

##  Ejemplos de Uso

### Preguntas que usa INTENTS (instantáneo)

- "Hola"
- "Tengo hambre"
- "Gracias"

### Preguntas que usa GROQ (0.3-0.8 seg)

- "¿Cuál es el horario?"
- "¿Tienen opciones vegetarianas?"
- "¿Cuánto cuesta una hamburguesa?"
- "¿Cuánto costarían 3 pizzas para delivery?"

##  Personalización

Puedes modificar:

- **Modelo**: Cambiar `llama-3.3-70b-versatile` por otro modelo
- **Temperature**: Ajustar creatividad (0.0 = preciso, 1.0 = creativo)
- **Max tokens**: Limitar longitud de respuesta

##  Límites de Groq (Free Tier)

-  **14,400 requests por día**
-  **30 requests por minuto**
-  **6,000 tokens por minuto**

##  Notas

1. El script mide el tiempo de respuesta de cada pregunta
2. En modo automático, muestra estadísticas al final
3. Groq es MUCHO más estable que Gemini para pruebas

##  Resultado Esperado

Con Groq deberías ver respuestas como:

```
 Tú: ¿Cuál es el horario?
 Bot [Groq AI] (0.45s): ¡Hola!  Estamos abiertos de Lunes a Domingo
de 9:00 AM a 10:00 PM. ¿Te gustaría hacer un pedido? 
```

¡Mucho más rápido y sin problemas de cuota!
