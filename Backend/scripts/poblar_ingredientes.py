import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Product, Ingredient, CATEGORY_CHOICES

print("=" * 50)
print("POBLANDO BASE DE DATOS CON INGREDIENTES")
print("=" * 50)

# Crear ingredientes comunes
ingredientes_data = [
    # Vegetales
    ("tomate", True),
    ("lechuga", True),
    ("cebolla", True),
    ("pepino", True),
    ("aguacate", True),
    ("pimiento", True),
    
    # Proteinas
    ("queso", True),
    ("jamon", True),
    ("pollo", True),
    ("carne", True),
    ("bacon", True),
    ("huevo", True),
    
    # Salsas y condimentos
    ("mayonesa", True),
    ("mostaza", True),
    ("ketchup", True),
    ("salsa de tomate", True),
    ("salsa bbq", True),
    
    # Otros
    ("pan", False),
    ("masa de pizza", False),
    ("arroz", False),
    ("pasta", False),
]

print("\nCreando ingredientes...")
for nombre, disponible_extra in ingredientes_data:
    ing, created = Ingredient.objects.get_or_create(
        nombre=nombre,
        defaults={"disponible_como_extra": disponible_extra}
    )
    if created:
        print(f"  Creado: {nombre} (extra: {disponible_extra})")
    else:
        print(f"  Ya existe: {nombre}")

print(f"\nTotal ingredientes: {Ingredient.objects.count()}")

def poblar_productos_paraguaneros():
    """
    Función para crear los productos del menú 'Los Cuatros Sabores de Paraguaná'
    """
    print("\n" + "=" * 50)
    print("CREANDO PRODUCTOS - LOS CUATROS SABORES DE PARAGUANÁ")
    print("=" * 50)
    
    productos_data = [
        # 🥗 ENTRADAS
        {
            "name": "Arepitas dulces con nata",
            "description": "Deliciosas arepitas dulces tradicionales servidas con nata fresca",
            "price": 3.50,
            "category": "entradas",
            "imagen": "arepitas_dulces.jpg"
        },
        {
            "name": "Empanadas de cazón y queso de cabra",
            "description": "Empanadas crujientes rellenas de cazón fresco y queso de cabra artesanal",
            "price": 4.00,
            "category": "entradas",
            "imagen": "empanadas_cazon.jpg"
        },
        {
            "name": "Tostones con guasacaca y chicharrón",
            "description": "Tostones crujientes acompañados de guasacaca casera y chicharrón",
            "price": 4.50,
            "category": "entradas",
            "imagen": "tostones_guasacaca.jpg"
        },
        
        # 🍲 SOPAS Y CREMAS
        {
            "name": "Sopa de pescado fresco",
            "description": "Sopa tradicional preparada con pescado fresco del día y vegetales",
            "price": 6.00,
            "category": "principales",
            "imagen": "sopa_pescado.jpg"
        },
        {
            "name": "Crema de auyama con queso rallado",
            "description": "Suave crema de auyama coronada con queso rallado",
            "price": 5.00,
            "category": "principales",
            "imagen": "crema_auyama.jpg"
        },
        {
            "name": "Mondongo paraguanero",
            "description": "Mondongo tradicional de Paraguaná con su sazón única",
            "price": 7.00,
            "category": "principales",
            "imagen": "mondongo.jpg"
        },
        
        # 🍖 PLATOS FUERTES
        {
            "name": "Chivo en coco con arroz con coco",
            "description": "Exquisito chivo guisado en leche de coco, acompañado de arroz con coco",
            "price": 12.00,
            "category": "principales",
            "imagen": "chivo_coco.jpg"
        },
        {
            "name": "Filete de pescado frito con tostones y ensalada fresca",
            "description": "Filete de pescado frito dorado, servido con tostones y ensalada del día",
            "price": 10.00,
            "category": "principales",
            "imagen": "filete_pescado.jpg"
        },
        {
            "name": "Pollo guisado con arepas asadas",
            "description": "Pollo guisado en su jugo con especias locales, acompañado de arepas asadas",
            "price": 8.50,
            "category": "principales",
            "imagen": "pollo_guisado.jpg"
        },
        {
            "name": "Parrilla mixta Los Cuatros Sabores",
            "description": "Parrilla especial con carne, pollo, chorizo y chivo - perfecta para compartir",
            "price": 18.00,
            "category": "principales",
            "imagen": "parrilla_mixta.jpg"
        },
        
        # 🍹 BEBIDAS
        {
            "name": "Guarapita de frutas locales",
            "description": "Bebida tradicional paraguanera con frutas frescas de la región",
            "price": 3.00,
            "category": "bebidas",
            "imagen": "guarapita.jpg"
        },
        {
            "name": "Jugo natural de lechoza",
            "description": "Jugo natural de lechoza fresca",
            "price": 2.50,
            "category": "bebidas",
            "imagen": "jugo_lechoza.jpg"
        },
        {
            "name": "Jugo natural de patilla",
            "description": "Refrescante jugo natural de patilla",
            "price": 2.50,
            "category": "bebidas",
            "imagen": "jugo_patilla.jpg"
        },
        {
            "name": "Jugo natural de guayaba",
            "description": "Delicioso jugo natural de guayaba",
            "price": 2.50,
            "category": "bebidas",
            "imagen": "jugo_guayaba.jpg"
        },
        {
            "name": "Cerveza artesanal falconiana",
            "description": "Cerveza artesanal producida en Falcón",
            "price": 4.00,
            "category": "bebidas",
            "imagen": "cerveza_artesanal.jpg"
        },
        {
            "name": "Refrescos y agua mineral",
            "description": "Variedad de refrescos y agua mineral",
            "price": 1.50,
            "category": "bebidas",
            "imagen": "refrescos.jpg"
        },
        
        # 🍮 POSTRES
        {
            "name": "Dulce de leche cortada",
            "description": "Tradicional dulce de leche cortada casero",
            "price": 3.50,
            "category": "postres",
            "imagen": "dulce_leche.jpg"
        },
        {
            "name": "Quesillo tradicional",
            "description": "Quesillo venezolano tradicional con su caramelo",
            "price": 4.00,
            "category": "postres",
            "imagen": "quesillo.jpg"
        },
        {
            "name": "Conserva de coco",
            "description": "Dulce conserva de coco rallado",
            "price": 3.00,
            "category": "postres",
            "imagen": "conserva_coco.jpg"
        },
    ]
    
    print(f"\nCreando {len(productos_data)} productos...")
    productos_creados = 0
    productos_existentes = 0
    
    for producto_info in productos_data:
        producto, created = Product.objects.get_or_create(
            name=producto_info["name"],
            defaults={
                "description": producto_info["description"],
                "price": producto_info["price"],
                "category": producto_info["category"],
                "imagen": producto_info["imagen"],
                "is_active": True
            }
        )
        
        if created:
            productos_creados += 1
            print(f"  ✅ Creado: {producto_info['name']} (${producto_info['price']}) - {producto_info['category']}")
        else:
            productos_existentes += 1
            print(f"  ℹ️  Ya existe: {producto_info['name']}")
    
    print(f"\n📊 RESUMEN:")
    print(f"  - Productos creados: {productos_creados}")
    print(f"  - Productos ya existentes: {productos_existentes}")
    print(f"  - Total en la base de datos: {Product.objects.count()}")
    
    # Mostrar resumen por categoría
    print(f"\n📋 PRODUCTOS POR CATEGORÍA:")
    for categoria_code, categoria_nombre in CATEGORY_CHOICES:
        count = Product.objects.filter(category=categoria_code).count()
        print(f"  - {categoria_nombre.capitalize()}: {count} productos")
    
    return productos_creados, productos_existentes


