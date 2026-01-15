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
import re
from sklearn.linear_model import LinearRegression

from .models import Product, Ingredient, Flavor, GlobalSetting, InventoryMovement
from django.db.models import Sum, Count, Avg, F
from .serializers import ProductSerializer, IngredientSerializer, FlavorSerializer
import hmac
import hashlib
import time
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

# ✅ Helper para calcular gastos basados en recetas (Dinámico)
def calculate_recipe_expenses(orders_queryset):
    """
    Calcula los gastos teóricos basados en las recetas de los productos vendidos.
    Retorna:
    - total_expenses (float): Costo total de ingredientes
    - shopping_list (list): Lista detallada de ingredientes requeridos [{nombre, qty, unit, cost, total}]
    """
    total_expenses = 0
    ingredient_needs = {} # {ing_name: {qty, unit, cost_per_unit, total_cost}}
    
    # 1. Agrupar productos vendidos
    sold_items = {} # {product_name: qty}
    
    # Iterar eficientemente con iterator()
    for order_item in orders_queryset.values_list('item', flat=True).iterator():
        # Parsear cantidad y nombre: "2 x Hamburguesa (Extra...)"
        match = re.search(r'^(\d+)\s*x\s*(.*?)(?:\s*[\(\[].*|$)', order_item)
        if match:
            qty = int(match.group(1))
            product_name = match.group(2).strip()
        else:
            qty = 1
            product_name = order_item.strip()
            
        sold_items[product_name] = sold_items.get(product_name, 0) + qty

    # 2. Calcular ingredientes necesarios basado en recetas
    for product_name, total_qty in sold_items.items():
        # Buscar producto
        product = Product.objects.filter(name__iexact=product_name).first()
        if not product:
            product = Product.objects.filter(name__icontains=product_name).first()
            
        if product:
            # Obtener recetas del producto
            recipes = product.recetas.select_related('ingredient').all()
            
            for recipe in recipes:
                ing = recipe.ingredient
                needed_qty = float(recipe.quantity) * total_qty
                cost = float(ing.cost) * needed_qty
                
                if ing.nombre not in ingredient_needs:
                    ingredient_needs[ing.nombre] = {
                        'ingredient_name': ing.nombre,
                        'quantity': 0.0,
                        'unit': ing.unit,
                        'cost_per_unit': float(ing.cost),
                        'total_cost': 0.0
                    }
                
                ingredient_needs[ing.nombre]['quantity'] += needed_qty
                ingredient_needs[ing.nombre]['total_cost'] += cost
                total_expenses += cost

    # Convertir a lista ordenada
    shopping_list = sorted(ingredient_needs.values(), key=lambda x: x['total_cost'], reverse=True)
    
    return total_expenses, shopping_list

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

# ✅ Recipe ViewSet (Recetario)
from .serializers import RecipeSerializer
from .models import Recipe

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        # Override to ensure integrity or custom logic if needed
        return super().create(request, *args, **kwargs)

# ✅ RRHH ViewSets
from .serializers import EmployeeSerializer, PayrollPaymentSerializer
from .models import Employee, PayrollPayment

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class PayrollPaymentViewSet(viewsets.ModelViewSet):
    queryset = PayrollPayment.objects.all().order_by('-payment_date')
    serializer_class = PayrollPaymentSerializer
    permission_classes = [permissions.IsAdminUser]

# --- ESTADÍSTICAS Y IA ---

