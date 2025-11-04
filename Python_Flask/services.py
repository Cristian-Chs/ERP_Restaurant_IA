# services.py
from models import Usuario

def buscar_usuario_por_correo(email):
    return Usuario.query.filter_by(email=email).first()

def verificar_contraseña(password_ingresada, password_guardada):
    from werkzeug.security import check_password_hash
    return check_password_hash(password_guardada, password_ingresada)

