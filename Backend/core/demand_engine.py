import pandas as pd
import numpy as np
from prophet import Prophet
from bot.models import Order
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.utils import timezone
from datetime import timedelta

class DemandForecaster:
    def __init__(self):
        pass

    def get_historical_data(self):
        """
        Obtiene el histórico de pedidos agrupados por hora.
        """
        data = Order.objects.annotate(
            hour=TruncHour('fecha')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')

        if len(data) < 20: # Prophet necesita un mínimo de datos para detectar estacionalidad
            return self._generate_simulated_historical_data()

        df = pd.DataFrame(list(data))
        df.columns = ['ds', 'y']
        # Asegurar que ds no tenga información de zona horaria para Prophet si es necesario
        df['ds'] = df['ds'].dt.tz_localize(None)
        return df

    def _generate_simulated_historical_data(self):
        """Genera datos sintéticos para entrenamiento si no hay suficiente historia."""
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        dates = [now - timedelta(hours=i) for i in range(24 * 14)] # 2 semanas de historia
        
        records = []
        for dt in dates:
            hour = dt.hour
            # Simular picos en almuerzo (12-14) y cena (19-21)
            base = 2
            if 12 <= hour <= 14: base = 15
            if 19 <= hour <= 21: base = 25
            
            # Variación aleatoria
            count = max(0, int(np.random.normal(base, base * 0.2)))
            records.append({'ds': dt.replace(tzinfo=None), 'y': count})
            
        return pd.DataFrame(records).sort_values('ds')

    def forecast_next_24h(self):
        """
        Entrena el modelo y predice las próximas 24 horas.
        """
        df = self.get_historical_data()
        
        # Configuramos Prophet con estacionalidad diaria fuerte
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False
        )
        model.fit(df)
        
        # Crear dataframe para el futuro (24 horas)
        future = model.make_future_dataframe(periods=24, freq='H')
        forecast = model.predict(future)
        
        # Filtrar solo el futuro
        last_date = df['ds'].max()
        future_forecast = forecast[forecast['ds'] > last_date][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        
        # Formatear para API
        results = []
        for _, row in future_forecast.iterrows():
            results.append({
                "hora": row['ds'].strftime("%Y-%m-%d %H:%M"),
                "pedidos_esperados": max(0, round(row['yhat'], 1)),
                "rango_min": max(0, round(row['yhat_lower'], 1)),
                "rango_max": max(0, round(row['yhat_upper'], 1))
            })
            
        return results

def get_demand_forecast():
    forecaster = DemandForecaster()
    return forecaster.forecast_next_24h()
