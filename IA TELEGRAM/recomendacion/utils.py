from collections import Counter
from bot.models import Order  # 👈 Importas pedidos desde tu app bot
from .models import Plato

def recomendar_popularidad():
    pedidos = Order.objects.all()
    conteo = Counter()
    for pedido in pedidos:
        conteo[pedido.item] += 1
    return [plato for plato, _ in conteo.most_common(5)]

def recomendar_por_cliente(telegram_id):
    pedidos_cliente = Order.objects.filter(telegram_id=telegram_id)
    if not pedidos_cliente.exists():
        return recomendar_popularidad()

    platos_cliente = set(p.item for p in pedidos_cliente)
    similares = Counter()

    for pedido in Order.objects.exclude(telegram_id=telegram_id):
        if pedido.item in platos_cliente:
            similares[pedido.item] += 1

    if not similares:
        return recomendar_popularidad()

    return [plato for plato, _ in similares.most_common(5)]


import pickle
from bot.models import Order

# Cargar modelo entrenado
with open("modelo_recomendacion.pkl", "rb") as f:
    modelo = pickle.load(f)

def recomendar_ml(telegram_id):
    # Obtener todos los platos únicos
    platos = Order.objects.values_list("item", flat=True).distinct()
    recomendaciones = []

    for plato in platos:
        pred = modelo.predict(telegram_id, plato)
        recomendaciones.append((plato, pred.est))

    # Ordenar por puntuación estimada
    recomendaciones.sort(key=lambda x: x[1], reverse=True)
    return [plato for plato, _ in recomendaciones[:5]]
