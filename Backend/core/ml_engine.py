import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from bot.models import OrderItem
from core.models import Product
from django.db.models import Sum

class PriceOptimizer:
    def __init__(self, product_id):
        self.product_id = product_id
        try:
            self.product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            self.product = None

    def get_historical_data(self):
        """
        Obtiene el histórico de ventas agrupado por precio para analizar la demanda.
        """
        # Agrupamos ventas por precio capturado y sumamos cantidades
        ventas = OrderItem.objects.filter(product_id=self.product_id).values('precio_unitario').annotate(
            total_qty=Sum('cantidad')
        ).order_by('precio_unitario')
        
        if not ventas or len(ventas) < 2:
            # Datos insuficientes para ML real, simulamos una curva de demanda base
            # para demostrar la funcionalidad si el negocio es nuevo.
            return self._generate_simulated_data()
        
        df = pd.DataFrame(list(ventas))
        df.columns = ['price', 'quantity']
        return df

    def _generate_simulated_data(self):
        """Genera datos sintéticos si no hay suficiente historia."""
        base_price = float(self.product.price) if self.product else 10.0
        prices = np.array([base_price * 0.8, base_price * 0.9, base_price, base_price * 1.1, base_price * 1.2])
        # Curva de demanda inversa simple: a mayor precio, menor cantidad
        quantities = np.array([50, 45, 40, 32, 25]) 
        return pd.DataFrame({'price': prices, 'quantity': quantities})

    def suggest_optimal_price(self):
        if not self.product:
            return None

        df = self.get_historical_data()
        
        # Modelo de Regresión Lineal: Cantidad = m * Precio + b
        X = df[['price']].values
        y = df['quantity'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Coeficientes: Cantidad = slope * P + intercept
        slope = model.coef_[0]
        intercept = model.intercept_
        
        # Costo unitario (si no está definido, asumimos 40% del precio actual)
        cost = float(self.product.cost_price) if self.product.cost_price > 0 else float(self.product.price) * 0.4
        
        # Función de Beneficio: Profit = (P - Cost) * (slope * P + intercept)
        # Es una parábola: Profit = slope*P^2 + (intercept - slope*Cost)*P - Cost*intercept
        # El máximo de una parábola ax^2 + bx + c está en x = -b / (2a)
        
        a = slope
        b = intercept - (slope * cost)
        
        if a >= 0:
            # Si el slope es positivo (raro, demanda sube con precio), sugerimos margen fijo
            return float(self.product.price) * 1.05 
            
        optimal_price = -b / (2 * a)
        
        # Validaciones de seguridad para la sugerencia
        current_price = float(self.product.price)
        # No sugerir cambios de más del 30% de golpe para evitar espantar clientes
        optimal_price = max(current_price * 0.7, min(current_price * 1.3, optimal_price))
        
        return round(optimal_price, 2)

def get_price_suggestion(product_id):
    optimizer = PriceOptimizer(product_id)
    return optimizer.suggest_optimal_price()
