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

            # 🛡️ VERIFICACIÓN DE SEGURIDAD (FASE 8)
            from .security import verify_payment_authenticity
            security_results = verify_payment_authenticity(order, order.payment_proof.path)
            
            # Si es duplicado, marcar estado especial y alertar
            if security_results["is_duplicate"]:
                order.status = 'fraude_sospecha'
                order.payment_data = {"fraud_error": f"Duplicado de orden #{security_results['duplicate_order_id']}"}
                order.save()
                print(f"⚠️ FRAUDE DETECTADO: El comprobante ya fue usado en orden #{security_results['duplicate_order_id']}")
            
            # Notificar al Administrador/Chef inmediatamente
            try:
                from .utils import notificar_nuevo_pedido_externo
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
    comentario = data.get("comentario", "")
    
    # Analizar sentimiento si hay comentario
    from .sentiment import analizar_sentimiento_groq
    sentimiento = analizar_sentimiento_groq(comentario) if comentario else "Neutral"

    Rating.objects.create(
        telegram_id=data["telegram_id"],
        plato=data["plato"],
        estrellas=data["rating"],
        comentario=comentario,
        sentimiento=sentimiento
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
            "payment_proof": p.payment_proof.url if p.payment_proof else None,
            "currency": p.currency,
            "exchange_rate": float(p.exchange_rate)
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

from .models import LoyaltyPoints

@csrf_exempt
def get_loyalty_points(request, telegram_id):
    """
    Devuelve los puntos de fidelidad de un cliente.
    """
    try:
        loyalty = LoyaltyPoints.objects.get(telegram_id=telegram_id)
        data = {
            "telegram_id": loyalty.telegram_id,
            "puntos": loyalty.puntos,
            "nivel": loyalty.nivel,
            "total_gastado": float(loyalty.total_gastado)
        }
        return JsonResponse(data)
    except LoyaltyPoints.DoesNotExist:
        return JsonResponse({"puntos": 0, "nivel": "Bronce", "total_gastado": 0.0})


# ----------------------------------------------------
# ✅ COUPON MANAGEMENT API
# ----------------------------------------------------
from .models import Coupon, RedeemedCoupon
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status as http_status

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def coupon_list_create(request):
    """
    GET: Lista todos los cupones
    POST: Crea un nuevo cupón
    """
    if request.method == 'GET':
        coupons = Coupon.objects.all().order_by('-fecha_creacion')
        data = [
            {
                'id': c.id,
                'code': c.code,
                'discount_type': c.discount_type,
                'discount_amount': float(c.discount_amount),
                'points_cost': c.points_cost,
                'is_active': c.is_active,
                'valid_from': c.valid_from.isoformat() if c.valid_from else None,
                'valid_until': c.valid_until.isoformat() if c.valid_until else None,
                'max_uses': c.max_uses,
                'current_uses': c.current_uses,
                'min_order_amount': float(c.min_order_amount),
                'fecha_creacion': c.fecha_creacion.isoformat()
            }
            for c in coupons
        ]
        return Response(data)
    
    elif request.method == 'POST':
        data = request.data
        try:
            # ✅ Parse dates explicitly to handle "YYYY-MM-DD" from frontend
            valid_from = data.get('valid_from')
            valid_until = data.get('valid_until')

            if valid_from and len(valid_from) == 10: # YYYY-MM-DD
                 valid_from += "T00:00:00Z"
            
            if valid_until and len(valid_until) == 10: # YYYY-MM-DD
                 valid_until += "T23:59:59Z" # End of day

            coupon = Coupon.objects.create(
                code=data['code'].upper(),
                discount_type=data.get('discount_type', 'fixed'),
                discount_amount=data['discount_amount'],
                points_cost=data.get('points_cost', 0),
                is_active=data.get('is_active', True),
                valid_from=valid_from,
                valid_until=valid_until,
                max_uses=data.get('max_uses', 0),
                min_order_amount=data.get('min_order_amount', 0)
            )
            return Response({
                'id': coupon.id,
                'code': coupon.code,
                'message': 'Cupón creado exitosamente'
            }, status=http_status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=http_status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def coupon_detail(request, coupon_id):
    """
    GET: Obtiene detalles de un cupón
    PUT: Actualiza un cupón
    DELETE: Elimina un cupón
    """
    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        return Response({'error': 'Cupón no encontrado'}, status=http_status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        data = {
            'id': coupon.id,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_amount': float(coupon.discount_amount),
            'points_cost': coupon.points_cost,
            'is_active': coupon.is_active,
            'valid_from': coupon.valid_from.isoformat() if coupon.valid_from else None,
            'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
            'max_uses': coupon.max_uses,
            'current_uses': coupon.current_uses,
            'min_order_amount': float(coupon.min_order_amount),
            'fecha_creacion': coupon.fecha_creacion.isoformat()
        }
        return Response(data)
    
    elif request.method == 'PUT':
        data = request.data
        try:
            coupon.code = data.get('code', coupon.code).upper()
            coupon.discount_type = data.get('discount_type', coupon.discount_type)
            coupon.discount_amount = data.get('discount_amount', coupon.discount_amount)
            coupon.points_cost = data.get('points_cost', coupon.points_cost)
            coupon.is_active = data.get('is_active', coupon.is_active)
            
            # ✅ Handle dates update
            updated_valid_from = data.get('valid_from', coupon.valid_from)
            updated_valid_until = data.get('valid_until', coupon.valid_until)

            if isinstance(updated_valid_from, str) and len(updated_valid_from) == 10:
                updated_valid_from += "T00:00:00Z"

            if isinstance(updated_valid_until, str) and len(updated_valid_until) == 10:
                updated_valid_until += "T23:59:59Z"

            coupon.valid_from = updated_valid_from
            coupon.valid_until = updated_valid_until
            
            coupon.max_uses = data.get('max_uses', coupon.max_uses)
            coupon.min_order_amount = data.get('min_order_amount', coupon.min_order_amount)
            coupon.save()
            return Response({'message': 'Cupón actualizado exitosamente'})
        except Exception as e:
            return Response({'error': str(e)}, status=http_status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        coupon.delete()
        return Response({'message': 'Cupón eliminado exitosamente'}, status=http_status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def coupon_redemptions(request):
    """
    Lista todos los cupones canjeados
    """
    redemptions = RedeemedCoupon.objects.all().select_related('coupon', 'order').order_by('-fecha_canje')
    data = [
        {
            'id': r.id,
            'telegram_id': r.telegram_id,
            'coupon_code': r.coupon.code,
            'discount_applied': float(r.discount_applied),
            'fecha_canje': r.fecha_canje.isoformat(),
            'order_id': r.order.id if r.order else None
        }
        for r in redemptions
    ]
    return Response(data)


@api_view(['POST'])
def validate_coupon(request):
    """
    Valida un cupón y devuelve el descuento aplicable
    No requiere autenticación para permitir uso en carrito web
    """
    coupon_code = request.data.get('code', '').upper()
    order_amount = float(request.data.get('order_amount', 0))
    
    if not coupon_code:
        return Response({'error': 'Código de cupón requerido'}, status=http_status.HTTP_400_BAD_REQUEST)
    
    try:
        coupon = Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return Response({'error': 'Cupón no válido'}, status=http_status.HTTP_404_NOT_FOUND)
    
    # Validar cupón
    if not coupon.is_valid():
        return Response({'error': 'Cupón expirado o inactivo'}, status=http_status.HTTP_400_BAD_REQUEST)
    
    # Calcular descuento
    discount = coupon.apply_discount(order_amount)
    
    if discount == 0:
        return Response({
            'error': f'Monto mínimo requerido: ${coupon.min_order_amount}'
        }, status=http_status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'valid': True,
        'code': coupon.code,
        'discount': float(discount),
        'discount_type': coupon.discount_type,
        'discount_amount': float(coupon.discount_amount),
        'message': f'Cupón aplicado: -{discount:.2f}'
    })


# ------------------------------
# ✅ ROUTE CALCULATION API
# ------------------------------
from bot_Cliente.dijkstra import PathFinder
import os

# Mapping of Sector Names to Approximate Coordinates (Lat, Lon)
# Based on Punto Fijo / Paraguana areas
SECTOR_COORDS = {
    "PUERTA MARAVEN": (11.696, -70.183),
    "COMUNIDAD CARDÓN": (11.668, -70.199),
    "MARAVEN": (11.670, -70.190),
    "CENTRO DE PUNTO FIJO": (11.705, -70.207),
    "BANCO OBRERO": (11.710, -70.198),
    "CAJA DE AGUA": (11.720, -70.195),
    "SANTA IRENE": (11.700, -70.195),
    "SANTA FE": (11.708, -70.188),
    "LAS MARGARITAS": (11.725, -70.180),
    "JUDIBANA": (11.758, -70.190),
    "LOS TAQUES": (11.833, -70.250),
    "VILLA MARINA": (11.850, -70.233),
    "EL CAYUDE": (11.600, -70.000) # Approx
}

@csrf_exempt
def calculate_route_view(request):
    """
    Calculates route using Dijkstra based on a sector name or coordinates.
    Expects JSON: { "location": "Puerta Maraven" } or { "location": "11.123, -70.123" }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        location_input = data.get("location", "").strip().upper()
        
        user_coords = None
        
        # 1. Try to match sector name
        if location_input in SECTOR_COORDS:
            user_coords = SECTOR_COORDS[location_input]
        
        # 2. Try to parse "Lat, Lon"
        else:
            try:
                parts = location_input.split(',')
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    user_coords = (lat, lon)
            except:
                pass
        
        if not user_coords:
            return JsonResponse({"error": "Ubicación no reconocida o inválida"}, status=400)
            
        # 3. Run Dijkstra
        finder = PathFinder()
        # Enforce map load (if not loaded)
        # Note: In production this should be loaded at startup (apps.py)
        # For now we check/load here safely
        if not finder.loaded:
            map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot_Cliente", "map.osm")
            finder.load_map(map_path)
            
        # Restaurant Coords (Fixed)
        restaurant_loc = (11.670464, -70.151655)
        
        result = finder.find_path(restaurant_loc, user_coords)
        
        return JsonResponse(result)

    except Exception as e:
        print(f"Error calculating route: {e}")
        return JsonResponse({"error": str(e)}, status=500)
