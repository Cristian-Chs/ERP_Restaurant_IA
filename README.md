# 🍽️ 4 Sabores Restaurant App

Sistema integral de gestión de restaurante con Bot de Telegram, Panel Web de Administración y Análisis Inteligente.

## 📁 Estructura del Proyecto

```
ReactPythonBackend/
├── Backend/           # Django REST API + Telegram Bot
├── reactproject/      # React Frontend (Vite)
└── documentation.txt  # Documentación técnica completa
```

## 🚀 Inicio Rápido

### Backend (Django)

```bash
cd Backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend (React)

```bash
cd reactproject
npm install
npm run dev
```

### Bot de Telegram

```bash
cd Backend/bot_Cliente
python main.py
```

## 🔑 Credenciales de Desarrollo

Ver `documentation.txt` para credenciales completas.

**Admin Django:**

- Usuario: `Admin`
- Password: `password`

**Panel de Cocina:**

- Usuario: `cocina`
- Password: `Pelota4321`

## 📚 Documentación

- **Completa:** Ver [`documentation.txt`](./documentation.txt)
- **Detallada:** Ver carpeta [`docs/`](./docs/)

## 🛠️ Stack Tecnológico

**Backend:**

- Django 5.2.8 + DRF
- PostgreSQL / SQLite
- Python Telegram Bot
- Pandas, NumPy (Analytics)
- Groq AI (Llama 3.3)

**Frontend:**

- React 18 + Vite
- CSS Modules
- React Router

## 📦 Módulos Principales

- **core** - Productos, ingredientes, empleados
- **bot** - Bot de Telegram (admin)
- **bot_cliente** - Bot de clientes (refactorizado)
- **recomendacion** - Sistema de recomendaciones ML
- **analytics** - Análisis con Pandas

## 🔗 URLs Importantes

- Admin Panel: http://localhost:5173/admin-panel
- Kitchen Panel: http://localhost:5173/kitchen-panel
- Django Admin: http://localhost:8000/admin/
- API Root: http://localhost:8000/api/

## 📝 Notas

- El bot usa `bot_state.pkl` para persistencia
- Configurar variables de entorno según `Backend/env.example`
- Ver `documentation.txt` para troubleshooting

---

**Versión:** 2.0 | **Última actualización:** Enero 2026
