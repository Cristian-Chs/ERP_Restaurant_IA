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
            'id', 'name', 'description', 'price', 'cost_price', 'category', 'is_active', 
            'imagen', 'ingredientes', 'sabores', 'ingrediente_nombres', 'sabor_nombres'
        )

#  Nuevo: Serializers para RRHH
from .models import Employee, PayrollPayment, Recipe, InventoryMovement, Table

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class PayrollPaymentSerializer(serializers.ModelSerializer):
    employee_name = serializers.StringRelatedField(source='employee', read_only=True)
    
    class Meta:
        model = PayrollPayment
        fields = ('id', 'employee', 'employee_name', 'amount', 'payment_date', 'notes')

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

#  Serializers para Inventario y Recetas
class RecipeSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.StringRelatedField(source='ingredient', read_only=True)
    product_name = serializers.StringRelatedField(source='product', read_only=True)
    unit = serializers.CharField(source='ingredient.unit', read_only=True)
    cost = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = ('id', 'product', 'product_name', 'ingredient', 'ingredient_name', 'quantity', 'unit', 'cost')
    
    def get_cost(self, obj):
        """Calcula el costo de este ingrediente en la receta"""
        return float(obj.get_cost())

class InventoryMovementSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.StringRelatedField(source='ingredient', read_only=True)
    unit = serializers.CharField(source='ingredient.unit', read_only=True)
    total_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryMovement
        fields = ('id', 'ingredient', 'ingredient_name', 'movement_type', 'quantity', 'unit', 
                  'cost_per_unit', 'total_cost', 'date', 'notes')
    
    def get_total_cost(self, obj):
        """Calcula el costo total del movimiento"""
        return float(obj.get_total_cost())

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'

