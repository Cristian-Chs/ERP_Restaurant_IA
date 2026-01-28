"""
Order Service
Lógica de negocio para creación y gestión de pedidos.
"""
import logging
import requests
from ..config import ORDERS_URL, PRODUCTOS_URL
from asgiref.sync import sync_to_async
from core.models import Ingredient
from rapidfuzz import process, fuzz
from bot_Cliente.utils.text_utils import clean_order_text, extraer_cantidad_y_producto
from bot_Cliente.utils.fuzzy_matching import extraer_ingredientes_removidos, extraer_ingredientes_agregados


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
    
    # 0. Condimentos comunes (siempre disponibles para quitar/poner)
    COMMON_CONDIMENTS = [
        "sal", "pimienta", "azucar", "salsa", "ketchup", "mayonesa", 
        "mostaza", "tomate", "cebolla", "lechuga", "hielo", "limon"
    ]
    ingredientes_finales.extend(COMMON_CONDIMENTS)

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


def extraer_producto_base(texto_usuario: str) -> str | None:
    """Detecta el producto base usando fuzzy matching contra el backend."""
    try:
        r = requests.get(PRODUCTOS_URL, timeout=5)
        if r.status_code != 200:
            return None
            
        productos = r.json().get("productos", [])
        # Normalizar
        productos = [p.strip().lower() for p in productos]
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        return None

    if not productos:
        return None

    texto = texto_usuario.lower()

    # Buscar coincidencia difusa
    result = process.extractOne(
        texto,
        productos,
        scorer=fuzz.token_set_ratio
    )
    
    if result is None:
        return None
    
    mejor_match, score, _ = result

    # Umbral mínimo
    if score >= 70:
        return mejor_match
        
    return None


async def interpretar_pedido(texto_usuario: str) -> dict:
    """
    Analiza el texto del usuario y devuelve una estructura de pedido.
    """
    # 1. Limpieza inicial
    texto_limpio = clean_order_text(texto_usuario)
    
    # 2. Extraer cantidad y texto restante
    cantidad, texto_sin_cantidad = extraer_cantidad_y_producto(texto_limpio)
    
    # Si no se especificó cantidad, asumimos 1
    cantidad_final = cantidad if cantidad is not None else 1
    
    # 3. Detectar producto base
    producto_base = extraer_producto_base(texto_sin_cantidad)
    
    if not producto_base:
        return {
            "producto": None,
            "cantidad": cantidad_final,
            "es_pedido_valido": False
        }

    # 4. Obtener ingredientes
    ingredientes_menu = await obtener_ingredientes_producto(producto_base)

    removidos = extraer_ingredientes_removidos(texto_sin_cantidad, ingredientes_menu)
    agregados = extraer_ingredientes_agregados(texto_sin_cantidad, ingredientes_menu)

    # 5. Construir string final
    pedido_str = producto_base.title()
    
    modificaciones = []
    if removidos:
        modificaciones.append(f"sin {', '.join(removidos)}")
    if agregados:
        modificaciones.append(f"con {', '.join(agregados)}")
        
    if modificaciones:
        pedido_str += f" ({', '.join(modificaciones)})"
    
    pedido_final = f"{cantidad_final} x {pedido_str}"

    return {
        "producto": producto_base,
        "cantidad": cantidad_final,
        "removidos": removidos,
        "agregados": agregados,
        "pedido_final": pedido_final,
        "es_pedido_valido": True
    }
