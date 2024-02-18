from flask import Blueprint
from .views import profile_view, user_dashboard_view

user = Blueprint('user', __name__, url_prefix='/user')

# Perfil del usuario
user.add_url_rule('/profile', 'profile', profile_view, methods=['GET', 'POST'])

# Panel de control del usuario
user.add_url_rule('/dashboard', 'dashboard', user_dashboard_view)

# Puedes agregar más rutas según lo necesites, como para ver el historial de diagnósticos.