from django.db.models import Sum, Count, Avg, F
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
            recaudado=Sum('precio')
        ).order_by('-total_pedidos')[:5]

        top_products_list = []
        for prod in top_products:
            avg_stars = Rating.objects.filter(plato=prod['item']).aggregate(Avg('estrellas'))['estrellas__avg']
            prod_dict = {
                'item': prod['item'],
                'total_pedidos': prod['total_pedidos'],
                'recaudado': float(prod['recaudado'] or 0),
                'avg_stars': round(avg_stars, 1) if avg_stars else 0
            }
            top_products_list.append(prod_dict)

        # 4. Insights: Top Clientes
        top_customers = Order.objects.filter(
            payment_status='payment_approved'
        ).values('telegram_id').annotate(
            total_ordenes=Count('id'),
            total_gastado=Sum('precio')
        ).order_by('-total_gastado')[:5]

        top_customers_list = [
            {
                'telegram_id': c['telegram_id'],
                'total_pedidos': c['total_ordenes'],
                'total_gastado': float(c['total_gastado'] or 0)
            } for c in top_customers
        ]

        # 5. Breakdown por Tipo de Servicio
        service_stats = Order.objects.filter(payment_status='payment_approved').values('service_type').annotate(
            count=Count('id')
        )
        service_breakdown = {s['service_type']: s['count'] for s in service_stats}

        return Response({
            "diarias": [{"dia": d['dia'], "total": float(d['total'] or 0), "cantidad": d['cantidad']} for d in daily_stats],
            "mensuales": [{"mes": d['mes'], "total": float(d['total'] or 0), "cantidad": d['cantidad']} for d in monthly_stats],
            "anuales": [{"year": d['year'], "total": float(d['total'] or 0), "cantidad": d['cantidad']} for d in yearly_stats],
            "top_products": top_products_list,
            "top_customers": top_customers_list,
            "service_breakdown": service_breakdown,
            # ✅ Financial Module Data
            "financial_summary": self.get_financial_summary(monthly_stats),
            "reliability_score": self.get_reliability_score(service_breakdown)
        })

    def get_financial_summary(self, monthly_stats):
        # 1. Monthly Revenue (Current Month)
        current_month = datetime.now().strftime('%Y-%m')
        current_revenue = 0
        for m in monthly_stats:
            if m['mes'].strftime('%Y-%m') == current_month:
                current_revenue = float(m['total'] or 0)
                break
        
        # 2. Expenses based on RECIPES (Theoretical)
        # Calcula ingredientes necesarios según recetas de ventas
        first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_this_month = Order.objects.filter(
            payment_status='payment_approved',
            fecha__gte=first_day
        )
        
        monthly_expenses, _ = calculate_recipe_expenses(orders_this_month)
        
        # 3. Estimated Tax (10%)
        estimated_tax = current_revenue * 0.10
        
        # 4. Net Profit (Revenue - Real Expenses - Tax)
        net_profit = current_revenue - monthly_expenses - estimated_tax
        
        # 5. Payment Methods (Mocked/Parsed)
        top_method = "Transferencia" 
        
        return {
            "current_month_revenue": current_revenue,
            "monthly_expenses": monthly_expenses,
            "estimated_tax": estimated_tax,
            "net_profit": net_profit,
            "currency": "$",
            "top_payment_method": top_method
        }

    def get_reliability_score(self, service_breakdown):
        # Calculate Reliability/Profitability Score (AI Endorsed)
        # Formula: (Approval Rate * 0.5) + (Sales Trend Up * 0.3) + (Active Products * 0.2)
        
        # Approval Rate
        total_orders = Order.objects.count()
        approved_orders = Order.objects.filter(payment_status='payment_approved').count()
        approval_rate = (approved_orders / total_orders) if total_orders > 0 else 0
        
        # Predict Trend (Reuse logic or call internal)
        # Minimal linear regression for trend
        last_7_days = Order.objects.filter(fecha__gte=datetime.now()-timedelta(days=7)).count()
        previous_7_days = Order.objects.filter(fecha__gte=datetime.now()-timedelta(days=14), fecha__lt=datetime.now()-timedelta(days=7)).count()
        trend_score = 1.0 if last_7_days >= previous_7_days else 0.5
        
        # Final Score (0 to 100)
        final_score = (approval_rate * 60) + (trend_score * 40)
        
        return {
            "score": round(final_score, 1),
            "label": "Alta" if final_score > 80 else ("Media" if final_score > 50 else "Baja"),
            "ai_endorsed": True,
            "description": "Calculado basado en consistencia de ventas y tasa de aprobación."
        }

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

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

