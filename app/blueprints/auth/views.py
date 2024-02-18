from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from app.models import Usuario  
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for, redirect
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from app import mail
from . import auth
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask import current_app
import re

@auth.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        nombre_usuario = request.form.get('username')
        contrasena = request.form.get('password')

        # Agregar verificación para asegurarse de que es_borrado no sea True
        user = Usuario.query.filter_by(nombre_usuario=nombre_usuario, es_borrado=False).first()

        if user and user.check_password(contrasena):
            login_user(user)
            return redirect(url_for('diagnosis.info_view'))
        else:
            flash('Nombre de usuario o contraseña inválidos', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

def register_view():
    if request.method == 'POST':
        nombre_usuario = request.form.get('username')  # Cambiado a nombre_usuario
        correo = request.form.get('email')  # Cambiado a correo
        contrasena = request.form.get('password')  # Cambiado a contrasena
        confirmar_contrasena = request.form.get('confirm_password')  # Cambiado a confirmar_contrasena

        # Verificar que el usuario no exista ya
        user = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()  # Cambiado a nombre_usuario
        if user:
            flash('El nombre de usuario ya está en uso. Por favor elige otro.', 'danger')
            return redirect(url_for('auth.register'))

        # Verificar que el email no exista ya
        user = Usuario.query.filter_by(correo=correo).first()  # Cambiado a correo
        if user:
            flash('El email ya está en uso. Por favor elige otro.', 'danger')
            return redirect(url_for('auth.register'))

        # Verificar que las contraseñas coincidan
        if contrasena != confirmar_contrasena:  # Cambiado a contrasena y confirmar_contrasena
            flash('Las contraseñas no coinciden. Por favor verifica e intenta de nuevo.', 'danger')
            return redirect(url_for('auth.register'))
        
        """contrasena_regex = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
        if not re.match(contrasena_regex, contrasena):
            flash('La contraseña debe tener al menos 8 caracteres, incluir un número y un carácter especial.', 'danger')
            return redirect(url_for('auth.register'))"""

        # Crear el usuario y añadirlo a la base de datos
        new_user = Usuario(nombre_usuario=nombre_usuario, correo=correo)  # Cambiado a nombre_usuario y correo
        new_user.set_password(contrasena)  # Cambiado a contrasena
        db.session.add(new_user)
        db.session.commit()

        flash('Te has registrado exitosamente!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request_view():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(correo=email).first()
        if user:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.id, salt='reset-password')
            msg = Message('Restablecer Contraseña', sender=current_app.config['MAIL_DEFAULT_SENDER'], recipients=[email])
            link = url_for('auth.reset_password_view', token=token, _external=True)
            msg.body = f'Para restablecer tu contraseña, visita el siguiente enlace: {link}'
            mail.send(msg)
            flash('Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña.', 'info')
        else:
            flash('No se encontró una cuenta con esa dirección de correo electrónico.', 'danger')
    return render_template('auth/reset_password_request.html')



@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_view(token):
    try:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        user_id = s.loads(token, salt='reset-password', max_age=3600)
    except SignatureExpired:
        flash('El enlace es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        new_password = request.form.get('password')
        user = Usuario.query.get(user_id)
        if user:
            user.set_password(new_password)
            db.session.commit()
            flash('Tu contraseña ha sido actualizada.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)


@login_required
def logout_view():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('main.index'))
