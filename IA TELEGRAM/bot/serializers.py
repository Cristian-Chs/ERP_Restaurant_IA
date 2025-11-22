from rest_framework import serializers
from .models import UserPreference, UserKnowledge, Order  # ✅ Importa todos los modelos

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['id', 'telegram_id', 'preference', 'liked', 'created_at', 'updated_at']

class UserKnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserKnowledge
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
