
import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import LoyaltyPoints

print("--- Loyalty Points Report ---")
for lp in LoyaltyPoints.objects.all():
    print(f"ID: {lp.telegram_id} | Points: {lp.puntos} | Level: {lp.nivel}")
print("--- End of Report ---")
