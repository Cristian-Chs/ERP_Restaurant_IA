from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
import json

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Order, Rating, GustoCliente
from .serializers import OrderSerializer
from .utils import notificar_pedido_listo
from ml.predict import recomendar_ml


# ------------------------------
# API REST (solo Orders)
# ------------------------------

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]


# ------------------------------
# Endpoints IA
# ------------------------------

def historial(request, telegram_id):
    orders = Order.objects.filter(telegram_id=telegram_id)
    ratings = Rating.objects.filter(telegram_id=telegram_id)

    data = []
    for o in orders:
        rating = ratings.filter(plato=o.item).first()
        data.append({
            "plato": o.item,
            "rating": rating.estrellas if rating else None
        })

    return JsonResponse({"historial": data})


@csrf_exempt
def guardar_rating(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    data = json.loads(request.body)
    Rating.objects.create(
        telegram_id=data["telegram_id"],
        plato=data["plato"],
        estrellas=data["rating"]
    )
    return JsonResponse({"status": "ok"})


def gustos(request, telegram_id):
    g = GustoCliente.objects.filter(telegram_id=telegram_id).first()
    return JsonResponse({"gustos": g.gustos if g else []})


def popularidad(request):
    conteo = Order.objects.values("item").annotate(total=Count("item")).order_by("-total")
    return JsonResponse({"populares": [c["item"] for c in conteo]})


def recomendacion_ml_view(request, telegram_id):
    recs = recomendar_ml(telegram_id, top_n=5)
    return JsonResponse({"recomendaciones": recs})


# ------------------------------
# Panel de cocina
# ------------------------------

def cocina_panel(request):
    pedidos = Order.objects.filter(status="pendiente")

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        order = Order.objects.get(id=order_id)
        order.status = "listo"
        order.save()

        notificar_pedido_listo(order.telegram_id, order.item)

        return redirect("cocina_panel")

    return render(request, "bot/cocina_panel.html", {"pedidos": pedidos})
