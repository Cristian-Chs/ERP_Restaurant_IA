import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg as AvgModel
from ..models import Order, Rating, GustoCliente, PedidoPersonalizado
from core.models import Product

logger = logging.getLogger(__name__)


def historial(request, telegram_id):
    ratings = Rating.objects.filter(telegram_id=telegram_id).order_by("-estrellas")
    data = [{"plato": r.plato, "rating": r.estrellas} for r in ratings]
    return JsonResponse({"historial": data})


@csrf_exempt
def guardar_rating(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    data = json.loads(request.body)
    comentario = data.get("comentario", "")

    from ..sentiment import analizar_sentimiento_groq
    sentimiento = analizar_sentimiento_groq(comentario) if comentario else "Neutral"

    Rating.objects.create(
        telegram_id=data["telegram_id"],
        plato=data["plato"],
        estrellas=data["rating"],
        comentario=comentario,
        sentimiento=sentimiento,
    )

    return JsonResponse({"status": "ok"})


def gustos(request, telegram_id):
    g = GustoCliente.objects.filter(telegram_id=telegram_id).first()
    if not g:
        return JsonResponse({"gustos": []})

    if isinstance(g.gustos, str):
        lista = [x.strip() for x in g.gustos.split(",") if x.strip()]
    else:
        lista = g.gustos

    return JsonResponse({"gustos": lista})


def popularidad(request):
    conteo = (
        Order.objects.values("item")
        .annotate(total=Count("item"))
        .order_by("-total")
    )
    populares = [c["item"] for c in conteo]
    return JsonResponse({"populares": populares})


def recomendacion_ml_view(request, telegram_id):
    try:
        from ml.predict import recomendar_ml
        recs = recomendar_ml(telegram_id, top_n=5)
    except Exception as e:
        logger.error(f"Error loading ML model: {e}")
        recs = []
    return JsonResponse({"recomendaciones": recs})


def recomendacion_similar_view(request, telegram_id):
    try:
        from ml.embeddings import recomendar_similares
    except ImportError:
        return JsonResponse({"similares": [], "error": "ML module missing"})

    ultimo = Rating.objects.filter(telegram_id=telegram_id).order_by("-id").first()
    if not ultimo:
        return JsonResponse({"similares": []})

    plato_objetivo = ultimo.plato
    platos = list(Product.objects.values_list("name", flat=True))

    try:
        similares = recomendar_similares(plato_objetivo, platos, top_n=5)
    except Exception as e:
        logger.error(f"Error in similar recommendation: {e}")
        similares = []

    return JsonResponse({"plato_base": plato_objetivo, "similares": similares})


def recomendacion_hibrida_view(request, telegram_id):
    top_personal = list(
        Order.objects.filter(telegram_id=telegram_id)
        .values("item")
        .annotate(total=Count("id"))
        .order_by("-total")
        .values_list("item", flat=True)[:3]
    )

    top_global = list(
        Order.objects.values("item")
        .annotate(total=Count("id"))
        .order_by("-total")
        .values_list("item", flat=True)[:3]
    )

    top_rated = list(
        Rating.objects.values("plato")
        .annotate(avg_stars=AvgModel("estrellas"))
        .order_by("-avg_stars")
        .values_list("plato", flat=True)[:3]
    )

    recomendacion_final = []

    if top_personal:
        recomendacion_final.extend(top_personal[:2])
        for p in top_global:
            if p not in recomendacion_final:
                recomendacion_final.append(p)
                break
        for p in top_rated:
            if p not in recomendacion_final:
                recomendacion_final.append(p)
                break
    else:
        recomendacion_final.extend(top_global[:3])
        for p in top_rated:
            if p not in recomendacion_final:
                recomendacion_final.append(p)

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
            "rated": top_rated,
        },
    })


@csrf_exempt
def guardar_pedido_personalizado(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    data = json.loads(request.body)
    PedidoPersonalizado.objects.create(
        telegram_id=data.get("telegram_id"),
        producto=data.get("producto"),
        removidos=data.get("removidos", []),
        agregados=data.get("agregados", []),
        pedido_final=data.get("pedido_final", ""),
    )

    return JsonResponse({"status": "ok"})
