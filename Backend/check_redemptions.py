
import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import RedeemedCoupon, Order

print("--- Redeemed Coupons History ---")
for rc in RedeemedCoupon.objects.all():
    order_info = f"Order: {rc.order.id}" if rc.order else "No Order"
    print(f"ID: {rc.id} | TelegramID: {rc.telegram_id} | Coupon: {rc.coupon.code} | {order_info}")
    if rc.order and rc.order.payment_data:
        print(f"  Payment Data: {rc.order.payment_data}")

print("--- End of Report ---")
