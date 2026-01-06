# 01. Visión General del Proyecto

## 1. Introducción

**Sistema de Restaurante 4 Sabores** es una solución integral diseñada para modernizar las operaciones del restaurante. Integra un **Bot de Telegram** para pedidos automatizados con una **Aplicación Web React** de alto rendimiento para la gestión de cocina y administración.

## 2. Características Principales

- **Pedidos Multicanal**: Los clientes pueden realizar pedidos a través de una Web App dedicada o directamente mediante comandos en Telegram.
- **Panel de Cocina en Tiempo Real**: Un tablero dedicado para los chefs que se actualiza instantáneamente cuando llegan nuevos pedidos, distinguiendo entre `Comer Aquí`, `Delivery` y `Pick-up`.
- **Panel de Administración**: Control total sobre productos, ingredientes, estadísticas de ventas y gestión de usuarios.
- **Recomendaciones por IA**: Un motor de Machine Learning integrado sugiere platos a los usuarios basándose en su historial de pedidos y tendencias globales.
- **Autenticación con Telegram**: Experiencia de inicio de sesión fluida utilizando los widgets de Telegram.

## 3. Stack Tecnológico

### Backend

- **Framework**: Django 5.x
- **API**: Django Rest Framework (DRF)
- **Base de Datos**: SQLite (Desarrollo) / PostgreSQL (Producción)
- **IA/ML**: Scikit-learn, Pandas
- **Autenticación**: JWT (Djoser) + Autenticación personalizada de Telegram

### Frontend

- **Framework**: React 18 (Vite)
- **Estilos**: CSS Modules, Styled Components
- **Gestión de Estado**: React Hooks (Context API)
- **Rutas**: React Router DOM 6

### Servicios Externos

- **Telegram Bot API**: Para interacción con usuarios y notificaciones.

## 4. Arquitectura del Sistema

El sistema sigue una arquitectura Cliente-Servidor estándar.

```mermaid
graph TD
    Client[Usuario (Web/Telegram)] -->|HTTP/HTTPS| API[Django REST API]
    Chef[Personal de Cocina] -->|Web Socket/Polling| API
    Admin[Administrador] -->|HTTPS| API

    API -->|Lectura/Escritura| DB[(Base de Datos)]
    API -->|Procesamiento| ML[Motor ML]
    API -->|Notificaciones| Bot[Bot de Telegram]
```
