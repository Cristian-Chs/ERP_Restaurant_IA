# intents.py
# 🧠 Cerebro del Mesero Digital
# Aquí puedes expandir las frases que el bot entiende y cómo responde.

INTENTS = {
    "SALUDO": [
        "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", 
        "que tal", "estás ahí", "holis", "hello", "hey"
    ],
    "DESPEDIDA": [
        "chao", "adiós", "hasta luego", "bye", "nos vemos", "gracias", "muchas gracias"
    ],
    "HAMBRE": [
        "tengo hambre", "que hambre", "muero de hambre", "tengo un hueco en el estomago",
        "quiero comer algo", "alimentame", "que hay de comer", "tengo apetito",
        "me gustaria ordenar algo rico", "quiero pedir algo"
    ],
    "INDECISION": [
        "no se que pedir", "que me recomiendas", "que hay bueno", "que es lo mas rico",
        "sorprendeme", "recomendacion", "sugerencia", "cual es la especialidad",
        "quiero probar algo nuevo", "probar algo nuevo", "algo diferente", "que recomiendas hoy"
    ],
    "AGRADECIMIENTO": [
        "gracias", "te lo agradezco", "excelente servicio", "muy amable", "gracias chamo", "fino"
    ],
    "AYUDA": [
        "ayuda", "socorro", "como funciona", "no entiendo", "que hago", "como pido"
    ],
    "PAGO_MOVIL": [
        "pago movil", "datos de pago", "transferencia", "numero de cuenta", 
        "a donde pago", "tienes pago movil", "cuenta bancaria", "datos bancarios",
        "zelle", "binance", "metodos de pago"
    ]
}

RESPONSES = {
    "SALUDO": [
        "¡Hola! 👋 Bienvenido a 4 Sabores. ¿Listo para comer algo delicioso?",
        "¡Buenas! 👨‍🍳 La cocina está a tope hoy. ¿Qué se te antoja?",
        "¡Hola! Soy tu mesero digital. ¿Te traigo la carta o buscas algo específico?",
        "¡Bienvenido! ¿Vienes por tu plato favorito o quieres probar algo nuevo?"
    ],
    "DESPEDIDA": [
        "¡Hasta luego! 👋 Esperamos verte pronto.",
        "¡Que tengas buen día! Aquí estaremos cuando te de hambre otra vez. 🍔",
        "¡Chao! Gracias por visitarnos."
    ],
    "HAMBRE": [
        "¡Has llegado al lugar indicado! 😋 ¿Te provoca algo clásico o una especialidad?",
        "¡No se diga más! Vamos a solucionar ese problema de inmediato. 🍔🍕",
        "¡A la orden! 👨‍🍳 ¿Qué tipo de comida te apetece hoy?",
        "Aquí estamos para consentirte. Revisa el /menu o pídeme una sugerencia."
    ],
    "INDECISION": [
        "Mmm... 🤔 Si buscas algo infalible, la **Hamburguesa 4 Sabores** nunca falla.",
        "¿Te gustan las sorpresas? Nuestros clientes aman la **Pizza Especial**. 🍕",
        "¡Déjame pensar! Hoy el chef está recomendando mucho los **Tequeños**. ¿Te animas?",
        "Si fuera tú, pediría una **Parrilla Mixta**. ¡Es una joya! 🥩",
        "¡Me encanta la gente aventurera! 🤠 Si quieres probar algo nuevo, tienes que darle una oportunidad al **Pepito Gratinado**."
    ],
    "AGRADECIMIENTO": [
        "¡Es un placer! 😊 Estamos para servirte.",
        "¡De nada! 👨‍🍳 ¡Vuelve pronto!",
        "¡A ti! Escribe si necesitas algo más. 🤜🤛"
    ],
    "AYUDA": [
        "Tranquilo, es como hablar con un amigo: 🗣️\nSimplemente dime qué quieres comer, por ejemplo: _'Quiero una hamburguesa con queso'_.",
        "Estoy aquí para ayudarte. Puedes escribir lo que te provoque o usar el comando /menu.",
        "¡Relájate! 🧘‍♂️ Escribe 'Tengo hambre' y te guiaré."
    ],
    "PAGO_MOVIL": [
        "💸 **Datos de Pago Móvil**\n\n🏦 **Banco**: Banesco\n📞 **Teléfono**: 0414-1234567\n🆔 **C.I.**: 12.345.678\n\n📲 Al realizar el pago, envíame una *foto del comprobante* para validarlo.",
        "Aquí tienes para transferir 👇\n\n🏦 **Banesco | Pago Móvil**\n📱 0414-1234567\n💳 V-12.345.678\n\n¡Espero tu comprobante! 📸"
    ],
    "DEFAULT": [
        "🤔 Mmm, no estoy seguro de haberte entendido.",
        "¡Vaya! Aún estoy aprendiendo humano. 😅 ¿Podrías decirlo de otra forma?",
        "Disculpa, mi oído de robot falló. 🤖 ¿Me repites eso?",
        "¿Podrías ser más específico? Quiero asegurarme de tomar bien tu nota. 📝"
    ]
}