class ExportFinancialPDFView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # 1. Recalculate Stats (Same logic as AdminStatsView)
        current_month = datetime.now().strftime('%Y-%m')
        
        monthly_stats = Order.objects.filter(
            fecha__year=datetime.now().year,
            payment_status='payment_approved'
        ).annotate(mes=TruncMonth('fecha')).values('mes').annotate(
            total=Sum('precio')
        )
        
        current_revenue = 0
        for m in monthly_stats:
            if m['mes'].strftime('%Y-%m') == current_month:
                current_revenue = float(m['total'] or 0)
                break
        
        # 2. Expenses based on RECIPES (Theoretical & Shopping List)
        first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_this_month = Order.objects.filter(
            payment_status='payment_approved',
            fecha__gte=first_day
        )
        
        monthly_expenses, shopping_list = calculate_recipe_expenses(orders_this_month)

        # 3. Estimated Tax (10%)
        estimated_tax = current_revenue * 0.10
        
        # 4. Net Profit (Revenue - Real Expenses - Tax)
        net_profit = current_revenue - monthly_expenses - estimated_tax
        
        # Reliability Score Mock/Calc
        total_orders = Order.objects.count()
        approved_orders = Order.objects.filter(payment_status='payment_approved').count()
        approval_rate = (approved_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Generate PDF
        response = HttpResponse(content_type='application/pdf')
        filename = f"Reporte_Financiero_{current_month}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        p = canvas.Canvas(response, pagesize=letter)
        w, h = letter

        # Header
        p.setTitle(f"Reporte Financiero {current_month}")
        
        # Background Header
        p.setFillColor(colors.HexColor("#1f2428"))
        p.rect(0, h - 100, w, 100, fill=1, stroke=0)
        
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, h - 60, "Reporte Financiero Mensual")
        p.setFont("Helvetica", 12)
        p.drawString(50, h - 80, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Content
        y = h - 150
        p.setFillColor(colors.black)
        
        # Box 1: Revenue
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Dinero Reunido (Ingreso Bruto)")
        p.setFont("Helvetica", 14)
        p.drawString(350, y, f"${current_revenue:,.2f}")
        p.line(50, y-10, 500, y-10)
        
        y -= 50
        # Box 2: Real Expenses (NEW)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Gastos de Mercancía (Compras)")
        p.setFillColor(colors.red)
        p.drawString(350, y, f"-${monthly_expenses:,.2f}")
        p.setFillColor(colors.black)
        p.line(50, y-10, 500, y-10)

        y -= 50
        # Box 3: Tax
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Impuesto Estimado (10%)")
        p.setFillColor(colors.red)
        p.drawString(350, y, f"-${estimated_tax:,.2f}")
        p.setFillColor(colors.black)
        p.line(50, y-10, 500, y-10)

        y -= 50
        # Box 4: Net Profit
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "Utilidad Neta (Libre)")
        p.setFillColor(colors.green)
        p.drawString(350, y, f"${net_profit:,.2f}")
        p.setFillColor(colors.black)
        p.line(50, y-10, 500, y-10)

        # === DETAILED PURCHASES SECTION (New Page or Below) ===
        p.showPage() # New page for details
        
        # Header Detailed
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, h - 50, "Lista de Compras Automática (Recetario)")
        p.setFont("Helvetica", 10)
        p.drawString(50, h - 70, "Generado según ingredientes necesarios para las ventas del mes.")
        
        y = h - 100
        headers = ["Ingrediente", "Cant. Necesaria", "Unidad", "Costo/U", "Total"]
        x_pos = [50, 200, 320, 380, 480]
        
        # Table Header
        p.setFont("Helvetica-Bold", 10)
        for i, head in enumerate(headers):
            p.drawString(x_pos[i], y, head)
        p.line(50, y-5, 550, y-5)
        
        y -= 25
        p.setFont("Helvetica", 10)
        
        # Table Rows (Shopping List from Helper)
        total_list_cost = 0
        for item in shopping_list:
            if y < 50:
                p.showPage()
                y = h - 50
                p.setFont("Helvetica-Bold", 10)
                for i, head in enumerate(headers):
                    p.drawString(x_pos[i], y, head)
                p.line(50, y-5, 550, y-5)
                y -= 25
                p.setFont("Helvetica", 10)
            
            p.drawString(x_pos[0], y, item['ingredient_name'][:30])
            p.drawString(x_pos[1], y, f"{item['quantity']:.2f}")
            p.drawString(x_pos[2], y, item['unit'])
            p.drawString(x_pos[3], y, f"${item['cost_per_unit']:.2f}")
            p.drawString(x_pos[4], y, f"${item['total_cost']:.2f}")
            
            total_list_cost += item['total_cost']
            y -= 20
        
        # Total Check Line
        y -= 10
        p.line(50, y+15, 550, y+15)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, y, "TOTAL NECESARIO:")
        p.drawString(480, y, f"${total_list_cost:,.2f}")

        y -= 80
        # AI Section
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Indicadores de Inteligencia Artificial")
        y -= 30
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"• Tasa de Aprobación de Pagos: {approval_rate:.1f}%")
        y -= 20
        p.drawString(50, y, f"• Método de Pago Frecuente: Transferencia")
        
        # Footer
        p.setFont("Helvetica-Oblique", 10)
        p.setFillColor(colors.gray)
        p.drawString(50, 50, "Documento generado automáticamente por Sistema de Gestión AI.(Derechos reservados para Restaurante 4 Sabores © 2026)")

        p.showPage()
        p.save()
        return response

