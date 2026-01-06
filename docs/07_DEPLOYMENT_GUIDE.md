# 07. Guía de Despliegue (Deployment)

## Lista de Verificación para Producción

### 1. Base de Datos

- Cambiar de SQLite a **PostgreSQL**.
- Actualizar `DATABASES` en `settings.py`.

### 2. Archivos Estáticos

- Ejecutar `python manage.py collectstatic` para recolectar archivos estáticos del backend.
- Construir (Build) la app de React:
  ```bash
  cd reactproject
  npm run build
  ```
- Servir la carpeta `reactproject/dist/` usando Nginx o copiarla al root estático de Django si se sirve vía Django (no recomendado para carga alta).

### 3. Seguridad

- Establecer `DEBUG=False` en `.env`.
- Configurar `ALLOWED_HOSTS` con tu nombre de dominio.
- Generar una `SECRET_KEY` fuerte.
- Configurar la lista de permitidos en CORS (`settings.py`).

### 4. Servidor Web (Gunicorn + Nginx)

- Usar **Gunicorn** para ejecutar la aplicación Django:
  ```bash
  gunicorn backend.wsgi:application --bind 0.0.0.0:8000
  ```
- Usar **Nginx** como proxy inverso:
  - Enrutar peticiones `/api/` a Gunicorn (puerto 8000).
  - Servir `/` (Frontend) desde los archivos estáticos construidos (`dist`).

### 5. Bot de Telegram

- Usar **Webhooks** en lugar de Polling para rendimiento en producción.
- Configurar un certificado SSL (requerido para Webhooks de Telegram). Nginx con Let's Encrypt (`certbot`) es la solución estándar.

## Gestión de Procesos

Usar **Supervisor** o **Systemd** para mantener el proceso de Gunicorn y el proceso del Bot corriendo continuamente.

Ejemplo de servicio Systemd para Gunicorn:

```ini
[Unit]
Description=Instancia Gunicorn para servir 4 Sabores
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/Backend
ExecStart=/path/to/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/path/to/backend.sock backend.wsgi:application

[Install]
WantedBy=multi-user.target
```
