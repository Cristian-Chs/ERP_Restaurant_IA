"""
Main Entry Point
Punto de entrada limpio para el bot de Telegram.
"""
import sys
import os
import logging
import pytz

# Configurar Django
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    PicklePersistence,
)

# Importar configuración
from bot_Cliente.config import BOT_TOKEN_CLIENTE

# Importar handlers
from bot_Cliente.handlers.commands import start, menu, menu_personalizado, soporte

# TODO: Importar otros handlers cuando estén listos
from bot_Cliente.handlers.messages import handle_message
from bot_Cliente.handlers.callbacks import handle_callback_query
from bot_Cliente.handlers.payments import handle_payment_receipt
from bot_Cliente.services.recommendation_service import recomendacion_similar


logging.basicConfig(level=logging.INFO)


def main():
    """
    Función principal que inicializa y ejecuta el bot.
    """
    print("Bot Cliente corriendo y atendiendo órdenes...")
    
    # Configurar persistencia (archivo local en bot_Cliente/)
    persistence = PicklePersistence(filepath="./bot_state.pkl")

    # Crear aplicación
    app = ApplicationBuilder().token(BOT_TOKEN_CLIENTE).persistence(persistence).build()
    app.job_queue.scheduler.configure(timezone=pytz.UTC)

    # ============================================================
    # REGISTRAR HANDLERS
    # ============================================================
    
    # Comandos principales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("menu_personalizado", menu_personalizado))
    app.add_handler(CommandHandler("soporte", soporte))
    
    # TODO: Descomentar cuando se migren estos handlers
    # app.add_handler(CommandHandler("recomendacion", recomendaciones))
    app.add_handler(CommandHandler("recomendacion_similar", recomendacion_similar))
    # app.add_handler(CommandHandler("recomendacion_hibrida", recomendacion_hibrida))
    
    # Handlers de mensajes
    # TODO: Descomentar cuando se migren
    # app.add_handler(MessageHandler(filters.Regex("^"), guardar_rating))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_payment_receipt))
    # app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Iniciar bot
    app.run_polling()


if __name__ == "__main__":
    main()
