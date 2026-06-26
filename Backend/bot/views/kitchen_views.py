import re
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import Order
from ..inventory_service import deduct_inventory_for_order

logger = logging.getLogger(__name__)


def api_cocina_orders(request):
    pedidos = Order.objects.filter(
        status__in=["pendiente", "esperando_pago", "fraude_sospecha"]
    ).order_by("fecha")

    data = [
        {
            "id": p.id,
            "telegram_id": p.telegram_id,
            "item": p.item,
            "precio": float(p.precio),
            "fecha": p.fecha.isoformat(),
            "status": p.status,
            "payment_status": p.payment_status,
            "service_type": p.service_type,
            "service_type_display": p.get_service_type_display(),
            "delivery_mode": p.get_delivery_mode_display() if p.delivery_mode else "N/A",
            "location": p.location or "N/A",
            "payment_proof": p.payment_proof.url if p.payment_proof else None,
            "currency": p.currency,
            "exchange_rate": float(p.exchange_rate),
            "payment_data": p.payment_data,
        }
        for p in pedidos
    ]
    return JsonResponse(data, safe=False)


@csrf_exempt
def api_cocina_payments_all(request):
    pedidos = Order.objects.exclude(payment_status='pending_payment').order_by("-fecha")

    data = []
    for p in pedidos:
        is_suspicious = False
        fraud_reason = ""

        if p.status == 'fraude_sospecha':
            is_suspicious = True
            fraud_reason = p.payment_data.get("fraud_error", "Detección de duplicado")

        if p.payment_data and "monto" in p.payment_data:
            try:
                ocr_monto_str = str(p.payment_data.get("monto", "0")).replace(".", "").replace(",", ".")
                ocr_monto = float(re.search(r'[\d\.]+', ocr_monto_str).group())
                diff = abs(ocr_monto - float(p.precio))
                if diff > 0.05:
                    is_suspicious = True
                    fraud_reason = f"Monto OCR (${ocr_monto}) no coincide con precio (${p.precio})"
            except Exception:
                pass

        data.append({
            "id": p.id,
            "telegram_id": p.telegram_id,
            "item": p.item,
            "precio": float(p.precio),
            "fecha": p.fecha.isoformat(),
            "status": p.status,
            "payment_status": p.payment_status,
            "payment_proof": p.payment_proof.url if p.payment_proof else None,
            "currency": p.currency,
            "is_suspicious": is_suspicious,
            "fraud_reason": fraud_reason,
            "payment_data": p.payment_data,
        })

    return JsonResponse(data, safe=False)


@csrf_exempt
def api_cocina_approve_payment(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        order = Order.objects.get(id=order_id)
        order.payment_status = 'payment_approved'
        order.status = 'pendiente'

        invoice_path = None
        try:
            from ..factura import InvoiceGenerator
            generator = InvoiceGenerator()
            invoice_path = generator.generate(order)
            order.invoice_path = invoice_path
            logger.info(f"Factura generada: {invoice_path}")
        except Exception as e:
            logger.error(f"Error generando factura: {e}")

        order.save()
        deduct_inventory_for_order(order)

        from ..utils import notificar_pago_aprobado
        notificar_pago_aprobado(order.telegram_id, order.id, invoice_path)

        return JsonResponse({"status": "ok", "invoice_generated": invoice_path is not None})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)
    except Exception as e:
        logger.error(f"Error en api_cocina_approve_payment: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_cocina_reject_payment(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        order = Order.objects.get(id=order_id)
        order.payment_status = 'payment_rejected'
        order.status = 'rechazado'
        order.save()

        from ..utils import notificar_pago_rechazado
        notificar_pago_rechazado(order.telegram_id, order.id)

        return JsonResponse({"status": "ok"})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)


@csrf_exempt
def api_cocina_mark_ready(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        order = Order.objects.get(id=order_id)
        order.status = "listo"
        order.save()
        return JsonResponse({"status": "ok"})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_cocina_reject(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        order = Order.objects.get(id=order_id)
        order.status = "rechazado"
        order.save()
        return JsonResponse({"status": "ok"})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_get_invoice(request, order_id):
    try:
        from django.http import FileResponse
        import os

        order = Order.objects.get(id=order_id)

        if not order.invoice_path or not os.path.exists(order.invoice_path):
            return JsonResponse({"error": "Factura no encontrada"}, status=404)

        return FileResponse(open(order.invoice_path, 'rb'), content_type='image/jpeg')

    except Order.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)
    except Exception as e:
        logger.error(f"Error sirviendo factura: {e}")
        return JsonResponse({"error": str(e)}, status=500)
