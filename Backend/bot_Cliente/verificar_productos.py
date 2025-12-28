import sys
import os

# Configurar Django
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from core.models import Product

# Verificar productos
productos = Product.objects.filter(is_active=True)
print(f"\n{'='*50}")
print(f"PRODUCTOS EN LA BASE DE DATOS")
print(f"{'='*50}\n")
print(f"Total de productos activos: {productos.count()}\n")

if productos.exists():
    for p in productos:
        print(f"  - {p.name} (Categoría: {p.category}, Precio: ${p.price})")
else:
    print("  ⚠️ NO HAY PRODUCTOS EN LA BASE DE DATOS")
    print("\n  Para agregar productos, puedes:")
    print("  1. Usar el panel de administración de Django")
    print("  2. Crear productos desde el frontend React")
    print("  3. Usar el shell de Django: python manage.py shell")

print(f"\n{'='*50}\n")
