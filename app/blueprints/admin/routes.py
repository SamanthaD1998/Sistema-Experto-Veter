from flask import Blueprint
from .views import (login_admin, dashboard_view, manage_diseases_view, 
                    profile_admin_view, manage_users_view,edit_disease_view,add_disease_view, add_user_view, edit_user_view)

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Inicio de sesión del Administrador
admin.add_url_rule('/', 'login_admin', login_admin, methods=['GET', 'POST'])

# Dashboard
admin.add_url_rule('/dashboard', 'dashboard', dashboard_view)

# Gestionar enfermedades
admin.add_url_rule('/manage_diseases', 'manage_diseases', manage_diseases_view)

# Gestionar síntomas
admin.add_url_rule('/profile_admin', 'profile_admin', profile_admin_view)

# Gestionar usuarios
admin.add_url_rule('/manage_users', 'manage_users', manage_users_view)

admin.add_url_rule('/edit_disease', 'edit_disease', edit_disease_view)

admin.add_url_rule('/add_disease', 'add_disease', add_disease_view)

admin.add_url_rule('/add_user', 'add_user', add_user_view)

admin.add_url_rule('/edit_user', 'edit_user', edit_user_view)
