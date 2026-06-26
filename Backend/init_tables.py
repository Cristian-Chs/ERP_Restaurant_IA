import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Table

def init_tables():
    print("Checking tables...")
    count = Table.objects.count()
    if count < 5:
        print(f"Found {count} tables. Creating up to 5...")
        for i in range(1, 6):
            obj, created = Table.objects.get_or_create(number=i)
            if created:
                print(f"Created Table {i}")
            else:
                print(f"Table {i} exists")
    else:
        print(f"Found {count} tables. No action needed.")

if __name__ == "__main__":
    init_tables()
