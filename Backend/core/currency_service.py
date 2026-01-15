import requests
from django.core.cache import cache
import time

from .models import GlobalSetting

class CurrencyService:
    BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"
    
    @classmethod
    def get_bs_rate(cls):
        """Retorna la tasa de BS desde la BD o un fallback."""
        return float(GlobalSetting.get_value("VES_USD_RATE", 55.40))

    @classmethod
    def get_rates(cls):
        """Devuelve las tasas de cambio cacheadas por 15 minutos."""
        rates = cache.get('exchange_rates')
        if not rates:
            rates = cls._fetch_live_rates()
            cache.set('exchange_rates', rates, 900) # 15 min
        return rates

    @classmethod
    def _fetch_live_rates(cls):
        """Consulta APIs externas para obtener tasas reales."""
        data = {
            "USD": 1.0,
            "VES": 0.0,
            "BTC": 0.0,
            "ETH": 0.0,
            "timestamp": int(time.time())
        }

        # 1. Binance para Cripto
        try:
            # BTC to USDT (USD)
            btc_resp = requests.get(f"{cls.BINANCE_URL}?symbol=BTCUSDT", timeout=5)
            if btc_resp.status_code == 200:
                data["BTC"] = float(btc_resp.json()["price"])

            # ETH to USDT (USD)
            eth_resp = requests.get(f"{cls.BINANCE_URL}?symbol=ETHUSDT", timeout=5)
            if eth_resp.status_code == 200:
                data["ETH"] = float(eth_resp.json()["price"])
        except Exception as e:
            print(f"Error fetching Binance rates: {e}")

        # 2. Monitor/BCV para VES (Prioriza el valor manual del admin)
        data["VES"] = cls.get_bs_rate()

        return data

def get_current_rates():
    return CurrencyService.get_rates()
