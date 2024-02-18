from flask import Blueprint
from .views import login_view, register_view, reset_password_view, logout_view,reset_password_request_view
from . import auth

#auth = Blueprint('auth', __name__, url_prefix='/auth')

# Iniciar sesión
auth.add_url_rule('/login', 'login', login_view, methods=['GET', 'POST'])

# Registrarse
auth.add_url_rule('/register', 'register', register_view, methods=['GET', 'POST'])

# Restablecer contraseña
auth.add_url_rule('/reset_password', 'reset_password', reset_password_view, methods=['GET', 'POST'])

auth.add_url_rule('/reset_password_request', 'reset_password_request', reset_password_request_view, methods=['GET', 'POST'])

# Cerrar sesión
auth.add_url_rule('/logout', 'logout', logout_view)
