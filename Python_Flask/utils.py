# utils.py
from functools import wraps
from flask import request, jsonify
import jwt
from auth import SECRET_KEY

def requiere_rol(rol_requerido):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Permitir solicitudes OPTIONS sin validar token (CORS preflight)
            if request.method == 'OPTIONS':
                return f(*args, **kwargs)

            token = request.headers.get('Authorization')
            if not token:
                return jsonify({"msg": "Token requerido"}), 403

            try:
                # Extraer token si viene como "Bearer <token>"
                token = token.split(" ")[1] if " " in token else token
                data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

                if data['rol'] != rol_requerido:
                    return jsonify({"msg": "Acceso denegado"}), 403

            except Exception as e:
                print("Error al verificar token:", e)
                return jsonify({"msg": "Token inválido"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorador
