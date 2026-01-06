# Instrucciones para Probar el Chatbot Híbrido con Gemini

## 🚀 Pasos para Ejecutar

### 1. Configurar API Key

Abre el archivo `Backend/scripts/test_chatbot_gemini.py` y en la línea 18 reemplaza:

```python
GEMINI_API_KEY = "AIzaSyDXdW3T0oG_-yyZvmot2kt9k_oPukKaQ3A"  # ← Coloca tu key aquí
```

Con tu API key de Gemini 2.5 Flash.

### 2. Ejecutar el Script

```bash
cd Backend
..\.venv\Scripts\python.exe scripts\test_chatbot_gemini.py
```

### 3. Seleccionar Modo de Prueba

El script te preguntará:

- **Modo 1 (Interactivo)**: Escribe tus propias preguntas
- **Modo 2 (Automático)**: Ejecuta 14 preguntas de prueba predefinidas

## 📝 Ejemplos de Preguntas para Probar

### Preguntas que usa INTENTS (Sistema Actual)

- "Hola"
- "Tengo hambre"
- "No sé qué pedir"
- "Gracias"
- "Ayuda"

### Preguntas que usa GEMINI (IA)

- "¿Cuál es el horario?"
- "¿Tienen opciones vegetarianas?"
- "¿Cuánto cuesta una hamburguesa?"
- "¿Hacen delivery?"
- "¿Dónde están ubicados?"
- "¿Tienen WiFi?"
- "¿Cuánto costarían 3 pizzas para delivery?"
- "¿Tienen opciones sin gluten?"

## 🎯 Qué Observar

El bot te indicará la fuente de cada respuesta:

- `🤖 Bot [Intents]:` = Usó el sistema de reglas actual
- `🤖 Bot [Gemini AI]:` = Usó inteligencia artificial

## 💡 Ventajas del Sistema Híbrido

1. **Rápido**: Preguntas comunes usan intents (instantáneo)
2. **Inteligente**: Preguntas nuevas usan Gemini (1-2 segundos)
3. **Económico**: Solo paga API cuando es necesario
4. **Escalable**: No necesitas programar cada pregunta nueva

## 🔧 Personalización

Puedes modificar la información del restaurante en la función `chatbot_gemini()`:

- Horario
- Ubicación
- Servicios
- Métodos de pago
- etc.

## 📊 Costo Estimado

Con Gemini 2.5 Flash:

- ~$0.001 por cada 1000 tokens
- Una conversación promedio: ~500 tokens
- 1000 conversaciones/mes ≈ $0.50 USD
- Muy económico para empezar

## ⚠️ Notas Importantes

1. El script requiere que Django esté configurado (usa tus modelos)
2. Necesitas tener productos en la base de datos para que el menú funcione
3. La primera vez puede tardar un poco en cargar Django

## 🎉 Próximos Pasos

Si el prototipo funciona bien:

1. Integrar en `bot_cliente.py`
2. Agregar más contexto al prompt de Gemini
3. Implementar caché para respuestas frecuentes
4. Agregar logging de conversaciones
