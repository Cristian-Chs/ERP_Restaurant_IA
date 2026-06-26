import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from .models import Order, Rating
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class MetricsConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keep_running = False
        self._metrics_task = None

    async def connect(self):
        await self.accept()
        self._keep_running = True
        self._metrics_task = asyncio.create_task(self._send_metrics_periodically())

    async def disconnect(self, close_code):
        self._keep_running = False
        if self._metrics_task:
            self._metrics_task.cancel()
            self._metrics_task = None

    async def _send_metrics_periodically(self):
        while self._keep_running:
            try:
                metrics = await self._get_metrics()
                await self.send(text_data=json.dumps(metrics))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending metrics: {e}")
            await asyncio.sleep(5)

    @sync_to_async
    def _get_metrics(self):
        today = timezone.now().date()

        ingresos_hoy = Order.objects.filter(
            fecha__date=today,
            payment_status='payment_approved'
        ).aggregate(total=Sum('precio'))['total'] or 0

        pedidos_activos = Order.objects.filter(
            status__in=['pendiente', 'esperando_pago']
        ).count()

        top_items = Order.objects.filter(fecha__date=today).values('item').annotate(
            qty=Count('id')
        ).order_by('-qty')[:3]

        latest_ratings = list(
            Rating.objects.all().order_by('-fecha')[:10].values(
                'plato', 'estrellas', 'comentario', 'sentimiento'
            )
        )

        return {
            "ingresos_hoy": float(ingresos_hoy),
            "pedidos_activos": pedidos_activos,
            "top_items": list(top_items),
            "recent_ratings": latest_ratings,
            "timestamp": timezone.now().strftime("%H:%M:%S")
        }