# Asignar ingredientes a productos existentes
print("\nAsignando ingredientes a productos...")

# Hamburguesa
try:
    hamburguesa = Product.objects.filter(name__iexact="hamburguesa").first()
    if hamburguesa:
        ingredientes_hamburguesa = Ingredient.objects.filter(
            nombre__in=["pan", "carne", "queso", "lechuga", "tomate", "cebolla", "mayonesa", "ketchup"]
        )
        hamburguesa.ingredientes.set(ingredientes_hamburguesa)
        print(f"  Hamburguesa: {hamburguesa.ingredientes.count()} ingredientes")
    else:
        print("  Producto 'Hamburguesa' no encontrado")
except Exception as e:
    print(f"  Error con hamburguesa: {e}")

# Pizza
try:
    pizza = Product.objects.filter(name__iexact="pizza").first()
    if pizza:
        ingredientes_pizza = Ingredient.objects.filter(
            nombre__in=["masa de pizza", "salsa de tomate", "queso", "tomate", "jamon", "pimiento"]
        )
        pizza.ingredientes.set(ingredientes_pizza)
        print(f"  Pizza: {pizza.ingredientes.count()} ingredientes")
    else:
        print("  Producto 'Pizza' no encontrado")
except Exception as e:
    print(f"  Error con pizza: {e}")


print("\n" + "=" * 50)

# Llamar a la función para crear productos paraguaneros
poblar_productos_paraguaneros()

print("\n" + "=" * 50)
print("PROCESO COMPLETADO")
print("=" * 50)

# Verificacion final
print("\nRESUMEN:")
print(f"  - Total ingredientes: {Ingredient.objects.count()}")
print(f"  - Ingredientes como extra: {Ingredient.objects.filter(disponible_como_extra=True).count()}")
print(f"  - Total productos: {Product.objects.count()}")

for producto in Product.objects.all()[:5]:
    count = producto.ingredientes.count()
    print(f"  - {producto.name}: {count} ingredientes")
