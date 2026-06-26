"""
Utilidades para procesamiento de texto
Funciones para limpiar, parsear y extraer información de texto de usuarios.
"""
import re


def extraer_cantidad_y_producto(texto: str) -> tuple[int | None, str]:
    """
    Extrae la cantidad y el nombre del producto del texto del usuario.
    
    Args:
        texto: Texto del usuario (ej: "2 hamburguesas", "tres pizzas")
    
    Returns:
        Tupla (cantidad, producto_texto)
    """
    texto = texto.strip()
    
    # 1. Regex para detectar números al inicio (ej: "2 hamburguesas", "3x pizza")
    match_numero = re.search(r'^(\d+)\s*(?:x\s*)?', texto, re.IGNORECASE)
    if match_numero:
        cantidad = int(match_numero.group(1))
        producto = texto[match_numero.end():].strip()
        return cantidad, producto
    
    # 2. Regex para palabras de cantidad (básico)
    mapa_numeros = {
        "una": 1, "un": 1, "uno": 1,
        "dos": 2, "dós": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6
    }
    
    palabras = texto.split(" ", 1)
    primera_palabra = palabras[0].lower()
    
    if primera_palabra in mapa_numeros:
        cantidad = mapa_numeros[primera_palabra]
        producto = palabras[1].strip() if len(palabras) > 1 else ""
        return cantidad, producto
        
    return None, texto


def parsear_resumen_web(texto: str) -> dict | None:
    """
    Intenta parsear un resumen de pedido pegado desde la web.
    
    Args:
        texto: Texto del resumen del pedido
    
    Returns:
        Dict con producto_base, pedido_final, precio, etc. o None si no es válido
    """
    # Detectar encabezados válidos
    es_nuevo_formato = "NUEVO PEDIDO CONFIRMADO" in texto
    es_formato_antiguo = "Resumen del Pedido" in texto or "TOTAL FINAL" in texto

    if not es_nuevo_formato and not es_formato_antiguo:
        return None

    # 1. Extraer items:  1. *Nombre* (Cant x $Precio)
    items_found = re.findall(r'\d+\.\s*\*(.+?)\*\s*\((\d+)\s*x', texto)
    
    if not items_found:
        return None

    partes_pedido = []
    for nombre, cant in items_found:
        partes_pedido.append(f"{cant} x {nombre}")
    
    pedido_final_str = ", ".join(partes_pedido)

    # 2. Extraer Total
    match_total = re.search(r'(?:TOTAL FINAL:|TOTAL:)\s*\$([\d\.]+)', texto, re.IGNORECASE)
    precio_total = float(match_total.group(1)) if match_total else 0.0

    # 3. Extraer Servicio y Modalidad (Nuevo Formato)
    service_type = 'AQUI'
    delivery_mode = None
    if "*Servicio:*" in texto:
        if "Comer Aquí" in texto: service_type = 'AQUI'
        if "Para Llevar" in texto: service_type = 'LLEVAR'
    
    if "*Modalidad:*" in texto:
        if "Retiro en Local" in texto: delivery_mode = 'RETIRO'
        if "Delivery" in texto: delivery_mode = 'DELIVERY'

    return {
        "producto_base": "Pedido Web",
        "pedido_final": pedido_final_str,
        "texto_original": texto,
        "precio": precio_total,
        "service_type": service_type,
        "delivery_mode": delivery_mode
    }


def clean_order_text(text: str) -> str:
    """
    Limpia el texto del pedido eliminando frases comunes.
    
    Args:
        text: Texto original del usuario
    
    Returns:
        Texto limpio sin frases de cortesía
    """
    # Eliminar frases comunes (Case Insensitive)
    # Orden importa: frases largas primero
    frases = [
        "quiero pedir", "me gustaría ordenar", "por favor confirma", "hay disponible",
        "quiero una", "quiero un", "dame una", "dame un",
        "quisiera una", "quisiera un", "me gustaría una", "me gustaría un",
        "me gustaria", "quisiera", "ordenar", "pedir",
        "quiero", "dame", "por favor", "necesito",
        "ordenas", "tienes", "tendras", "me das", "me da", "disponible",
        "mejor", "solo", "solamente", "cambia a", "cambiar a", "son", "serian"
    ]
    
    cleaned_text = text
    for frase in frases:
        cleaned_text = re.sub(frase, "", cleaned_text, flags=re.IGNORECASE)
        
    # Eliminar símbolos y espacios extra
    cleaned_text = cleaned_text.replace("*", "").replace("-", "").strip()
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Colapsar espacios
    
    return cleaned_text


def extraer_referencia(text: str) -> str:
    """Extrae número de referencia de comprobante (8-12 dígitos)"""
    match = re.search(r'\b\d{8,12}\b', text)
    return match.group() if match else "N/A"


def extraer_fecha(text: str) -> str:
    """Extrae fecha del comprobante (formato DD/MM/YYYY o DD-MM-YYYY)"""
    match = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', text)
    return match.group() if match else "N/A"


def extraer_monto(text: str) -> str:
    """Extrae monto del comprobante"""
    match = re.search(r'(\d+[.,]\d{2})', text)
    return match.group() if match else "N/A"


def extraer_telefono(text: str) -> str:
    """Extrae número de teléfono venezolano (04XXXXXXXXX)"""
    match = re.search(r'\b(04\d{9})\b', text)
    return match.group() if match else "N/A"


def extraer_tipo_operacion(text: str) -> str:
    """Detecta el tipo de operación bancaria"""
    text_lower = text.lower()
    if "pago móvil" in text_lower:
        return "Pago Móvil"
    elif "transferencia" in text_lower:
        return "Transferencia"
    elif "depósito" in text_lower:
        return "Depósito"
    else:
        return "N/A"
