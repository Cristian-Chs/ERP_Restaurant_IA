# admin_routes.py
from flask import Blueprint
from utils import requiere_rol

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/crear-platillo', methods=['POST'])
@requiere_rol('admin')
def crear_platillo():
    # lógica para crear platillo
    return {"msg": "Platillo creado"}
