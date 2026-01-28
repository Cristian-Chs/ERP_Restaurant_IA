import os
import pickle
from collections import Counter
from django.conf import settings
from bot.models import Order

# ----------------------------------------------------
#  Cargar modelo ML entrenado (si existe)
# ----------------------------------------------------
def cargar_modelo():
    modelo_path = os.path.join(settings.BASE_DIR, "recomendacion", "modelo_recomendacion.pkl")
    if not os.path.exists(modelo_path):
        return None
    with open(modelo_path, "rb") as f:
        return pickle.load(f)

# ----------------------------------------------------
#  Recomendación por popularidad (fallback)
# ----------------------------------------------------
def recomendar_popularidad(top_n=5):
    pedidos = Order.objects.all()
    conteo = Counter(p.item for p in pedidos)
    return [plato for plato, _ in conteo.most_common(top_n)]

# ----------------------------------------------------
#  Recomendación por similitud entre clientes
# ----------------------------------------------------
def recomendar_por_cliente(telegram_id, top_n=5):
    pedidos_cliente = Order.objects.filter(telegram_id=telegram_id)
    if not pedidos_cliente.exists():
        return recomendar_popularidad(top_n)

    platos_cliente = set(p.item for p in pedidos_cliente)
    similares = Counter()

    for pedido in Order.objects.exclude(telegram_id=telegram_id):
        if pedido.item in platos_cliente:
            similares[pedido.item] += 1

    if not similares:
        return recomendar_popularidad(top_n)

    return [plato for plato, _ in similares.most_common(top_n)]

# ----------------------------------------------------
#  Recomendación usando modelo ML (si está disponible)
# ----------------------------------------------------
def recomendar_ml(telegram_id, top_n=5):
    modelo = cargar_modelo()
    if modelo is None:
        return recomendar_por_cliente(telegram_id, top_n)

    # Obtener todos los platos únicos
    platos = Order.objects.values_list("item", flat=True).distinct()
    recomendaciones = []

    for plato in platos:
        try:
            pred = modelo.predict(telegram_id, plato)
            recomendaciones.append((plato, pred.est))
        except Exception:
            continue  # Ignorar errores de predicción

    if not recomendaciones:
        return recomendar_por_cliente(telegram_id, top_n)

    recomendaciones.sort(key=lambda x: x[1], reverse=True)
    return [plato for plato, _ in recomendaciones[:top_n]]
