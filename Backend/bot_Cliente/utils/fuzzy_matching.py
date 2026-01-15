"""
Fuzzy Matching para ingredientes y productos
Usa RapidFuzz para encontrar coincidencias aproximadas.
"""
from rapidfuzz import process, fuzz


def fuzzy_match_ingrediente(texto: str, ingredientes_menu: list[str], threshold: int = 70) -> str | None:
    """
    Devuelve el ingrediente más parecido dentro del texto.
    
    Args:
        texto: Texto del usuario
        ingredientes_menu: Lista de ingredientes válidos
        threshold: Umbral mínimo de similitud (0-100)
    
    Returns:
        Ingrediente encontrado o None
    """
    if not ingredientes_menu:
        return None
    
    texto = texto.lower()

    result = process.extractOne(
        texto,
        ingredientes_menu,
        scorer=fuzz.token_set_ratio
    )
    
    # process.extractOne puede devolver None si no hay coincidencias
    if result is None:
        return None
    
    mejor_match, score, _ = result

    if score >= threshold:
        return mejor_match

    return None


def extraer_ingredientes_removidos(texto: str, ingredientes_menu: list[str]) -> list[str]:
    """
    Detecta ingredientes que el usuario quiere remover.
    
    Args:
        texto: Texto del pedido
        ingredientes_menu: Lista de ingredientes disponibles
    
    Returns:
        Lista de ingredientes a remover
    """
    from bot_Cliente.config import INGREDIENTES_REMOVIDOS_KEYWORDS
    
    texto = texto.lower()
    removidos = []

    for kw in INGREDIENTES_REMOVIDOS_KEYWORDS:
        if kw in texto:
            # Extraemos la parte después del keyword
            parte = texto.split(kw, 1)[-1]

            # Intentamos detectar cada ingrediente usando fuzzy matching
            match = fuzzy_match_ingrediente(parte, ingredientes_menu)
            if match and match not in removidos:
                removidos.append(match)

    return removidos


def extraer_ingredientes_agregados(texto: str, ingredientes_menu: list[str]) -> list[str]:
    """
    Detecta ingredientes que el usuario quiere agregar.
    
    Args:
        texto: Texto del pedido
        ingredientes_menu: Lista de ingredientes disponibles
    
    Returns:
        Lista de ingredientes a agregar
    """
    from bot_Cliente.config import INGREDIENTES_AGREGADOS_KEYWORDS
    
    texto = texto.lower()
    agregados = []

    for kw in INGREDIENTES_AGREGADOS_KEYWORDS:
        if kw in texto:
            parte = texto.split(kw, 1)[-1]

            # Intentamos detectar cada ingrediente usando fuzzy matching
            match = fuzzy_match_ingrediente(parte, ingredientes_menu)
            if match and match not in agregados:
                agregados.append(match)

    return agregados
