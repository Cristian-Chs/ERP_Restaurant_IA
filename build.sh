#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install Dependencies
pip install -r Backend/requirements.txt
pip install gunicorn # Ensure binary is installed

# 2. Build Frontend (React)
cd reactproject
npm install
npm run build
cd ..

# 3. Collect Static Files (Django)
cd Backend
python manage.py collectstatic --no-input
python manage.py migrate
