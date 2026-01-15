import imagehash
from PIL import Image
from .models import PaymentHash, Order
import pytesseract
import re

def calculate_payment_hash(image_path):
    """
    Calcula el hash perceptual (dhash) de una imagen para detectar duplicados visuales.
    """
    try:
        img = Image.open(image_path)
        # dhash es resistente a cambios de tamaño menores y ediciones ligeras
        hash_val = imagehash.dhash(img)
        return str(hash_val)
    except Exception as e:
        print(f"Error calculando hash de imagen: {e}")
        return None

def verify_payment_authenticity(order, image_path):
    """
    Realiza verificaciones de seguridad sobre el comprobante:
    1. Duplicidad (Hashing)
    2. Coincidencia de monto (OCR)
    """
    results = {
        "is_duplicate": False,
        "amount_mismatch": False,
        "ocr_amount": None,
        "duplicate_order_id": None
    }

    # 1. Verificar Duplicadod
    current_hash = calculate_payment_hash(image_path)
    if current_hash:
        order.payment_hash = current_hash
        order.save()

        # Buscar si este hash ya existe en otro pedido exitoso o pendiente
        existing = PaymentHash.objects.filter(hash_value=current_hash).exclude(order=order).first()
        if existing:
            results["is_duplicate"] = True
            results["duplicate_order_id"] = existing.order.id
        else:
            # Registrar el nuevo hash
            PaymentHash.objects.get_or_create(hash_value=current_hash, order=order)

    # 2. Verificar Monto via OCR (Opcional pero recomendado)
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        # Buscar patrones de precios (ej: 15.00, 1.500, etc)
        amounts = re.findall(r'(\d+[\.,]\d{2})', text)
        if amounts:
            # Limpiar y convertir a float para comparar
            clean_amounts = [float(a.replace(',', '.')) for a in amounts]
            results["ocr_amount"] = clean_amounts
            
            order_total = float(order.precio)
            # Verificamos si el monto del pedido aparece en el comprobante
            if not any(abs(a - order_total) < 0.1 for a in clean_amounts):
                results["amount_mismatch"] = True
    except Exception as e:
        print(f"Error en OCR: {e}. Asegurate de tener Tesseract instalado en el sistema.")

    return results
