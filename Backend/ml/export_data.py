import os
import sys
import django
import pandas as pd

# 👇 Añade la carpeta raíz del proyecto (django Backend/) al PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# 👇 Configura Django correctamente
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import Order

def export_orders():
    # Extraer datos de pedidos
    orders = Order.objects.all().values("telegram_id", "item", "status")
    df = pd.DataFrame(list(orders))

    if df.empty:
        print("⚠️ No hay pedidos en la base de datos. Exportación cancelada.")
        return

    # Simular un "rating" (ejemplo: cada pedido = 5 estrellas)
    df["rating"] = 5

    # Guardar en CSV
    output_path = os.path.join(os.path.dirname(__file__), "..", "orders.csv")
    df.to_csv(output_path, index=False)

    print(f"✅ Datos exportados a {output_path}")

if __name__ == "__main__":
    export_orders()
