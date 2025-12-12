from rest_framework.response import Response
from rest_framework.decorators import api_view
from .utils import recomendar_por_cliente

@api_view(["GET"])
def recomendaciones_cliente(request, telegram_id):
    recomendados = recomendar_por_cliente(telegram_id)
    return Response({"telegram_id": telegram_id, "recomendados": recomendados})

from rest_framework.response import Response
from rest_framework.decorators import api_view
from .utils import recomendar_ml

@api_view(["GET"])
def recomendaciones_cliente(request, telegram_id):
    recomendados = recomendar_ml(telegram_id)
    return Response({"telegram_id": telegram_id, "recomendados": recomendados})

from django.http import JsonResponse
from .utils import recomendar_ml

def recomendaciones_cliente(request, telegram_id):
    recomendaciones = recomendar_ml(telegram_id)
    return JsonResponse({
        "telegram_id": telegram_id,
        "recomendaciones": recomendaciones
    })
