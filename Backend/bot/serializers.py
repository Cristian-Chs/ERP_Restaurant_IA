from rest_framework import serializers
from .models import Order, Rating, GustoCliente


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"


class GustoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GustoCliente
        fields = "__all__"

