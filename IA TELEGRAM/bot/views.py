from rest_framework import viewsets
from django.shortcuts import render, redirect

from .models import UserPreference, UserKnowledge, Order
from .serializers import UserPreferenceSerializer, UserKnowledgeSerializer, OrderSerializer
from .utils import notificar_pedido_listo  # 👈 import limpio

# ------------------------------
# API REST con DRF
# ------------------------------

class UserPreferenceViewSet(viewsets.ModelViewSet):
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer

class UserKnowledgeViewSet(viewsets.ModelViewSet):
    queryset = UserKnowledge.objects.all()
    serializer_class = UserKnowledgeSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

# ------------------------------
# Panel de cocina (vista web)
# ------------------------------

def cocina_panel(request):
    """
    Vista para cocina: muestra pedidos pendientes y permite marcarlos como listos.
    """
    pedidos = Order.objects.filter(status="pendiente")

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        order = Order.objects.get(id=order_id)
        order.status = "listo"
        order.save()

        # Notificar automáticamente al cliente
        notificar_pedido_listo(order.telegram_id, order.item)

        return redirect("cocina_panel")

    return render(request, "bot/cocina_panel.html", {"pedidos": pedidos})

