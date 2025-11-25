import pandas as pd
from bot.models import Order

def export_orders():
    # Extraer datos de pedidos
    orders = Order.objects.all().values("telegram_id", "item")
    df = pd.DataFrame(list(orders))
    # Simular un "rating" (ejemplo: cada pedido = 5 estrellas)
    df["rating"] = 5
    df.to_csv("orders.csv", index=False)
    print("Datos exportados a orders.csv")
