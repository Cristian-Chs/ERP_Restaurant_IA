# core/serializers.py
from rest_framework import serializers
from .models import Product 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # 🚨 CORRECCIÓN: Agregar 'imagen' al final
        fields = ('id', 'name', 'description', 'price', 'category', 'is_active', 'imagen')

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