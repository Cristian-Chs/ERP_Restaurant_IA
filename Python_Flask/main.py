from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from auth import auth_bp  # si tienes Blueprint para auth
from admin_routes import admin_bp  # si tienes rutas protegidas
from cliente_routes import cliente_bp  # si tienes rutas cliente

app = Flask(__name__)
CORS(app)

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tu_base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '1234' #'clave_super_segura'

db.init_app(app)

# Ruta de prueba
@app.route('/api/saludo')
def saludo():
    return jsonify({"mensaje": "Bienvenido a 4to Sabores Restaurant 👍"})

# Registrar Blueprints si los tienes
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(cliente_bp, url_prefix='/api/cliente')

# Crear tablas si no existen
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5000)
