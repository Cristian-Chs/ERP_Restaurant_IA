import requests

TELEGRAM_API_URL = "https://api.telegram.org/bot8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU/sendMessage"
# 👆 Reemplaza TU_TOKEN_AQUI por el token real de tu bot

def notificar_pedido_listo(telegram_id, item):
    mensaje = f"✅ Tu pedido de: {item} ya está listo para retirar."
    requests.post(TELEGRAM_API_URL, json={
        "chat_id": telegram_id,
        "text": mensaje
    })
