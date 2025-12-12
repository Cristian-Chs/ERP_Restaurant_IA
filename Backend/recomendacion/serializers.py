from rest_framework import serializers
from .models import Plato, Recomendacion

class PlatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plato
        fields = "__all__"

class RecomendacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recomendacion
        fields = "__all__"
