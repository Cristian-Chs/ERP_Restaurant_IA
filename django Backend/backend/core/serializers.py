# core/serializers.py
from rest_framework import serializers
from .models import Product 

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # 🚨 CORRECCIÓN: Agregar 'imagen' al final
        fields = ('id', 'name', 'description', 'price', 'category', 'is_active', 'imagen')