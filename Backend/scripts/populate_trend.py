import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django to run standalone
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import Order

def run():
    print("🚀 Generando datos de prueba para Tendencia ALTA...")
    
    # Generar 5 pedidos con montos ascendentes en los últimos 5 días
    # Esto creará una pendiente positiva perfecta para el modelo de regresión
    montos = [150.00, 300.00, 550.00, 800.00, 1200.00]
    
    base_date = datetime.now()
    
    for i, monto in enumerate(montos):
        # Fechas: Hace 4 días -> Hoy
        fecha_simulada = base_date - timedelta(days=(4 - i))
        
        order = Order.objects.create(
            telegram_id=88888888, # ID falso
            item="prueba_tendencia alta",
            precio=monto,
            status="listo",
            payment_status="payment_approved",
            service_type="DELIVERY"
            # La fecha se pone automática en auto_now_add, hay que forzarla después
        )
        
        # Sobreescribir fecha para simular historial
        order.fecha = fecha_simulada
        order.save()
        
        print(f"✅ Pedido creado: {fecha_simulada.strftime('%Y-%m-%d')} - ${monto}")
        
    print("\n✨ Datos generados. La IA debería detectar ahora una tendencia al ALZA.")

if __name__ == "__main__":
    run()
