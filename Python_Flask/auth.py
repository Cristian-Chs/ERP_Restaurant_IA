# auth.py
from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, datetime
from models import Usuario, db
from functools import wraps

app = Flask(__name__)
CORS(app)
SECRET_KEY = '1234'

auth_bp = Blueprint('auth', __name__)
cliente_bp = Blueprint('cliente', __name__)

# Decorador para proteger rutas por rol
def requiere_rol(rol_requerido):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({"msg": "Token requerido"}), 403
            try:
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

# Registro
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = generate_password_hash(data['password'])  # ← usa 'password'
    nuevo_usuario = Usuario(
        nombre=data['nombre'],
        email=data['email'],              # ← usa 'email'
        password=hashed_pw,               # ← usa 'password'
        rol=data['rol']
    )
    db.session.add(nuevo_usuario)
    db.session.commit()
    return jsonify({"msg": "Usuario registrado"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = Usuario.query.filter_by(email=data['email']).first()  # ← usa 'email'

    if not usuario:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    if not check_password_hash(usuario.password, data['password']):  # ← usa 'password'
        return jsonify({"msg": "Contraseña incorrecta"}), 401

    try:
        token = jwt.encode({
            'id': usuario.id,
            'rol': usuario.rol,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, SECRET_KEY, algorithm='HS256')

        if isinstance(token, bytes):
            token = token.decode('utf-8')

        return jsonify({"token": token}), 200
    except Exception as e:
        print("Error al generar el token:", e)
        return jsonify({"msg": "Error interno"}), 500   


# Ruta protegida para cliente
@cliente_bp.route('/menu', methods=['GET'])
@requiere_rol('cliente')
def menu_cliente():
    return jsonify({"msg": "Menú del cliente"}), 200

# Registro de blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(cliente_bp, url_prefix='/api/cliente')

if __name__ == '__main__':
    app.run(debug=True)
