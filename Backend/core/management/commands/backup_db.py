from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Crea un backup de la base de datos (PostgreSQL o SQLite)'

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        db_conf = settings.DATABASES['default']
        engine = db_conf['ENGINE']
        db_name = db_conf['NAME']

        self.stdout.write(f"📦 Iniciando backup de {db_name} ({engine})...")

        if 'postgresql' in engine:
            filename = f"backup_{db_name}_{timestamp}.sql"
            filepath = os.path.join(backup_dir, filename)
            
            # Construir comando pg_dump
            # Requiere que pg_dump esté en el PATH o configurar ruta
            env = os.environ.copy()
            env['PGPASSWORD'] = db_conf['PASSWORD']
            
            user = db_conf['USER']
            host = db_conf['HOST']
            port = db_conf['PORT']
            
            cmd = f'pg_dump -h {host} -p {port} -U {user} -F c -b -v -f "{filepath}" {db_name}'
            
            try:
                self.stdout.write("Ejecutando pg_dump...")
                # Usamos os.system o subprocess
                import subprocess
                result = subprocess.run(cmd, shell=True, env=env, check=True)
                self.stdout.write(self.style.SUCCESS(f"✅ Backup creado exitosamente: {filepath}"))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"❌ Error al crear backup de Postgres: {e}"))
                self.stdout.write("Asegúrate de que 'pg_dump' está instalado y en el PATH del sistema.")

        elif 'sqlite3' in engine:
            filename = f"backup_{db_name}_{timestamp}.sqlite3"
            # db_name es la ruta al archivo en sqlite
            import shutil
            try:
                shutil.copy2(db_name, os.path.join(backup_dir, filename))
                self.stdout.write(self.style.SUCCESS(f"✅ Backup de SQLite creado: {filename}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error al copiar SQLite: {e}"))
        
        else:
            # Fallback a dumpdata de Django (JSON) - Funciona para cualquier DB
            filename = f"dump_{timestamp}.json"
            filepath = os.path.join(backup_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                call_command('dumpdata', stdout=f)
            self.stdout.write(self.style.SUCCESS(f"✅ Data dump (JSON) creado: {filepath}"))
