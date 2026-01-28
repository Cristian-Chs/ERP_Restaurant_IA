#  Panel de Administración de Cupones

## Acceso

El sistema ahora cuenta con **dos paneles de administración**:

### 1. Panel Principal de Django

**URL**: `http://localhost:8000/admin/`

Gestión completa del sistema incluyendo:

- Pedidos (Orders)
- Ratings
- Gustos de Cliente
- Cupones
- Cupones Canjeados
- Puntos de Fidelidad

### 2. Panel Dedicado de Cupones 

**URL**: `http://localhost:8000/admin/coupons/`

Panel especializado para gestión de promociones que incluye:

-  **Cupones**: Crear y gestionar cupones de descuento
-  **Cupones Canjeados**: Historial de canjes
-  **Puntos de Fidelidad**: Gestión de puntos de usuarios

## Características del Panel de Cupones

### Vista de Lista Mejorada

#### Cupones

- **Código**: Identificador único del cupón
- **Descuento**: Muestra visual del descuento ( $5 o  10%)
- **Tipo**: Fijo o Porcentaje
- **Costo en Puntos**: Puntos necesarios para canjear
- **Estado**:  Activo /  Inactivo
- **Uso**: Indicador visual con semáforo
  - 🟢 Menos del 75% usado
  - 🟡 75-99% usado
  -  100% usado o agotado

#### Cupones Canjeados

- **Cupón**:  Código del cupón usado
- **Usuario**: Telegram ID
- **Descuento Aplicado**:  Monto del descuento
- **Fecha de Canje**: Cuándo se usó
- **Orden**: Link directo a la orden asociada

### Acciones Rápidas

Selecciona uno o más cupones y aplica acciones en lote:

1. ** Activar cupones seleccionados**

   - Activa cupones desactivados

2. ** Desactivar cupones seleccionados**

   - Desactiva cupones temporalmente

3. ** Reiniciar contador de usos**
   - Resetea el contador de usos a 0
   - Útil para reutilizar cupones

### Filtros Disponibles

- Por estado (Activo/Inactivo)
- Por tipo de descuento (Fijo/Porcentaje)
- Por fecha de creación
- Por fecha de expiración

### Formulario de Creación

El formulario está organizado en secciones:

####  Información del Cupón

- **Código**: Ej: PROMO2026, VERANO2026
- **Tipo de Descuento**: Fijo ($) o Porcentaje (%)
- **Monto del Descuento**: $5 o 10 (para 10%)
- **Costo en Puntos**: 0 = cupón manual, >0 = canjeable por puntos

#### ⏰ Validez y Límites

- **Activo**: Activar/desactivar cupón
- **Válido Desde**: Fecha de inicio (opcional)
- **Válido Hasta**: Fecha de expiración (opcional)
- **Usos Máximos**: 0 = ilimitado
- **Usos Actuales**: Solo lectura

####  Restricciones

- **Monto Mínimo del Pedido**: Ej: $10.00

## Ejemplos de Cupones

### Cupón de Bienvenida

```
Código: BIENVENIDO
Tipo: Fijo
Descuento: $5.00
Costo en Puntos: 0
Monto Mínimo: $15.00
Usos Máximos: 100
```

### Cupón de Porcentaje

```
Código: VERANO20
Tipo: Porcentaje
Descuento: 20
Costo en Puntos: 0
Monto Mínimo: $20.00
Válido Hasta: 2026-03-31
```

### Cupón por Puntos

```
Código: PUNTOS50
Tipo: Fijo
Descuento: $5.00
Costo en Puntos: 50
Monto Mínimo: $10.00
Usos Máximos: 0 (ilimitado)
```

## Ventajas del Panel Separado

1. **Interfaz Especializada**: Diseñada específicamente para gestión de promociones
2. **Acceso Controlado**: Puedes dar acceso solo al panel de cupones sin exponer todo el admin
3. **Mejor Organización**: Separa la gestión de promociones del resto del sistema
4. **Visualización Mejorada**: Iconos y colores para identificar rápidamente el estado

## Permisos

Para acceder a cualquiera de los paneles, el usuario debe:

- Tener `is_staff = True`
- Tener permisos sobre los modelos correspondientes

## Notas Técnicas

- Ambos paneles comparten la misma base de datos
- Los cambios en un panel se reflejan en el otro
- El panel de cupones es una vista especializada del admin principal
- Ubicación del código:
  - `bot/coupon_admin.py`: Configuración del AdminSite
  - `bot/coupon_urls.py`: URLs del panel de cupones
  - `bot/admin.py`: Configuración de los ModelAdmin
