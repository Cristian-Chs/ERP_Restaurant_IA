#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 1. Installing Backend Dependencies..."
# Usamos --no-cache-dir para ahorrar espacio en disco durante el build
pip install --no-cache-dir -r Backend/requirements.txt
pip install --no-cache-dir gunicorn whitenoise

echo "🎨 2. Building Frontend (React)..."
cd reactproject
# npm ci es más rápido y estable para despliegues
if [ -f package-lock.json ]; then
    npm ci
else
    npm install
fi
npm run build
cd ..

echo "📂 3. Collecting Static Files..."
cd Backend
python manage.py collectstatic --no-input
python manage.py migrate
echo "✅ Build Complete!"
