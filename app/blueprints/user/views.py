from flask import render_template
from flask_login import login_required, current_user
from . import user  
from flask import flash, redirect, url_for, request
from app.models import Usuario
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

@user.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_view():
    return render_template('user/profile.html')

@user.route('/dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard_view():
    # Código para la vista del panel de usuario
    return render_template('user/user_dashboard.html')

@user.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    user = current_user
    user.nombre_usuario = request.form['nombre_usuario']
    user.correo = request.form['correo']

    # Obtener la nueva contraseña y la confirmación de la contraseña del formulario
    nueva_contrasena = request.form.get('contrasena')
    confirmar_contrasena = request.form.get('confirmar_contrasena')

    # Verificar si se proporcionó una nueva contraseña y si coincide con la confirmación
    if nueva_contrasena and nueva_contrasena == confirmar_contrasena:
        # Actualizar la contraseña utilizando el método set_password del modelo Usuario
        user.set_password(nueva_contrasena)
    elif nueva_contrasena:
        # Si se proporcionó una contraseña pero no coincide con la confirmación
        flash('Las contraseñas no coinciden.', 'danger')
        return redirect(url_for('user.profile_view'))

    db.session.commit()
    flash('Tu perfil ha sido actualizado.', 'success')
    return redirect(url_for('user.profile_view'))


