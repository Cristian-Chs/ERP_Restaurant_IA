import hashlib
import hmac
import time
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import GlobalSetting, Table
from ..serializers import TableSerializer
from ..ml_engine import get_price_suggestion
from ..currency_service import get_current_rates

logger = logging.getLogger(__name__)


class TelegramLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        hash_received = data.get('hash')
        if not hash_received:
            return Response({"error": "No hash provided"}, status=400)

        bot_token = settings.TELEGRAM_BOT_TOKEN

        check_list = []
        for key, value in sorted(data.items()):
            if key != 'hash':
                check_list.append(f"{key}={value}")
        data_check_string = "\n".join(check_list)

        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if hmac_hash != hash_received:
            return Response({"error": "Hash validation failed"}, status=403)

        auth_date = int(data.get('auth_date', 0))
        if time.time() - auth_date > 86400:
            return Response({"error": "Auth data expired"}, status=403)

        telegram_id = data.get('id')
        username = f"tg_{telegram_id}"
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        user, created = User.objects.get_or_create(username=username)
        if created:
            user.first_name = first_name
            user.last_name = last_name
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        refresh['rol'] = 'admin' if user.is_staff else 'cliente'

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'is_new': created,
            },
        })


class PriceOptimizationAPI(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, product_id):
        try:
            suggestion = get_price_suggestion(product_id)
            if suggestion is None:
                return Response({"error": "Producto no encontrado"}, status=404)
            return Response({
                "status": "success",
                "suggestion": suggestion,
                "message": "Sugerencia calculada basada en elasticidad de demanda e histórico.",
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class DemandPredictionAPI(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            from ..demand_engine import get_demand_forecast
            forecast = get_demand_forecast()
            return Response({
                "status": "success",
                "predictions": forecast,
                "message": "Predicción de demanda horaria para las próximas 24 horas.",
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class CurrencyRatesAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        rates = get_current_rates()
        return Response(rates)


class UpdateCurrencyRateAPI(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        new_rate = request.data.get("rate")
        if not new_rate:
            return Response({"error": "Tasa requerida"}, status=400)

        try:
            rate_obj, created = GlobalSetting.objects.get_or_create(key="VES_USD_RATE")
            rate_obj.value = str(new_rate)
            rate_obj.save()
            cache.delete('exchange_rates')
            return Response({
                "status": "success",
                "message": f"Tasa actualizada a {new_rate} Bs.",
                "rate": new_rate,
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class TableAvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        total_tables = Table.objects.count()
        occupied_tables = Table.objects.filter(is_occupied=True).count()

        can_order = True
        message = "Hay mesas disponibles."

        if total_tables > 0 and occupied_tables >= total_tables:
            can_order = False
            message = "Lo siento pero en estos momento no hay lugares disponible."

        return Response({
            "can_order": can_order,
            "message": message,
            "available_count": total_tables - occupied_tables,
        })
