"""
Order Service
Lógica de negocio para creación y gestión de pedidos.
"""
import logging
import requests
from ..config import ORDERS_URL, PRODUCTOS_URL
from asgiref.sync import sync_to_async
from core.models import Ingredient


def save_order(telegram_id: int, item: str) -> bool:
    """
    Guarda un pedido en el backend Django.
    
    Args:
        telegram_id: ID de Telegram del cliente
        item: Descripción del pedido
    
    Returns:
        True si se guardó exitosamente
    """
    data = {"telegram_id": telegram_id, "item": item, "status": "pendiente"}
    try:
        response = requests.post(ORDERS_URL, json=data, timeout=8)
        return response.status_code in (200, 201)
    except Exception as e:
        logging.error(f"[ERROR] No se pudo conectar al backend: {e}")
        return False


async def obtener_ingredientes_producto(producto_base: str) -> list[str]:
    """
    Obtiene la lista de ingredientes de un producto.
    
    Args:
        producto_base: Nombre del producto
    
    Returns:
        Lista de nombres de ingredientes (lowercase)
    """
    ingredientes_finales = []

    # 1. Ingredientes del plato desde el backend
    try:
        r = requests.get(f"{PRODUCTOS_URL}?detalle={producto_base}", timeout=5)
        data = r.json()
        ingredientes_plato = data.get("ingredientes", [])
    except Exception as e:
        print("ERROR obteniendo ingredientes del plato:", e)
        ingredientes_plato = []

    # Normalizar
    for ing in ingredientes_plato:
        if isinstance(ing, dict):
            ingredientes_finales.append(ing.get("nombre", "").lower())
        else:
            ingredientes_finales.append(str(ing).lower())

    # 2. Ingredientes globales extra desde Django ORM (async-safe)
    try:
        extras = await sync_to_async(list)(
            Ingredient.objects.filter(disponible_como_extra=True).values_list("nombre", flat=True)
        )
        for ing in extras:
            ing = ing.strip().lower()
            if ing not in ingredientes_finales:
                ingredientes_finales.append(ing)
    except Exception as e:
        print("ERROR obteniendo ingredientes extra:", e)

    print("DEBUG ingredientes_finales:", ingredientes_finales)
    return ingredientes_finales
