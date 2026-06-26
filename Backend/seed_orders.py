import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from bot.models import Order
from core.models import Product

def seed_orders():
    print("Generating historical orders...")
    
    products_db = list(Product.objects.all())
    if not products_db:
        print("Error: No products in database to create orders from.")
        return

    # 1. Generate Orders for the last 60 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=60)
    
    orders_created = 0
    
    current_date = start_date
    while current_date <= end_date:
        # Determine number of orders for this day (Random but realistic: 5 to 20)
        # Weekends have more orders
        is_weekend = current_date.weekday() >= 5
        num_orders = random.randint(8, 25) if is_weekend else random.randint(3, 12)
        
        for _ in range(num_orders):
            product = random.choice(products_db)
            
            # Create Order
            order = Order(
                telegram_id=random.randint(1000000, 9999999),
                # Removed chat_id as it does not exist in the model
                item=product.name,
                precio=product.price, 
                customer_name=f"Cliente {random.randint(1, 100)}",
                currency="USD",
                status="completado",
                payment_status="payment_approved",
                service_type=random.choice(["LLEVAR", "AQUI", "AQUI"]), # Fixed choices based on model
                delivery_mode=random.choice(["RETIRO", "DELIVERY"]) if random.random() > 0.5 else None
            )
            # Need to save first to set ID (though not used for Date), then update fecha
            order.save()
            
            # Update fecha manually since auto_now_add=True prevents setting it on init
            order.fecha = current_date.replace(hour=random.randint(11, 22), minute=random.randint(0, 59))
            order.save(update_fields=['fecha'])
            
            orders_created += 1
            
        current_date += timedelta(days=1)

    print(f"Successfully created {orders_created} orders from {start_date.date()} to {end_date.date()}.")

if __name__ == "__main__":
    seed_orders()