class ExportPayrollPDFView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # 1. Get Payroll Data (All history or filtered)
        # For simplicity, we export all history ordered by date
        payments = PayrollPayment.objects.all().order_by('-payment_date')
        
        current_date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Generate PDF
        response = HttpResponse(content_type='application/pdf')
        filename = f"Reporte_Nomina_{current_date_str}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        p = canvas.Canvas(response, pagesize=letter)
        w, h = letter

        # Header
        p.setTitle(f"Reporte de Nómina {current_date_str}")
        
        # Background Header
        p.setFillColor(colors.HexColor("#1f2428"))
        p.rect(0, h - 80, w, 80, fill=1, stroke=0)
        
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, h - 50, "Reporte de Nómina")
        p.setFont("Helvetica", 10)
        p.drawString(w - 200, h - 50, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Content Configuration
        y = h - 120
        p.setFillColor(colors.black)
        
        # Table Headers
        headers = ["Fecha", "Empleado", "Rol", "Notas", "Monto"]
        x_positions = [50, 150, 270, 350, 500]
        
        p.setFont("Helvetica-Bold", 10)
        for i, header in enumerate(headers):
            p.drawString(x_positions[i], y, header)
        
        p.line(50, y-5, 550, y-5)
        y -= 25
        
        # Table Rows
        p.setFont("Helvetica", 10)
        total_payroll = 0
        
        for pay in payments:
            if y < 50: # New Page if needed
                p.showPage()
                y = h - 50
                p.setFont("Helvetica-Bold", 10)
                for i, header in enumerate(headers):
                    p.drawString(x_positions[i], y, header)
                p.line(50, y-5, 550, y-5)
                y -= 25
                p.setFont("Helvetica", 10)

            p.drawString(x_positions[0], y, str(pay.payment_date))
            p.drawString(x_positions[1], y, pay.employee.name[:20]) # Truncate if too long
            p.drawString(x_positions[2], y, pay.employee.get_role_display()[:15])
            p.drawString(x_positions[3], y, (pay.notes or "")[:20])
            p.drawString(x_positions[4], y, f"${pay.amount:,.2f}")
            
            total_payroll += pay.amount
            y -= 20
            
        # Total
        y -= 10
        p.line(50, y+15, 550, y+15)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, y, "TOTAL PAGADO:")
        p.setFillColor(colors.HexColor("#2ecc71"))
        p.drawString(500, y, f"${total_payroll:,.2f}")
        
        # Footer
        p.setFillColor(colors.gray)
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(50, 30, "Documento confidencial de Recursos Humanos. 4 Sabores Restaurant.")

        p.showPage()
        p.save()
        return response
from .ml_engine import get_price_suggestion

class PriceOptimizationAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, product_id):
        suggestion = get_price_suggestion(product_id)
        
        try:
            product = Product.objects.get(id=product_id)
            return Response({
                "product_id": product_id,
                "current_price": float(product.price),
                "suggested_price": suggestion,
                "status": "success",
                "message": "Sugerencia calculada basada en elasticidad de demanda e histórico."
            })
        except Product.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=404)
from .demand_engine import get_demand_forecast

class DemandPredictionAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        try:
            forecast = get_demand_forecast()
            return Response({
                "status": "success",
                "predictions": forecast,
                "message": "Predicción de demanda horaria para las próximas 24 horas (Facebook Prophet)."
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
from .currency_service import get_current_rates

class CurrencyRatesAPI(APIView):
    permission_classes = [permissions.AllowAny] # Público para que los clientes vean los precios convertidos

    def get(self, request):
        rates = get_current_rates()
        return Response(rates)

class UpdateCurrencyRateAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        new_rate = request.data.get("rate")
        if not new_rate:
            return Response({"error": "Tasa requerida"}, status=400)
        
        try:
            rate_obj, created = GlobalSetting.objects.get_or_create(key="VES_USD_RATE")
            rate_obj.value = str(new_rate)
            rate_obj.save()
            
            # Limpiar cache para que se refresque al instante
            from django.core.cache import cache
            cache.delete('exchange_rates')
            
            return Response({
                "status": "success",
                "message": f"Tasa actualizada a {new_rate} Bs.",
                "rate": new_rate
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
