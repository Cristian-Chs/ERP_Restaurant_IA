# 04. Referencia de API

URL Base: `http://localhost:8000/api/`

## Autenticación (`/auth/`)

- **Login (JWT)**: `POST /auth/jwt/create/`
  - Body: `{ "username": "...", "password": "..." }`
- **Registro**: `POST /auth/users/`
- **Login con Telegram**: `POST /auth/telegram/`
  - Body: Datos del Widget de Telegram (hash, id, first_name, etc.)

## Productos (`/core/`)

- **Listar Todos (Agrupados)**: `GET /products/`
  - Devuelve productos agrupados por categorías (Entradas, Principales, etc.).
- **Lista Plana**: `GET /productos/`
- **Listar Ingredientes**: `GET /ingredientes/`

## Control de Acceso (Admin)

- **Admin Productos**: `POST/PUT/DELETE /products-admin/{id}/`
- **Estadísticas de Ventas**: `GET /admin/stats/`
- **Predicción de Ventas**: `GET /admin/prediction/`

## Bot y Cocina (`/bot/`)

### Panel de Cocina

- **Obtener Pedidos Pendientes**: `GET /bot/api/cocina/orders/`
- **Marcar Listo**: `POST /bot/api/cocina/orders/{id}/ready/`
- **Rechazar Pedido**: `POST /bot/api/cocina/orders/{id}/reject/`

### Servicio de IA

- **Obtener Recomendaciones**: `GET /bot/recomendacion_hibrida/{telegram_id}/`
  - Retorna: JSON con lista `recomendaciones` (Nombres de productos).

### Gestión de Sesión

- **Obtener Sesión**: `GET /bot/session/{telegram_id}/`
- **Actualizar Sesión**: `POST /bot/session/update/{telegram_id}/`
- **Resetear Sesión**: `POST /bot/session/reset/{telegram_id}/`
