# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from rest_framework.permissions import AllowAny # o IsAuthenticated, dependiendo del caso

class MenuListView(APIView):
    # Permite acceso a cualquiera para ver el menú.
    # Si quieres restringir, usa IsAuthenticated
    permission_classes = [AllowAny] 

    def get(self, request, format=None):
        # 1. Obtener todos los productos activos de la base de datos
        products = Product.objects.filter(is_active=True)
        
        # 2. Serializar los datos
        serializer = ProductSerializer(products, many=True)
        
        # 3. Inicializar el diccionario de agrupación (similar a tu JSON anterior)
        grouped_menu = {
            'promociones': [],
            'entradas': [],
            'principales': [],
            'postres': [],
            'bebidas': [],
        }
        
        # 4. Agrupar los productos serializados por su campo 'category'
        for product_data in serializer.data:
            category_key = product_data.get('category')
            
            # El campo 'category' en el modelo es una clave en minúsculas (ej: 'entradas')
            if category_key in grouped_menu:
                grouped_menu[category_key].append(product_data)
            else:
                # Si por alguna razón la categoría es inválida, se va a Promociones
                grouped_menu['promociones'].append(product_data)
        
        # 5. Devolver el diccionario agrupado como respuesta JSON
        return Response(grouped_menu)