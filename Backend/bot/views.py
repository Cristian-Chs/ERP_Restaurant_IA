from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg
from django.db import models
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
# Endpoints IA (CORREGIDOS)
# ------------------------------

def historial(request, telegram_id):
    """
    Devuelve historial ordenado por rating (solo platos con rating).
    """
    ratings = Rating.objects.filter(telegram_id=telegram_id).order_by("-estrellas")

    data = [
        {"plato": r.plato, "rating": r.estrellas}
        for r in ratings
    ]

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
    """
    Devuelve gustos como lista, no como string.
    """
    g = GustoCliente.objects.filter(telegram_id=telegram_id).first()

    if not g:
        return JsonResponse({"gustos": []})

    # Si está guardado como string: "Pizza,Pasta"
    if isinstance(g.gustos, str):
        lista = [x.strip() for x in g.gustos.split(",") if x.strip()]
    else:
        lista = g.gustos

    return JsonResponse({"gustos": lista})


def popularidad(request):
    """
    Devuelve platos más pedidos, sin duplicados.
    """
    conteo = (
        Order.objects.values("item")
        .annotate(total=Count("item"))
        .order_by("-total")
    )

    populares = [c["item"] for c in conteo]

    return JsonResponse({"populares": populares})


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

from ml.embeddings import recomendar_similares
from core.models import Product

def recomendacion_similar_view(request, telegram_id):
    # ✅ Obtener último plato del usuario
    ultimo = Rating.objects.filter(telegram_id=telegram_id).order_by("-id").first()

    if not ultimo:
        return JsonResponse({"similares": []})

    plato_objetivo = ultimo.plato

    # ✅ Obtener todos los platos del menú (campo correcto: name)
    platos = list(Product.objects.values_list("name", flat=True))

    # ✅ Calcular similares
    similares = recomendar_similares(plato_objetivo, platos, top_n=5)

    return JsonResponse({
        "plato_base": plato_objetivo,
        "similares": similares
    })

from ml.embeddings import recomendar_similares
from ml.predict import recomendar_ml
from core.models import Product

def recomendacion_hibrida_view(request, telegram_id):
    # ✅ 1. Top Personal (Lo que más pide el usuario)
    top_personal = list(
        Order.objects.filter(telegram_id=telegram_id)
        .values("item")
        .annotate(total=Count("id"))
        .order_by("-total")
        .values_list("item", flat=True)[:3]  # Top 3 personales
    )

    # ✅ 2. Top Global (Más populares en general)
    top_global = list(
        Order.objects.values("item")
        .annotate(total=Count("id"))
        .order_by("-total")
        .values_list("item", flat=True)[:3]  # Top 3 globales
    )

    # ✅ 3. Top Rated (Mejor calificados)
    top_rated = list(
        Rating.objects.values("plato")
        .annotate(avg_stars=models.Avg("estrellas")) # Necesitamos importar Avg si no está
        .order_by("-avg_stars")
        .values_list("plato", flat=True)[:3]
    )

    # ✅ 4. Mezcla Inteligente
    recomendacion_final = []

    # Si es cliente habitual (tiene historial), priorizamos sus gustos
    if top_personal:
        # 60% Personal (2 platos)
        recomendacion_final.extend(top_personal[:2])
        # 40% Tendencias (1 popular + 1 rating)
        for p in top_global:
            if p not in recomendacion_final:
                recomendacion_final.append(p)
                break 
        for p in top_rated:
            if p not in recomendacion_final:
                recomendacion_final.append(p)
                break
    else:
        # Si es cliente nuevo, full tendencias
        recomendacion_final.extend(top_global[:3])
        for p in top_rated:
            if p not in recomendacion_final:
                recomendacion_final.append(p)
    
    # Limpiar duplicados y limitar a 5
    resultado = []
    seen = set()
    for p in recomendacion_final:
        if p not in seen:
            resultado.append(p)
            seen.add(p)
    
    return JsonResponse({
        "recomendaciones": resultado[:5],
        "fuentes": {
            "personal": top_personal,
            "global": top_global,
            "rated": top_rated
        }
    })

from .models import PedidoPersonalizado

@csrf_exempt
def guardar_pedido_personalizado(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    data = json.loads(request.body)

    telegram_id = data.get("telegram_id")
    producto = data.get("producto")
    removidos = data.get("removidos", [])
    agregados = data.get("agregados", [])
    pedido_final = data.get("pedido_final", "")

    PedidoPersonalizado.objects.create(
        telegram_id=telegram_id,
        producto=producto,
        removidos=removidos,
        agregados=agregados,
        pedido_final=pedido_final
    )

    return JsonResponse({"status": "ok"})
