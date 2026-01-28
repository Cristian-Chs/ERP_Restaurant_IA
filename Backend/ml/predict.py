import os
import sys
import django
import pickle
import numpy as np
from typing import List, Tuple, Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import Order

def cargar_modelo() -> Dict[str, Any] | None:
    modelo_path = os.path.join(os.path.dirname(__file__), "modelo_recomendacion.pkl")
    if not os.path.exists(modelo_path):
        print(" No se encontró el archivo modelo_recomendacion.pkl")
        return None
    try:
        with open(modelo_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f" Error al cargar el modelo: {e}")
        return None

def recomendar_popularidad(top_n: int = 5) -> List[str]:
    pedidos = Order.objects.all()
    conteo: dict[str, int] = {}
    for pedido in pedidos:
        conteo[pedido.item] = conteo.get(pedido.item, 0) + 1

    return [
        plato for plato, _ in 
        sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:top_n]
    ]

def recomendar_ml(telegram_id: int, top_n: int = 5) -> List[str]:
    modelo_data = cargar_modelo()
    if modelo_data is None:
        return recomendar_popularidad(top_n)

    svd = modelo_data["svd"]
    user_encoder = modelo_data["user_encoder"]
    item_encoder = modelo_data["item_encoder"]
    user_latent_matrix = modelo_data.get("user_latent_matrix")

    if user_latent_matrix is None:
        return recomendar_popularidad(top_n)

    if telegram_id not in user_encoder.classes_:
        return recomendar_popularidad(top_n)

    user_id = user_encoder.transform([telegram_id])[0]
    if user_id >= user_latent_matrix.shape[0]:
        return recomendar_popularidad(top_n)

    user_vector = user_latent_matrix[user_id].reshape(1, -1)

    platos_modelo = item_encoder.classes_
    recomendaciones: List[Tuple[str, float]] = []

    for plato in platos_modelo:
        try:
            item_id = item_encoder.transform([plato])[0]
            item_vector = svd.components_[:, item_id].reshape(-1, 1)
            score = np.dot(user_vector, item_vector)[0][0]
            recomendaciones.append((plato, float(score)))
        except Exception:
            continue

    pedidos_usuario = Order.objects.filter(telegram_id=telegram_id).values_list("item", flat=True)
    platos_excluir = set(pedidos_usuario)

    recomendaciones_filtradas = [
        (plato, score) for plato, score in recomendaciones
        if plato not in platos_excluir
    ]

    recomendaciones_filtradas.sort(key=lambda x: x[1], reverse=True)
    return [plato for plato, _ in recomendaciones_filtradas[:top_n]]

if __name__ == "__main__":
    clientes = Order.objects.values_list("telegram_id", flat=True).distinct()
    if not clientes:
        print("No hay clientes, probando popularidad:")
        print(recomendar_popularidad(5))
        sys.exit(0)

    for telegram_id in clientes:
        print(f"\nCliente: {telegram_id}")
        print(recomendar_ml(telegram_id, 3))
