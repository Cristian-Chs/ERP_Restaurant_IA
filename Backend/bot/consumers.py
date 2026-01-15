import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from .models import Order, Rating
from asgiref.sync import sync_to_async

class MetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.keep_running = True
        # Iniciar el bucle de envío de métricas
        asyncio.create_task(self.send_metrics_periodically())

    async def disconnect(self, close_code):
        self.keep_running = False

    async def send_metrics_periodically(self):
        while self.keep_running:
            metrics = await self.get_metrics()
            await self.send(text_data=json.dumps(metrics))
            await asyncio.sleep(5) # Actualizar cada 5 segundos

    @sync_to_async
    def get_metrics(self):
        today = timezone.now().date()
        
        # Ingresos de hoy
        # Nota: Usamos float() porque Decimal no es serializable directamente a JSON
        ingresos_hoy = Order.objects.filter(
            fecha__date=today, 
            payment_status='payment_approved'
        ).aggregate(total=Sum('precio'))['total'] or 0
        
        # Pedidos activos (pendientes en cocina o caja)
        pedidos_activos = Order.objects.filter(
            status__in=['pendiente', 'esperando_pago']
        ).count()
        
        # Productos más vendidos hoy
        # (Heurística simple basada en el campo 'item' que es un string)
        # En un sistema real sería un modelo OrderItem
        top_items = Order.objects.filter(fecha__date=today).values('item').annotate(
            qty=Count('id')
        ).order_by('-qty')[:3]

        # ✅ 4. Últimos Ratings con Sentimiento
        latest_ratings = list(
            Rating.objects.all().order_by('-fecha')[:10].values(
                'plato', 'estrellas', 'comentario', 'sentimiento'
            )
        )

        # Tiempo promedio de preparación (simulado o basado en histórico)
        return {
            "ingresos_hoy": float(ingresos_hoy),
            "pedidos_activos": pedidos_activos,
            "top_items": list(top_items),
            "recent_ratings": latest_ratings, # Add recent_ratings here
            "timestamp": timezone.now().strftime("%H:%M:%S")
        }
