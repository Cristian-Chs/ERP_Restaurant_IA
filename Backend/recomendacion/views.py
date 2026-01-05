from django.http import JsonResponse
from .utils import recomendar_ml

def recomendaciones_cliente(request, telegram_id):
    recomendaciones = recomendar_ml(telegram_id)
    return JsonResponse({
        "telegram_id": telegram_id,
        "recomendaciones": recomendaciones
    })
