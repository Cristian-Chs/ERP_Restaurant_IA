#!/usr/bin/env bash
# start_services.sh

# 1. Iniciar el Bot de Telegram en segundo plano (&)
echo "🤖 Starting Telegram Bot..."
python bot_Cliente/main.py &

# 2. Iniciar Gunicorn (Servidor Web) en primer plano
# Gunicorn mantendrá el contenedor vivo
echo "🚀 Starting Django Gunicorn..."
gunicorn backend.wsgi:application
