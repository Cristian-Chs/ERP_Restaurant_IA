# 03. Arquitectura del Backend

## Resumen

El backend está construido con **Django** y estructurado en varias aplicaciones (`apps`) para separar responsabilidades. Expone una API REST utilizando **Django Rest Framework (DRF)**.

## Estructura del Proyecto (`Backend/`)

- `backend/`: Configuraciones principales del proyecto, rutas (`urls.py`) y configuración WSGI/ASGI.
- `core/`: App principal que maneja **Productos**, **Ingredientes** y **Gestión de Usuarios**.
- `bot/`: App dedicada a la lógica del **Bot de Telegram**, **Procesamiento de Pedidos** y **Webhooks**.
- `ml/`: Paquete personalizado que contiene la lógica de Inteligencia Artificial/Machine Learning para recomendaciones.
- `scripts/`: Scripts de utilidad para exportación/importación de datos y mantenimiento.

## Modelos Clave

### App Core (`backend.core`)

| Modelo       | Descripción                                      | Campos Clave                                                       |
| ------------ | ------------------------------------------------ | ------------------------------------------------------------------ |
| `Product`    | Representa un ítem del menú.                     | `name`, `price`, `category`, `ingredientes` (M2M), `sabores` (M2M) |
| `Ingredient` | Materias primas o extras.                        | `nombre`, `disponible_como_extra`                                  |
| `Flavor`     | Variaciones de productos (Ej: Sabores de pizza). | `nombre`                                                           |
| `User`       | Modelo de usuario personalizado (vía Djoser).    | `username`, `email`, `role`                                        |

### App Bot (`backend.bot`)

| Modelo            | Descripción                                | Campos Clave                                                   |
| ----------------- | ------------------------------------------ | -------------------------------------------------------------- |
| `Order`           | Representa una transacción de cliente.     | `telegram_id`, `item` (Nombre Prod.), `status`, `service_type` |
| `TelegramSession` | Gestiona el estado conversacional del bot. | `state` (ej: 'SELECTING_QUANTITY'), `temp_data` (JSON)         |
| `Rating`          | Feedback para platos.                      | `telegram_id`, `plato`, `estrellas` (1-5)                      |
| `GustoCliente`    | Preferencias agregadas del usuario.        | `telegram_id`, `gustos` (Lista)                                |

## Aspectos Destacados de la Lógica de Negocio

- **Señales (Signals)**: Se utilizan para disparar notificaciones cuando cambia el estado de una `Order` (por ejemplo, notificar al usuario vía Telegram cuando cocina marca un pedido como "Listo").
- **Vistas Personalizadas**:
  - `api_cocina_orders`: Consulta optimizada para el Panel de Cocina (solo pedidos activos).
  - `TelegramLoginView`: Maneja la verificación de autenticación basada en widgets.

## Integración de Machine Learning (`Backend/ml/`)

El sistema emplea un motor de recomendación híbrido:

1.  **Filtrado Colaborativo**: Sugiere ítems basados en usuarios similares.
2.  **Basado en Contenido**: Sugiere ítems similares a lo que al usuario le gustó antes (usando ingredientes/tags).
3.  **Popularidad**: Respaldo para usuarios nuevos (sugiere "Los más vendidos").
