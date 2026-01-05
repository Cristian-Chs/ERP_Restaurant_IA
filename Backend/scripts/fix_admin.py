import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User

try:
    u, c = User.objects.get_or_create(username='admin')
    u.set_password('password')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print("SUCCESS_ADMIN_FIX")
except Exception as e:
    print(f"FAILED_ADMIN_FIX: {e}")
