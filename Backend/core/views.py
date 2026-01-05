from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression

from .models import Product, Ingredient, Flavor
from .serializers import ProductSerializer, IngredientSerializer, FlavorSerializer
import hmac
import hashlib
import time
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

def listar_ingredientes(request):
    ingredientes = Ingredient.objects.all()
    data = [{"id": ing.id, "nombre": ing.nombre} for ing in ingredientes]
    return JsonResponse({"ingredientes": data})


def filtrar_productos(request):
    ingredientes = request.GET.get("ingredientes")
    if ingredientes:
        lista = [i.strip() for i in ingredientes.split(",") if i.strip()]
        productos = Product.objects.filter(ingredientes__nombre__in=lista).distinct()
    else:
        productos = Product.objects.all()

    data = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": float(p.precio),
            "ingredientes": [i.nombre for i in p.ingredientes.all()],
            "sabores": [s.nombre for s in p.sabores.all()],
        }
        for p in productos
    ]
    return JsonResponse({"productos": data})


class MenuListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        products = Product.objects.filter(is_active=True)
        serializer = ProductSerializer(products, many=True)

        grouped_menu = {
            'promociones': [],
            'entradas': [],
            'principales': [],
            'postres': [],
            'bebidas': [],
        }

        for product_data in serializer.data:
            category_key = product_data.get('category')
            if category_key in grouped_menu:
                grouped_menu[category_key].append(product_data)
            else:
                grouped_menu['promociones'].append(product_data)

        return Response(grouped_menu)

def productos_view(request):
    # ✅ Si se solicita detalle de un producto específico
    detalle = request.GET.get("detalle")
    
    if detalle:
        try:
            # Buscar producto por nombre (case-insensitive)
            producto = Product.objects.filter(
                name__iexact=detalle.strip(),
                is_active=True
            ).first()
            
            if producto:
                # Obtener ingredientes del producto
                ingredientes = list(
                    producto.ingredientes.values_list("nombre", flat=True)
                )
                
                return JsonResponse({
                    "nombre": producto.name,
                    "descripcion": producto.description,
                    "precio": float(producto.price),
                    "categoria": producto.category,
                    "ingredientes": ingredientes,
                    "sabores": list(producto.sabores.values_list("nombre", flat=True))
                })
            else:
                return JsonResponse({
                    "error": f"Producto '{detalle}' no encontrado",
                    "ingredientes": []
                }, status=404)
        except Exception as e:
            print(f"ERROR en productos_view con detalle: {e}")
            return JsonResponse({
                "error": str(e),
                "ingredientes": []
            }, status=500)
    
    # ✅ Si no hay detalle, devolver lista de nombres (comportamiento original)
    productos = list(
        Product.objects.filter(is_active=True).values_list("name", flat=True)
    )
    return JsonResponse({"productos": productos})

def check_user_and_get_reset_link(request):
    """
    Endpoint de desarrollo para obtener UID y Token directamente si el usuario existe.
    AVISO: Esto es un bypass de seguridad solicitado para agilizar pruebas.
    """
    email = request.GET.get("email")
    if not email:
        return JsonResponse({"error": "Email requerido"}, status=400)
    
    try:
        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({"exists": False, "error": "Cuenta no existe"})
        
        # Generar UID y Token (Lógica estándar de Django/Djoser)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        return JsonResponse({
            "exists": True,
            "uid": uid,
            "token": token
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# --- PANEL ADMIN VIEWSETS ---

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        print(f"DEBUG: Create Product Request from user: {request.user}")
        print(f"DEBUG: Auth status: {request.user.is_authenticated}")
        print(f"DEBUG: Is Staff: {request.user.is_staff if hasattr(request.user, 'is_staff') else 'N/A'}")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        print(f"DEBUG: Update Product Request from user: {request.user}")
        return super().update(request, *args, **kwargs)

    def get_serializer_class(self):
        return ProductSerializer

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAdminUser]

class FlavorViewSet(viewsets.ModelViewSet):
    queryset = Flavor.objects.all()
    serializer_class = FlavorSerializer
    permission_classes = [permissions.IsAdminUser]

# --- ESTADÍSTICAS Y IA ---

from django.db.models import Sum, Count, Avg
from bot.models import Order, Rating

class AdminStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        print(f"DEBUG: Stats Request from user: {request.user}")
        # 0. Ventas por Día (últimos 30 días)
        daily_stats = Order.objects.filter(
            fecha__gte=datetime.now() - timedelta(days=30),
            payment_status='payment_approved'
        ).annotate(dia=TruncDay('fecha')).values('dia').annotate(
            total=Sum('precio'), 
            cantidad=Count('id')
        ).order_by('dia')

        # 1. Ventas por Mes (este año)
        monthly_stats = Order.objects.filter(
            fecha__year=datetime.now().year,
            payment_status='payment_approved'
        ).annotate(mes=TruncMonth('fecha')).values('mes').annotate(
            total=Sum('precio'),
            cantidad=Count('id')
        ).order_by('mes')

        # 2. Ventas por Año
        yearly_stats = Order.objects.filter(
            payment_status='payment_approved'
        ).annotate(year=TruncYear('fecha')).values('year').annotate(
            total=Sum('precio'),
            cantidad=Count('id')
        ).order_by('year')

        # 3. Insights: Top Productos
        top_products = Order.objects.filter(
            payment_status='payment_approved'
        ).values('item').annotate(
            total_pedidos=Count('id'),
            total_revenue=Sum('precio')
        ).order_by('-total_pedidos')[:5]

        for prod in top_products:
            avg_stars = Rating.objects.filter(plato=prod['item']).aggregate(Avg('estrellas'))['estrellas__avg']
            prod['avg_stars'] = round(avg_stars, 1) if avg_stars else 0

        # 4. Insights: Top Clientes
        top_customers = Order.objects.filter(
            payment_status='payment_approved'
        ).values('telegram_id').annotate(
            total_ordenes=Count('id'),
            total_gastado=Sum('precio')
        ).order_by('-total_gastado')[:5]

        # 5. Breakdown por Tipo de Servicio
        service_stats = Order.objects.filter(payment_status='payment_approved').values('service_type').annotate(
            count=Count('id')
        )
        service_breakdown = {s['service_type']: s['count'] for s in service_stats}

        return Response({
            "diarias": [{"dia": d['dia'], "total": float(d['total'] or 0), "cantidad": d['cantidad']} for d in daily_stats],
            "mensuales": [{"mes": d['mes'], "total": float(d['total'] or 0), "cantidad": d['cantidad']} for d in monthly_stats],
            "anuales": [{"year": d['year'], "total": float(d['total'] or 0), "cantidad": d['cantidad']} for d in yearly_stats],
            "top_products": list(top_products),
            "top_customers": list(top_customers),
            "service_breakdown": service_breakdown
        })

class SalesPredictionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Obtener datos históricos (últimos 60 días)
        data = Order.objects.filter(
            payment_status='payment_approved'
        ).annotate(dia=TruncDay('fecha')).values('dia').annotate(
            total=Sum('precio')
        ).order_by('dia')

        if len(data) < 5:
            return Response({
                "error": "No hay suficientes datos para predecir (mínimo 5 días)",
                "insufficient_data": True,
                "predicciones_proximos_7_dias": [],
                "trend": "neutral"
            }, status=200)

        # Preparar datos para Linear Regression
        # X = índice de día (0, 1, 2...), Y = total de ventas
        X = np.array(range(len(data))).reshape(-1, 1)
        y = np.array([float(d['total'] or 0) for d in data])

        model = LinearRegression()
        model.fit(X, y)

        # Predecir los próximos 7 días
        next_indices = np.array(range(len(data), len(data) + 7)).reshape(-1, 1)
        predictions = model.predict(next_indices)

        return Response({
            "predicciones_proximos_7_dias": list(predictions),
            "trend": "up" if model.coef_[0] > 0 else "down"
        })

class TelegramLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        hash_received = data.get('hash')
        if not hash_received:
            return Response({"error": "No hash provided"}, status=400)

        # 1. Verificar el Hash de Telegram
        bot_token = "8537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU"
        
        check_list = []
        for key, value in sorted(data.items()):
            if key != 'hash':
                check_list.append(f"{key}={value}")
        data_check_string = "\n".join(check_list)

        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if hmac_hash != hash_received:
            return Response({"error": "Hash validation failed"}, status=403)

        # 2. Verificar expiración (24h)
        auth_date = int(data.get('auth_date', 0))
        if time.time() - auth_date > 86400:
            return Response({"error": "Auth data expired"}, status=403)

        # 3. Obtener o Crear Usuario
        telegram_id = data.get('id')
        username = f"tg_{telegram_id}"
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        user, created = User.objects.get_or_create(username=username)
        if created:
            user.first_name = first_name
            user.last_name = last_name
            user.set_unusable_password() 
            user.save()

        # 4. Generar Tokens JWT
        refresh = RefreshToken.for_user(user)
        refresh['rol'] = 'admin' if user.is_staff else 'cliente'
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'is_new': created
            }
        })
