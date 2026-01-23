#!/usr/bin/env bash
# start_services.sh

# 1. Iniciar el Bot de Telegram en segundo plano (&)
echo "🤖 Starting Telegram Bot..."
python bot_Cliente/main.py &

# Esperar unos segundos para no estresar la CPU/RAM al inicio
sleep 5

# 2. Iniciar Gunicorn (Servidor Web) en primer plano
# Optimizamos procesos para no exceder los 512MB de Koyeb
echo "🚀 Starting Django Gunicorn..."
gunicorn backend.wsgi:application \
    --workers 2 \
    --threads 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --bind 0.0.0.0:$PORT
