
import os
import sys
import django

# Add the project root to sys.path
# Assuming this script is in Backend/scripts/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from core.models import Table

def init_tables():
    print("Initializing tables...")
    for i in range(1, 6):
        table, created = Table.objects.get_or_create(number=i)
        if created:
            print(f"Created Table {i}")
        else:
            print(f"Table {i} already exists")
            
    print("Tables initialized successfully.")

if __name__ == "__main__":
    init_tables()
