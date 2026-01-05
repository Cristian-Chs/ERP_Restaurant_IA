# core/serializers.py
from rest_framework import serializers
from .models import Product, Ingredient, Flavor
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'

class FlavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flavor
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    # Usamos PrimaryKeyRelatedField para que React envíe solo IDs en el CRUD (Entrada)
    ingredientes = serializers.PrimaryKeyRelatedField(many=True, queryset=Ingredient.objects.all(), required=False)
    sabores = serializers.PrimaryKeyRelatedField(many=True, queryset=Flavor.objects.all(), required=False)

    # Campos de solo lectura para mostrar nombres en el Frontend (Salida)
    ingrediente_nombres = serializers.StringRelatedField(source='ingredientes', many=True, read_only=True)
    sabor_nombres = serializers.StringRelatedField(source='sabores', many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 'category', 'is_active', 
            'imagen', 'ingredientes', 'sabores', 'ingrediente_nombres', 'sabor_nombres'
        )

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar claims personalizados
        token['username'] = user.username
        
        # Lógica de roles
        if user.is_superuser:
            token['rol'] = 'admin'
        elif user.username == 'cocina':
            token['rol'] = 'cocina'
        else:
            token['rol'] = 'cliente'

        return token