"""
Order Service
Lógica de negocio para creación y gestión de pedidos.
"""
import logging
import requests
import re
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
    Analiza el texto del usuario y devuelve múltiples productos usando fuzzy matching.
    
    Returns:
        {
            "es_pedido_valido": bool,
            "items": [
                {"producto": str, "cantidad": int, "precio": float},
                ...
            ],
            "total": float,
            "pedido_final": str
        }
    """
    # 1. Obtener todos los productos del menú
    try:
        r = requests.get(PRODUCTOS_URL, timeout=5)
        if r.status_code != 200:
            return {"es_pedido_valido": False, "items": [], "total": 0, "pedido_final": ""}
        
        productos_data = r.json().get("productos_detalle", [])
        if not productos_data:
            return {"es_pedido_valido": False, "items": [], "total": 0, "pedido_final": ""}
            
        # Crear diccionario {nombre_lower: info} para búsqueda rápida
        productos_map = {p["nombre"].lower(): p for p in productos_data}
        nombres_productos = list(productos_map.keys())
            
    except Exception as e:
        print(f"Error fetching products: {e}")
        return {"es_pedido_valido": False, "items": [], "total": 0, "pedido_final": ""}
    
    # 2. Dividir el texto en segmentos (por comas y conjunciones)
    # Reemplazar ' y ', ' e ' por comas para facilitar split
    texto_seg = re.sub(r' (y|e) ', ',', texto_usuario, flags=re.IGNORECASE)
    segmentos = [s.strip() for s in texto_seg.split(',')]
    
    items_detectados = []
    
    for segmento in segmentos:
        if not segmento:
            continue
            
        # Limpiar segmento y extraer cantidad
        segmento_limpio = clean_order_text(segmento)
        cantidad, producto_texto = extraer_cantidad_y_producto(segmento_limpio)
        
        # Default quantity to 1 if not detected (e.g. "una" removed or implicit)
        if cantidad is None:
            cantidad = 1
        
        if not producto_texto:
            continue

            
        # Fuzzy Match contra nombres de productos
        match = process.extractOne(
            producto_texto.lower(), 
            nombres_productos, 
            scorer=fuzz.token_set_ratio
        )
        
        if match:
            nombre_match, score, _ = match
            
            # Umbral de confianza
            if score >= 80:
                producto_info = productos_map[nombre_match]
                precio = float(producto_info.get("precio", 0))
                
                # Verificar si ya detectamos este producto (sumar cantidad)
                existente = next((i for i in items_detectados if i["producto"] == producto_info["nombre"]), None)
                
                if existente:
                    existente["cantidad"] += cantidad
                    existente["precio"] = existente["cantidad"] * precio
                else:
                    items_detectados.append({
                        "id": producto_info.get("id"),
                        "producto": producto_info.get("nombre"), 
                        "cantidad": cantidad,
                        "precio": precio * cantidad
                    })
    
    # 4. Si no se detectó nada, retornar inválido
    if not items_detectados:
        return {"es_pedido_valido": False, "items": [], "total": 0, "pedido_final": ""}
    
    # 5. Calcular total
    total = sum(item["precio"] for item in items_detectados)
    
    # 6. Crear string concatenado
    pedido_parts = [f"{item['cantidad']} x {item['producto']}" for item in items_detectados]
    pedido_final = ", ".join(pedido_parts)
    
    return {
        "es_pedido_valido": True,
        "items": items_detectados,
        "total": total,
        "pedido_final": pedido_final
    }

