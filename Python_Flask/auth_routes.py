from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from services import buscar_usuario_por_correo, verificar_contraseña

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    usuario = buscar_usuario_por_correo(email)
    if not usuario or not verificar_contraseña(password, usuario.password):
        return jsonify({"msg": "Credenciales inválidas"}), 401

    token = jwt.encode({
        "id": usuario.id,
        "rol": usuario.rol,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({"token": token})
