# 05. Arquitectura del Frontend

## Resumen

El frontend es una **Single Page Application (SPA)** de React inicializada con **Vite**. Se centra en una interfaz fideligna, responsiva, con animaciones (Framer Motion) y actualizaciones en tiempo real.

## Estructura de Carpetas (`reactproject/src/`)

```text
src/
├── components/       # Bloques de UI Reutilizables
│   ├── AuroraBackground.jsx  # Efecto visual para landing/auth
│   ├── Navbar.jsx            # Barra de navegación principal
│   ├── CarritoTelegram.jsx   # Lógica del Carrito de Compras
│   └── TelegramButton.jsx    # Botón flotante de soporte
├── pages/            # Vistas de Página Completa
│   ├── KitchenPanel.jsx      # Tablero del Chef (Auto-refresco)
│   ├── Menu.jsx              # Catálogo Principal de Productos
│   ├── Login.jsx             # Página de Autenticación
│   └── AdminPanel.jsx        # Tablero de Gestión
├── App.jsx           # Enrutador Principal y Proveedores de Estado Global
└── main.jsx          # Punto de entrada
```

## Módulos Clave

### Panel de Cocina (`KitchenPanel.jsx`)

- Mecanismo de sondeo (polling cada 10s) a `GET /api/bot/api/cocina/orders/`.
- Divide los pedidos en columnas: **Local** (Comer aquí) y **Delivery**.
- Tarjetas interactivas para "Completar" o "Cancelar" pedidos.

### Menú y Carrito (`Menu.jsx`, `CarritoTelegram.jsx`)

- **Lógica del Carrito**: Gestionada vía el hook `useCartLogic` en `App.jsx`, pasado como props.
- **Visualización de Productos**: Obtiene datos de `GET /api/products/`. Maneja estados de carga y error.

### Autenticación

- Usa `localStorage` para almacenar tokens JWT.
- **ProtectedRoute**: Un componente envoltorio (wrapper) para restringir acceso a `/admin` y `/kitchen-panel`.

## Estrategia de Estilos

- **Vanilla CSS**: Usado para el diseño base.
- **Estilos en Línea**: Uso extensivo de estilos en línea de React para valores dinámicos (animaciones).
- **Librerías**: `framer-motion` para transiciones de página y popups modales.
