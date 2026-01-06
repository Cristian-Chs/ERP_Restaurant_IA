# 02. Configuración e Instalación

## Pre requisitos

Asegúrate de tener instalado lo siguiente en tu máquina de desarrollo:

- **Python**: Versión 3.10 o superior.
- **Node.js**: Versión 18 o superior (se recomienda LTS).
- **Git**: Para control de versiones.
- **Virtualenv**: Recomendado para gestionar dependencias de Python.

## 1. Clonar el Repositorio

```bash
git clone <url_del_repositorio>
cd ReactPythonBackend
```

## 2. Configuración del Backend

El backend se encuentra en el directorio `Backend/`.

### Paso 1: Crear Entorno Virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 2: Instalar Dependencias

```bash
cd Backend
pip install -r requirements.txt
```

### Paso 3: Variables de Entorno

Crea un archivo `.env` en `Backend/backend/` (junto a `settings.py`) con el siguiente contenido:

```ini
SECRET_KEY=clave_secreta_desarrollo_123
DEBUG=True
TELEGRAM_BOT_TOKEN=tu_token_de_telegram_aqui
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Paso 4: Migraciones de Base de Datos

```bash
python manage.py migrate
```

### Paso 5: Crear Superusuario (Admin)

```bash
python manage.py createsuperuser
```

### Paso 6: Ejecutar Servidor

```bash
python manage.py runserver
```

La API estará disponible en `http://localhost:8000/`.

## 3. Configuración del Frontend

El frontend se encuentra en el directorio `reactproject/`.

### Paso 1: Instalar Dependencias

```bash
cd reactproject
npm install
```

### Paso 2: Ejecutar Servidor de Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173/`.

## 4. Ejecución del Bot de Telegram

El bot se ejecuta compartiendo el contexto de Django.

Para desarrollo local:

- Asegúrate de que `TELEGRAM_BOT_TOKEN` esté configurado correctamente.
- Revisa la lógica en `Backend/bot/` para ver el punto de entrada (usualmente un script o comando de gestión, o webhook).
