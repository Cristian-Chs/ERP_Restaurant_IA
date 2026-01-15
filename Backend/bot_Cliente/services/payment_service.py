"""
Payment Service
Procesamiento de pagos y OCR de comprobantes.
"""
import logging
import requests
from rapidfuzz import process
from ..config import OCR_API_URL, OCR_API_KEY, BANCOS
from ..utils.text_utils import (
    extraer_referencia,
    extraer_fecha,
    extraer_monto,
    extraer_telefono,
    extraer_tipo_operacion
)


def extraer_banco(text: str) -> str:
    """
    Detecta el banco usando fuzzy matching.
    
    Args:
        text: Texto del comprobante
    
    Returns:
        Nombre del banco o "N/A"
    """
    banco, score, _ = process.extractOne(text, BANCOS)
    return banco if score > 70 else "N/A"


async def extraer_datos_comprobante(file_path: str) -> dict:
    """
    Extrae datos de un comprobante de pago usando OCR.
    
    Args:
        file_path: Ruta al archivo de imagen
    
    Returns:
        Dict con datos extraídos o error
    """
    try:
        with open(file_path, 'rb') as f:
            payload = {
                'apikey': OCR_API_KEY,
                'language': 'spa',
                'isOverlayRequired': False,
                'OCREngine': '2'
            }
            response = requests.post(OCR_API_URL, files={'file': f}, data=payload)
            result = response.json()

        if result.get("IsErroredOnProcessing"):
            return {"error": result.get("ErrorMessage", "Error en OCR")}

        text = result['ParsedResults'][0]['ParsedText']

        data = {
            "numero_referencia": extraer_referencia(text),
            "fecha": extraer_fecha(text),
            "monto": extraer_monto(text),
            "banco_emisor": extraer_banco(text),
            "banco_receptor": extraer_banco(text),
            "telefono_origen": extraer_telefono(text),
            "telefono_destino": extraer_telefono(text),
            "tipo_operacion": extraer_tipo_operacion(text),
        }

        return data

    except Exception as e:
        logging.error(f"Error en OCR: {e}")
        return {"error": str(e)}
