import re
from rapidfuzz import process, fuzz

# --- MOCK DATA ---
PRODUCTOS = [
    "Empanada", "Empanada de Carne", "Empanada de Pollo", "Empanada de Queso",
    "Agua", "Agua Mineral", "Refresco", "Coca Cola", "Pepsi"
]
PRODUCTOS_DATA = [
    {"nombre": p, "precio": 1.5 if "Empanada" in p else 1.0, "id": i} for i, p in enumerate(PRODUCTOS)
]
PRODUCTOS_MAP = {p["nombre"].lower(): p for p in PRODUCTOS_DATA}
NOMBRES_PRODUCTOS = list(PRODUCTOS_MAP.keys())

# --- COPIED LOGIC FROM text_utils.py ---

def clean_order_text(text: str) -> str:
    # Eliminar frases comunes (Case Insensitive)
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
        
    cleaned_text = cleaned_text.replace("*", "").replace("-", "").strip()
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text

def extraer_cantidad_y_producto(texto: str) -> tuple[int | None, str]:
    texto = texto.strip()
    match_numero = re.search(r'^(\d+)\s*(?:x\s*)?', texto, re.IGNORECASE)
    if match_numero:
        cantidad = int(match_numero.group(1))
        producto = texto[match_numero.end():].strip()
        return cantidad, producto
    
    mapa_numeros = {
        "una": 1, "un": 1, "uno": 1,
        "dos": 2, "dós": 2, "tres": 3,
        "cuatro": 4, "cinco": 5, "seis": 6
    }
    
    palabras = texto.split(" ", 1)
    primera_palabra = palabras[0].lower()
    
    if primera_palabra in mapa_numeros:
        cantidad = mapa_numeros[primera_palabra]
        producto = palabras[1].strip() if len(palabras) > 1 else ""
        return cantidad, producto
        
    return None, texto

# --- COPIED LOGIC FROM order_service.py ---

def interpretar_pedido(texto_usuario: str):
    # 2. Dividir el texto en segmentos
    texto_seg = re.sub(r' (y|e) ', ',', texto_usuario, flags=re.IGNORECASE)
    segmentos = [s.strip() for s in texto_seg.split(',')]
    
    print(f"DEBUG: Segmentos raw: {segmentos}")
    
    items_detectados = []
    
    for segmento in segmentos:
        if not segmento:
            continue
            
        # BUG SUSPECT: `extraer_cantidad_y_producto` doesn't clean the text, 
        # but `extractOne` might struggle if there is garbage.
        # Let's see what happens.
        
        # Limpiar segmento? logic inside `interpretar` didn't call `clean_order_text` in the file view I saw earlier! 
        # Wait, I need to check if `interpretar_pedido` calls `clean_order_text`.
        # Taking a look at `view_file` output Step 21...
        # Line 12: `from bot_Cliente.utils.text_utils import clean_order_text, extraer_cantidad_y_producto`
        # Line 161 (approx): It does NOT call `clean_order_text` on the full string or segments!
        
        cantidad, producto_texto = extraer_cantidad_y_producto(segmento)
        print(f"DEBUG: Parsed segment '{segmento}' -> Qty: {cantidad}, Prod: '{producto_texto}'")
        
        if not producto_texto:
            continue
            
        # Fuzzy Match
        match = process.extractOne(
            producto_texto.lower(), 
            NOMBRES_PRODUCTOS, 
            scorer=fuzz.token_set_ratio
        )
        
        print(f"DEBUG: Fuzzy Match for '{producto_texto}' -> {match}")
        
        if match:
            nombre_match, score, _ = match
            if score >= 80:
                print(f"  -> MATCHED: {nombre_match} (Score: {score})")
                items_detectados.append(nombre_match)
    
    return items_detectados

# --- RUN TEST ---
test_input = "Dame una empanada y una agua mineral"
print(f"\n--- Testing: '{test_input}' ---")
resultado = interpretar_pedido(test_input)
print(f"Resultado final: {resultado}")
