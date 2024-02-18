from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

# Instancias
db = SQLAlchemy()
login_manager = LoginManager()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)  # Cambiado a nombre_usuario
    correo = db.Column(db.String(100), unique=True, nullable=False)  # Cambiado a correo
    contrasena = db.Column(db.String(255))  # Cambiado a contrasena_hash
    es_admin = db.Column(db.Boolean, default=False)  # Cambiado a es_admin
    es_borrado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)  # Añadido fecha_creacion

    def set_password(self, password):
        self.contrasena = generate_password_hash(password)  # Corregido aquí


    def check_password(self, password):
        return check_password_hash(self.contrasena, password)  # Corregido aquí
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Usuario.query.get(user_id)

class Enfermedad(db.Model):
    __tablename__ = 'enfermedades'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    enfermedades_sintomas = db.relationship('EnfermedadSintoma', backref='enfermedad', lazy=True)

class Sintoma(db.Model):
    __tablename__ = 'sintomas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    enfermedades_sintomas = db.relationship('EnfermedadSintoma', backref='sintoma', lazy=True)

class EnfermedadSintoma(db.Model):
    __tablename__ = 'enfermedades_sintomas'
    enfermedad_id = db.Column(db.Integer, db.ForeignKey('enfermedades.id'), primary_key=True)
    sintoma_id = db.Column(db.Integer, db.ForeignKey('sintomas.id'), primary_key=True)
    peso = db.Column(db.Integer, nullable=False, default=0)
    es_principal = db.Column(db.Boolean, nullable=False)

class Mascota(db.Model):
    __tablename__ = 'mascotas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('mascotas', lazy=True))

class Diagnostico(db.Model):
    __tablename__ = 'diagnosticos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    enfermedad_id = db.Column(db.Integer, db.ForeignKey('enfermedades.id'), nullable=False)
    id_mascota = db.Column(db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    porcentaje = db.Column(db.Numeric(5,2), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('diagnosticos', lazy=True))
    enfermedad = db.relationship('Enfermedad', backref=db.backref('diagnosticos', lazy=True))
    mascota = db.relationship('Mascota', backref=db.backref('diagnosticos', lazy=True))


def obtener_sintomas_unicos():
    return Sintoma.query.distinct(Sintoma.nombre).order_by(Sintoma.nombre).all()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def init_models(app):
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Especifica la vista para el login

    with app.app_context():
        db.create_all()  # crea las tablas si no existen

def setup_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen

def setup_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Actualiza este valor según corresponda

