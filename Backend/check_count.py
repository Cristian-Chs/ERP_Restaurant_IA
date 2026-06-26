import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from bot.models import Order

count = Order.objects.count()
print(f"Total Orders in DB: {count}")
