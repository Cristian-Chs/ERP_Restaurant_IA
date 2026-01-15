#!/bin/bash

# ==============================================================================
# Script de Provisionamiento para 4 Sabores Backend
# Sistema Operativo Objetivo: Ubuntu 22.04 LTS / 24.04 LTS
# ==============================================================================

set -e  # Detener si hay error

echo "🚀 Iniciando configuración del servidor..."

# 1. Actualizar sistema
echo "📦 Actualizando paquetes del sistema..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Instalar dependencias del sistema
echo "📦 Instalando dependencias (Python, Postgres, Nginx, Git)..."
sudo apt-get install -y python3-pip python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl git

# 3. Crear base de datos y usuario de Postgres
# NOTA: Cambiar 'password' por una segura en producción
DB_NAME="telegram_bot_prod"
DB_USER="bot_user"
DB_PASS="CAMBIAR_ESTA_CONTRASEÑA"

echo "🐘 Configurando PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || echo "Base de datos ya existe"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" || echo "Usuario ya existe"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# 4. Clonar/Preparar directorio del proyecto
PROJECT_DIR="/var/www/reactpythonbackend"
REPO_URL="https://github.com/TU_USUARIO/TU_REPO.git" # CAMBIAR ESTO

echo "📂 Preparando directorio del proyecto en $PROJECT_DIR..."
# sudo mkdir -p $PROJECT_DIR
# sudo chown -R $USER:www-data $PROJECT_DIR
# git clone $REPO_URL $PROJECT_DIR  <-- Descomentar si se clona desde git

# 5. Configurar entorno virtual
echo "🐍 Configurando entorno virtual Python..."
# cd $PROJECT_DIR
# python3 -m venv .venv
# source .venv/bin/activate
# pip install -r Backend/requirements.txt
# pip install gunicorn

# 6. Copiar configuraciones
echo "⚙️ Copiando configuraciones de Nginx y Systemd..."
# sudo cp deployment/nginx/reactpythonbackend /etc/nginx/sites-available/
# sudo ln -s /etc/nginx/sites-available/reactpythonbackend /etc/nginx/sites-enabled/
# sudo cp deployment/systemd/gunicorn.service /etc/systemd/system/

# 7. Reiniciar servicios
echo "🔄 Reiniciando servicios..."
# sudo systemctl daemon-reload
# sudo systemctl start gunicorn
# sudo systemctl enable gunicorn
# sudo systemctl restart nginx

# 8. Firewall (UFW)
echo "🛡️ Configurando Firewall (UFW)..."
sudo ufw allow 'Nginx Full'
# sudo ufw enable

echo "✅ Configuración base terminada."
echo "⚠️  IMPORTANTE: Ahora debes subir tu código, configurar el .env y ejecutar las migraciones."
