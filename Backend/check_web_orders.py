
import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import Order

print("--- Web Orders Check (telegram_id=0) ---")
web_orders = Order.objects.filter(telegram_id=0)
for o in web_orders:
    print(f"Order #{o.id} | Status: {o.status} | PaymentData: {o.payment_data}")

print("--- End of Report ---")
