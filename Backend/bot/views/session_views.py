import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import TelegramSession, LoyaltyPoints

logger = logging.getLogger(__name__)


@csrf_exempt
def get_or_create_session(request, telegram_id):
    session, created = TelegramSession.objects.get_or_create(telegram_id=telegram_id)
    return JsonResponse({
        "telegram_id": session.telegram_id,
        "state": session.state,
        "current_product_id": session.current_product_id,
        "temp_data": session.temp_data,
    })


@csrf_exempt
def update_session(request, telegram_id):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        session = TelegramSession.objects.get(telegram_id=telegram_id)

        if "state" in data:
            session.state = data["state"]
        if "current_product_id" in data:
            session.current_product_id = data["current_product_id"]
        if "temp_data" in data:
            current_temp = session.temp_data or {}
            current_temp.update(data["temp_data"])
            session.temp_data = current_temp

        session.save()
        return JsonResponse({"status": "ok", "state": session.state})
    except TelegramSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def reset_session(request, telegram_id):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        session = TelegramSession.objects.get(telegram_id=telegram_id)
        session.state = "IDLE"
        session.current_product_id = None
        session.temp_data = {}
        session.save()
        return JsonResponse({"status": "ok", "state": "IDLE"})
    except TelegramSession.DoesNotExist:
        return JsonResponse({"status": "ok", "state": "IDLE"})


@csrf_exempt
def get_loyalty_points(request, telegram_id):
    try:
        loyalty = LoyaltyPoints.objects.get(telegram_id=telegram_id)
        data = {
            "telegram_id": loyalty.telegram_id,
            "puntos": loyalty.puntos,
            "nivel": loyalty.nivel,
            "total_gastado": float(loyalty.total_gastado),
        }
        return JsonResponse(data)
    except LoyaltyPoints.DoesNotExist:
        return JsonResponse({"puntos": 0, "nivel": "Bronce", "total_gastado": 0.0})
