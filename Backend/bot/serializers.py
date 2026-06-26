from rest_framework import serializers
from .models import Order, Rating, GustoCliente


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
    items = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = Order
        fields = "__all__"
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        
        # Crear OrderItems
        if items_data:
            from .models import OrderItem
            for item in items_data:
                try:
                    OrderItem.objects.create(
                        order=order,
                        product_id=item.get('product_id'),
                        cantidad=item.get('cantidad', 1),
                        precio_unitario=item.get('precio_unitario', 0)
                    )
                except Exception as e:
                    print(f"Error creando item de orden: {e}")
                    
        return order


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"


class GustoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GustoCliente
        fields = "__all__"

