import re
import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from ..models import Product, Ingredient
from ..serializers import ProductSerializer

logger = logging.getLogger(__name__)


def calculate_recipe_expenses(orders_queryset):
    total_expenses = 0
    ingredient_needs = {}
    sold_items = {}

    for order_item in orders_queryset.values_list('item', flat=True).iterator():
        match = re.search(r'^(\d+)\s*x\s*(.*?)(?:\s*[\(\[].*|$)', order_item)
        if match:
            qty = int(match.group(1))
            product_name = match.group(2).strip()
        else:
            qty = 1
            product_name = order_item.strip()
        sold_items[product_name] = sold_items.get(product_name, 0) + qty

    for product_name, total_qty in sold_items.items():
        product = Product.objects.filter(name__iexact=product_name).first()
        if not product:
            product = Product.objects.filter(name__icontains=product_name).first()
        if product:
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
                        'total_cost': 0.0,
                    }
                ingredient_needs[ing.nombre]['quantity'] += needed_qty
                ingredient_needs[ing.nombre]['total_cost'] += cost
                total_expenses += cost

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
    detalle = request.GET.get("detalle")

    if detalle:
        try:
            producto = Product.objects.filter(
                name__iexact=detalle.strip(), is_active=True
            ).first()

            if producto:
                ingredientes = list(producto.ingredientes.values_list("nombre", flat=True))
                return JsonResponse({
                    "nombre": producto.name,
                    "descripcion": producto.description,
                    "precio": float(producto.price),
                    "categoria": producto.category,
                    "ingredientes": ingredientes,
                    "sabores": list(producto.sabores.values_list("nombre", flat=True)),
                })
            else:
                return JsonResponse({
                    "error": f"Producto '{detalle}' no encontrado",
                    "ingredientes": [],
                }, status=404)
        except Exception as e:
            logger.error(f"ERROR en productos_view con detalle: {e}")
            return JsonResponse({"error": str(e), "ingredientes": []}, status=500)

    productos_queryset = Product.objects.filter(is_active=True)
    nombres = list(productos_queryset.values_list("name", flat=True))
    detalles = [
        {
            "id": p.id,
            "nombre": p.name,
            "precio": float(p.price),
            "descripcion": p.description,
        }
        for p in productos_queryset
    ]

    return JsonResponse({"productos": nombres, "productos_detalle": detalles})


def check_user_and_get_reset_link(request):
    email = request.GET.get("email")
    if not email:
        return JsonResponse({"error": "Email requerido"}, status=400)

    try:
        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({"exists": False, "error": "Cuenta no existe"})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        return JsonResponse({"exists": True, "uid": uid, "token": token})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
