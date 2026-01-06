from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg
from django.db import models
import json

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Order, Rating, GustoCliente
from core.models import Product
from .serializers import OrderSerializer
from .utils import notificar_pedido_listo, notificar_nuevo_pedido_externo
from ml.predict import recomendar_ml


# ------------------------------
# API REST (solo Orders)
# ------------------------------

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Guardar la orden
        order = serializer.save()
        
        # ✅ Si el pedido trae una imagen de comprobante (subida desde Web)
        if order.payment_proof:
            order.payment_status = 'payment_submitted'
            order.save()
            
            # Notificar al Administrador/Chef inmediatamente
            try:
                notificar_nuevo_pedido_externo(order)
                print(f"DEBUG [OrderViewSet] Notificación enviada para pedido web {order.id}")
            except Exception as e:
                print(f"Error notificando pedido web: {e}")
        
        # ⚠️ Lógica antigua para otros casos (si aplica)
        elif order.service_type != 'HERE' and order.status not in ['pendiente', 'esperando_pago']:
            try:
                notificar_nuevo_pedido_externo(order)
            except Exception as e:
                print(f"Error notificando pedido externo: {e}")


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
    try:
        from ml.predict import recomendar_ml
        recs = recomendar_ml(telegram_id, top_n=5)
    except Exception as e:
        print(f"Error loading ML model: {e}")
        recs = [] # Fallback
    return JsonResponse({"recomendaciones": recs})



# ------------------------------
# Panel de cocina
# ------------------------------

# ------------------------------
# API Cocina (REACT)
# ------------------------------

def api_cocina_orders(request):
    """
    Devuelve pedidos para el panel (Cocina y Caja).
    Cocina: Pagados o Locales.
    Caja: En espera de verificación.
    """
    # Obtenemos todos los que no estén entregados/listos/rechazados aún
    pedidos = Order.objects.filter(
        status__in=["pendiente", "esperando_pago"]
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
            "service_type": p.service_type, # Devolvemos el código (HERE/TOGO)
            "service_type_display": p.get_service_type_display(),
            "delivery_mode": p.get_delivery_mode_display() if p.delivery_mode else "N/A",
            "location": p.location or "N/A",
            "payment_proof": p.payment_proof.url if p.payment_proof else None
        }
        for p in pedidos
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def api_cocina_approve_payment(request, order_id):
    """
    Aprueba un pago desde el panel de Caja.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        order = Order.objects.get(id=order_id)
        order.payment_status = 'payment_approved'
        order.status = 'pendiente' # Aseguramos que pase a cocina
        order.save()
        
        # Opcional: Notificar al usuario por Telegram que su pago fue aprobado
        from .utils import notificar_pago_aprobado
        notificar_pago_aprobado(order.telegram_id, order.id)
        
        return JsonResponse({"status": "ok"})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)

@csrf_exempt
def api_cocina_reject_payment(request, order_id):
    """
    Rechaza un pago desde el panel de Caja.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        order = Order.objects.get(id=order_id)
        order.payment_status = 'payment_rejected'
        order.status = 'rechazado'
        order.save()
        
        # Opcional: Notificar rechazo
        from .utils import notificar_pago_rechazado
        notificar_pago_rechazado(order.telegram_id, order.id)
        
        return JsonResponse({"status": "ok"})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)

@csrf_exempt
def api_cocina_mark_ready(request, order_id):
    """
    Marca un pedido como listo.
    """
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
    """
    Marca un pedido como rechazado.
    """
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



def recomendacion_similar_view(request, telegram_id):
    try:
        from ml.embeddings import recomendar_similares
    except ImportError:
        return JsonResponse({"similares": [], "error": "ML module missing"})
    # ✅ Obtener último plato del usuario
    ultimo = Rating.objects.filter(telegram_id=telegram_id).order_by("-id").first()

    if not ultimo:
        return JsonResponse({"similares": []})

    plato_objetivo = ultimo.plato

    # ✅ Obtener todos los platos del menú (campo correcto: name)
    platos = list(Product.objects.values_list("name", flat=True))

    # ✅ Calcular similares
    try:
        similares = recomendar_similares(plato_objetivo, platos, top_n=5)
    except Exception as e:
        print(f"Error in similar recommendation: {e}")
        similares = []

    return JsonResponse({
        "plato_base": plato_objetivo,
        "similares": similares
    })



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


# ----------------------------------------------------
# ✅ SESSION API (STATE MACHINE)
# ----------------------------------------------------
from .models import TelegramSession

@csrf_exempt
def get_or_create_session(request, telegram_id):
    session, created = TelegramSession.objects.get_or_create(telegram_id=telegram_id)
    return JsonResponse({
        "telegram_id": session.telegram_id,
        "state": session.state,
        "current_product_id": session.current_product_id,
        "temp_data": session.temp_data
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
        print(f"Error updating session: {e}")
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
