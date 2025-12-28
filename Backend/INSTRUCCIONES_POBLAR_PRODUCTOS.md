# 🍴 Instrucciones para Poblar Productos - Los Cuatros Sabores de Paraguaná

## ✅ Función Creada

Se ha creado la función `poblar_productos_paraguaneros()` en el archivo `poblar_ingredientes.py` que incluye **19 productos** del menú especial:

### 🥗 Entradas (3 productos)

- Arepitas dulces con nata - $3.50
- Empanadas de cazón y queso de cabra - $4.00
- Tostones con guasacaca y chicharrón - $4.50

### 🍲 Sopas y Cremas (3 productos)

- Sopa de pescado fresco - $6.00
- Crema de auyama con queso rallado - $5.00
- Mondongo paraguanero - $7.00

### 🍖 Platos Fuertes (4 productos)

- Chivo en coco con arroz con coco - $12.00
- Filete de pescado frito con tostones y ensalada fresca - $10.00
- Pollo guisado con arepas asadas - $8.50
- Parrilla mixta Los Cuatros Sabores - $18.00

### 🍹 Bebidas (6 productos)

- Guarapita de frutas locales - $3.00
- Jugo natural de lechoza - $2.50
- Jugo natural de patilla - $2.50
- Jugo natural de guayaba - $2.50
- Cerveza artesanal falconiana - $4.00
- Refrescos y agua mineral - $1.50

### 🍮 Postres (3 productos)

- Dulce de leche cortada - $3.50
- Quesillo tradicional - $4.00
- Conserva de coco - $3.00

---

## 🚀 Cómo Ejecutar el Script

### Opción 1: Ejecutar todo el script (ingredientes + productos)

```bash
cd Backend
python poblar_ingredientes.py
```

Este comando:

1. Creará los ingredientes básicos
2. Asignará ingredientes a productos existentes (hamburguesa, pizza)
3. **Creará los 19 productos del menú paraguanero**
4. Mostrará un resumen completo

### Opción 2: Ejecutar solo la función de productos

Si solo quieres crear los productos paraguaneros sin ejecutar todo el script, puedes usar Django shell:

```bash
cd Backend
python manage.py shell
```

Luego en el shell de Django:

```python
from core.models import Product, CATEGORY_CHOICES
exec(open('poblar_ingredientes.py').read())
poblar_productos_paraguaneros()
```

---

## 📋 Características de la Función

✅ **No duplica productos**: Usa `get_or_create()` para evitar duplicados  
✅ **Categorización automática**: Asigna cada producto a su categoría correcta  
✅ **Precios realistas**: Precios en dólares según el tipo de plato  
✅ **Descripciones detalladas**: Cada producto tiene una descripción atractiva  
✅ **Imágenes asignadas**: Nombres de archivo para las imágenes de cada plato  
✅ **Resumen detallado**: Muestra estadísticas al finalizar

---

## 📊 Salida Esperada

Al ejecutar el script verás:

```
==================================================
CREANDO PRODUCTOS - LOS CUATROS SABORES DE PARAGUANÁ
==================================================

Creando 19 productos...
  ✅ Creado: Arepitas dulces con nata ($3.5) - entradas
  ✅ Creado: Empanadas de cazón y queso de cabra ($4.0) - entradas
  ...

📊 RESUMEN:
  - Productos creados: 19
  - Productos ya existentes: 0
  - Total en la base de datos: 19

📋 PRODUCTOS POR CATEGORÍA:
  - Promociones: 0 productos
  - Entradas: 3 productos
  - Principales: 7 productos
  - Postres: 3 productos
  - Bebidas: 6 productos
```

---

## ⚠️ Requisitos Previos

Asegúrate de tener:

1. Django instalado (`pip install -r requirements.txt`)
2. Base de datos configurada y migrada
3. El modelo `Product` con los campos: `name`, `description`, `price`, `category`, `imagen`, `is_active`

---

## 🔧 Personalización

Si necesitas modificar algún producto, edita la lista `productos_data` en la función `poblar_productos_paraguaneros()` dentro del archivo `poblar_ingredientes.py`.

Cada producto tiene esta estructura:

```python
{
    "name": "Nombre del producto",
    "description": "Descripción detallada",
    "price": 10.00,
    "category": "principales",  # entradas, principales, postres, bebidas
    "imagen": "nombre_imagen.jpg"
}
```
