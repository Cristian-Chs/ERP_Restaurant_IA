# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)         # ← antes era 'correo'
    password = db.Column(db.String(100), nullable=False)       # ← antes era 'contrasena'
    rol = db.Column(db.String(20), nullable=False)
