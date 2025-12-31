from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from .models import Product, Ingredient
from .serializers import ProductSerializer

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
                    "ingredientes": ingredientes
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
