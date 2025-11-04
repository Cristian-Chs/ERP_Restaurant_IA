# cliente_routes.py
from flask import Blueprint, jsonify
from utils import requiere_rol


cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/hacer-pedido', methods=['POST'])
@requiere_rol('cliente')
def hacer_pedido():
    # lógica para hacer pedido
    return {"msg": "Pedido recibido"}

@cliente_bp.route('/menu', methods=['GET'])
@requiere_rol('cliente')
def menu_cliente():
    return jsonify(obtener_menu())

# menu.py (opcional)
def obtener_menu():
    return {
        "platillos": [
            { "id": 1, "nombre": "Pizza", "descripcion": "Deliciosa pizza de queso", "precio": 100, "imagen": "pizza" },
            { "id": 2, "nombre": "Sushi", "descripcion": "Sushi fresco de salmón", "precio": 120, "imagen": "sushi" }
        ],
        "entradas": [
            { "id": 3, "nombre": "Tequeño", "descripcion": "Palitos de masa rellenos de queso blanco", "precio": 1, "imagen": "TEQUEÑOS" },
            { "id": 4, "nombre": "Mini Empanada", "descripcion": "Empanadas pequeñas de carne, pollo y queso", "precio": 1, "imagen": "empanada" }
        ],
        "principales": [
            { "id": 5, "nombre": "Asado negro", "descripcion": "Carne de res cocida en salsa dulce oscura", "precio": 1, "imagen": "asado" },
            { "id": 6, "nombre": "Pollo a la brasa", "descripcion": "Pollo marinado y cocido al carbón", "precio": 1, "imagen": "pollo" }
        ],
        "postres": [
            { "id": 7, "nombre": "Quesillo", "descripcion": "Postre cremoso tipo flan", "precio": 1, "imagen": "quesillo" },
            { "id": 8, "nombre": "Torta de zanahoria", "descripcion": "Bizcocho dulce con zanahoria y especias", "precio": 1, "imagen": "torta de zanahoria" }
        ],
        "bebidas": [
            { "id": 9, "nombre": "Jugo de parchita", "descripcion": "Refrescante jugo natural de maracuyá", "precio": 1, "imagen": "jugo de parchita" },
            { "id": 10, "nombre": "Cerveza Polar", "descripcion": "Cerveza venezolana clásica", "precio": 1, "imagen": "cerveza" }
        ]
    }
