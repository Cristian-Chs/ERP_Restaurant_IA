"""
Script para verificar que las variables de entorno se cargan correctamente.
"""
import os
import sys

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(__file__))

# Intentar cargar .env si python-dotenv está disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv cargado")
except ImportError:
    print("⚠️  python-dotenv no instalado (opcional)")
    print("   Las variables se cargarán del sistema o .env manualmente")

# Verificar variables críticas
print("\n🔍 Verificando variables de entorno:\n")

variables = {
    "DJANGO_SECRET_KEY": "Django Secret Key",
    "DEBUG": "Debug Mode",
    "DB_PASSWORD": "Database Password",
    "BOT_TOKEN_CLIENTE": "Telegram Bot Token",
    "GROQ_API_KEY": "Groq API Key",
    "OCR_API_KEY": "OCR API Key",
}

all_ok = True
for var, description in variables.items():
    value = os.getenv(var)
    if value:
        # Mostrar solo primeros caracteres para seguridad
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ {description:25} = {masked}")
    else:
        print(f"❌ {description:25} = NO CONFIGURADO")
        all_ok = False

print("\n" + "="*60)
if all_ok:
    print("✅ TODAS las variables están configuradas correctamente")
    print("   El proyecto debería funcionar sin problemas")
else:
    print("❌ FALTAN variables de entorno")
    print("   Asegúrate de tener un archivo .env en la raíz del proyecto")
    print("   Puedes copiar .env.example y completar los valores")

print("="*60)
