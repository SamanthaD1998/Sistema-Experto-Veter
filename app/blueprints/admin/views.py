from . import admin
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, current_user
from app.models import Usuario  # Asegúrate de que esta importación sea correcta
from werkzeug.security import check_password_hash
from flask_login import UserMixin, logout_user
from app.models import db, Diagnostico,Usuario,Enfermedad,EnfermedadSintoma,Sintoma,Mascota
from flask import jsonify
from sqlalchemy import func, extract
import json
from flask import Flask, make_response
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import datetime
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Spacer

@admin.route('/', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        nombre_usuario = request.form.get('username')
        contrasena = request.form.get('password')

        admin_user = Usuario.query.filter_by(nombre_usuario=nombre_usuario, es_borrado=False).first()  # Asegúrate de que es_borrado está incluido en tu modelo de Usuario
        if admin_user and admin_user.check_password(contrasena) and admin_user.es_admin:
            login_user(admin_user)
            return redirect(url_for('admin.dashboard_view'))
        else:
            flash('Credenciales de administrador inválidas, usuario no es administrador, o la cuenta ha sido desactivada', 'danger')

    return render_template('admin/login_admin.html')


@admin.route('/dashboard')
@login_required
def dashboard_view():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('main.index'))

    # Consulta para obtener la cantidad de usuarios registrados por mes
    usuarios_por_mes = db.session.query(
        func.date_trunc('month', Usuario.fecha_creacion).label('mes'),
        func.count(Usuario.id).label('cantidad')
    ).group_by('mes').order_by('mes').all()

    # Convertir los resultados a un formato adecuado para JSON
    usuarios_por_mes_format = [{'mes': mes.strftime("%B"), 'cantidad': cantidad} for mes, cantidad in usuarios_por_mes]

    usuarios_por_mes_json = json.dumps(usuarios_por_mes_format)
 # Diagnosticos por enfermedad
    diagnosticos_por_enfermedad = db.session.query(
        Enfermedad.nombre,
        func.count(Diagnostico.id).label('cantidad')
    ).join(Diagnostico, Diagnostico.enfermedad_id == Enfermedad.id) \
     .group_by(Enfermedad.nombre).all()

    diagnosticos_por_enfermedad_format = [{'enfermedad': enfermedad, 'cantidad': cantidad} for enfermedad, cantidad in diagnosticos_por_enfermedad]
    diagnosticos_por_enfermedad_json = json.dumps(diagnosticos_por_enfermedad_format)

    return render_template('admin/dashboard.html', usuarios_por_mes_json=usuarios_por_mes_json, diagnosticos_por_enfermedad_json=diagnosticos_por_enfermedad_json)

@admin.route('/manage_diseases')
@login_required
def manage_diseases_view():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('main.index'))

    enfermedades = Enfermedad.query.all()
    enfermedades_data = []

    for enfermedad in enfermedades:
        sintomas_principales = [es.sintoma.nombre for es in enfermedad.enfermedades_sintomas if es.es_principal]
        diagnosticada = Diagnostico.query.filter_by(enfermedad_id=enfermedad.id).first() is not None

        enfermedades_data.append({
            'id': enfermedad.id,
            'nombre': enfermedad.nombre,
            'sintomas_principales': sintomas_principales,
            'diagnosticada': diagnosticada  # Nuevo campo para indicar si la enfermedad ha sido diagnosticada
        })

    return render_template('admin/manage_diseases.html', enfermedades=enfermedades_data)


@admin.route('/add_disease', methods=['GET', 'POST'])
@login_required
def add_disease_view():
    from app.models import Enfermedad, Sintoma, EnfermedadSintoma
    from app.experto.knowledge_base import DiagnosticoSistemaExperto, obtener_datos_enfermedades

    if request.method == 'POST':
        enfermedad_nombre = request.form['disease_name'].strip()
        sintomas_principales = request.form.getlist('main_symptoms[]')
        sintomas_principales_pesos = request.form.getlist('main_symptoms_weight[]')
        sintomas_secundarios = request.form.getlist('secondary_symptoms[]')

        # Verificar si la enfermedad ya existe
        if Enfermedad.query.filter_by(nombre=enfermedad_nombre).first():
            flash('La enfermedad ya está registrada.', 'warning')
            return redirect(url_for('admin.add_disease_view'))

        # Verificar si hay síntomas repetidos
        if set(sintomas_principales) & set(sintomas_secundarios):
            flash('No se pueden agregar síntomas repetidos como principales y secundarios.', 'warning')
            return redirect(url_for('admin.add_disease_view'))

        if not enfermedad_nombre or not sintomas_principales or not sintomas_secundarios:
            flash('Por favor, complete todos los campos requeridos.', 'warning')
            return redirect(url_for('admin.add_disease_view'))
        
        nueva_enfermedad = Enfermedad(nombre=enfermedad_nombre)
        db.session.add(nueva_enfermedad)
        db.session.flush()  # Obtener el ID asignado a la nueva enfermedad

        # Procesar síntomas principales
        procesar_sintomas(sintomas_principales, sintomas_principales_pesos, nueva_enfermedad, True)

        # Procesar síntomas secundarios sin pasar pesos
        procesar_sintomas(sintomas_secundarios, [], nueva_enfermedad, False)

        db.session.commit()

        # Actualizar el sistema experto
        actualizar_sistema_experto()

        flash('Enfermedad agregada correctamente', 'success')
        return redirect(url_for('admin.manage_diseases_view'))

    return render_template('admin/add_disease.html')

def procesar_sintomas(sintomas, pesos_principales, enfermedad, es_principal):
    from app.models import Enfermedad, Sintoma, EnfermedadSintoma

    if es_principal:
        # Procesar síntomas principales
        for i, sintoma_nombre in enumerate(sintomas):
            peso = int(pesos_principales[i])
            _agregar_sintoma(sintoma_nombre, peso, enfermedad, es_principal)
    else:
        # Procesar síntomas secundarios
        peso_total_secundarios = 30  # 30% restante
        num_sintomas_secundarios = len(sintomas)
        for sintoma_nombre in sintomas:
            # Dividir el 30% equitativamente entre los síntomas secundarios
            peso = round(peso_total_secundarios / num_sintomas_secundarios)
            _agregar_sintoma(sintoma_nombre, peso, enfermedad, es_principal)

def _agregar_sintoma(sintoma_nombre, peso, enfermedad, es_principal):
    from app.models import Enfermedad, Sintoma, EnfermedadSintoma
    sintoma = Sintoma.query.filter_by(nombre=sintoma_nombre).first()
    if not sintoma:
        sintoma = Sintoma(nombre=sintoma_nombre)
        db.session.add(sintoma)
        db.session.flush()

    relacion = EnfermedadSintoma(enfermedad_id=enfermedad.id, sintoma_id=sintoma.id, es_principal=es_principal, peso=peso)
    db.session.add(relacion)


def actualizar_sistema_experto():
    from app.models import Enfermedad, Sintoma, EnfermedadSintoma
    from app.experto.knowledge_base import DiagnosticoSistemaExperto, obtener_datos_enfermedades, generar_reglas_dinamicas

    enfermedades_con_sintomas = obtener_datos_enfermedades()
    reglas_dinamicas = generar_reglas_dinamicas(enfermedades_con_sintomas)

    engine = DiagnosticoSistemaExperto()
    engine.reset()

    for enfermedad, reglas in reglas_dinamicas.items():

        pass


@admin.route('/edit_disease/<int:id_enfermedad>', methods=['GET', 'POST'])
@login_required
def edit_disease_view(id_enfermedad):
    enfermedad = Enfermedad.query.get_or_404(id_enfermedad)
    relaciones = EnfermedadSintoma.query.filter_by(enfermedad_id=id_enfermedad).all()

    if request.method == 'POST':
        enfermedad.nombre = request.form['disease_name']

        for relacion in relaciones:
            sintoma_id = relacion.sintoma_id
            nuevo_nombre_sintoma = request.form.get(f'main_symptom_{sintoma_id}', '').strip() or request.form.get(f'secondary_symptom_{sintoma_id}', '').strip()
            peso = request.form.get(f'main_symptom_weight_{sintoma_id}', 0)

            sintoma = Sintoma.query.get(sintoma_id)

            if sintoma.nombre != nuevo_nombre_sintoma:
                # Verifica si el síntoma está asociado con otras enfermedades
                otras_relaciones = EnfermedadSintoma.query.filter(EnfermedadSintoma.sintoma_id == sintoma_id, EnfermedadSintoma.enfermedad_id != id_enfermedad).first()
                if otras_relaciones:
                    # Crea un nuevo síntoma si el nombre ha cambiado y el síntoma está asociado con otras enfermedades
                    nuevo_sintoma = Sintoma(nombre=nuevo_nombre_sintoma)
                    db.session.add(nuevo_sintoma)
                    db.session.flush()  # Para obtener el ID del nuevo síntoma
                    relacion.sintoma_id = nuevo_sintoma.id
                else:
                    # Actualiza el nombre del síntoma si solo está asociado con esta enfermedad
                    sintoma.nombre = nuevo_nombre_sintoma

            if relacion.es_principal:
                relacion.peso = peso

        db.session.commit()
        flash('Enfermedad actualizada exitosamente.', 'success')
        return redirect(url_for('admin.manage_diseases_view'))

    return render_template('admin/edit_disease.html', enfermedad=enfermedad, relaciones=relaciones)

@admin.route('/profile_admin')
@login_required
def profile_admin_view():
    return render_template('admin/profile_admin.html')

@admin.route('/update_profile_admin', methods=['POST'])
@login_required
def update_profile_admin():
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
        return redirect(url_for('admin.profile_admin_view'))

    db.session.commit()
    flash('Tu perfil ha sido actualizado.', 'success')
    return redirect(url_for('admin.profile_admin_view'))

@admin.route('/manage_users')
@login_required
def manage_users_view():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('main.index'))

    # Recupera todos los usuarios que no están marcados como borrados y los ordena por fecha de creación de forma descendente
    usuarios = Usuario.query.filter_by(es_borrado=False).order_by(Usuario.fecha_creacion.asc()).all()
    
    # Pasa los usuarios al template
    return render_template('admin/manage_users.html', usuarios=usuarios)


@admin.route('/edit_user/<int:id_usuario>', methods=['GET', 'POST'])
@login_required
def edit_user_view(id_usuario):
    if not current_user.es_admin:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('admin.dashboard_view'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if request.method == 'POST':
        usuario.nombre_usuario = request.form.get('username')
        usuario.correo = request.form.get('email')
        usuario.es_admin = 'is_admin' in request.form
        contrasena = request.form.get('password')
        confirmar_contrasena = request.form.get('confirm_password')

        if contrasena:
            if contrasena != confirmar_contrasena:
                flash('Las contraseñas no coinciden.', 'danger')
                return redirect(url_for('admin.edit_user_view', id_usuario=id_usuario))
            usuario.set_password(contrasena)

        db.session.commit()
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('admin.manage_users_view'))

    return render_template('admin/edit_user.html', usuario=usuario)


@admin.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user_view():
    if not current_user.es_admin:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('admin.dashboard_view'))

    if request.method == 'POST':
        nombre_usuario = request.form.get('username')
        correo = request.form.get('email')
        contrasena = request.form.get('password')
        confirmar_contrasena = request.form.get('confirm_password')
        es_admin = 'is_admin' in request.form

        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('admin.add_user_view'))

        usuario_existente = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario_existente:
            flash('El nombre de usuario ya está en uso. Por favor elige otro.', 'danger')
            return redirect(url_for('admin.add_user_view'))

        correo_existente = Usuario.query.filter_by(correo=correo).first()
        if correo_existente:
            flash('El correo electrónico ya está en uso. Por favor elige otro.', 'danger')
            return redirect(url_for('admin.add_user_view'))

        nuevo_usuario = Usuario(
            nombre_usuario=nombre_usuario, 
            correo=correo, 
            es_admin=es_admin
        )
        nuevo_usuario.set_password(contrasena)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Usuario creado exitosamente', 'success')
        return redirect(url_for('admin.manage_users_view'))

    return render_template('admin/add_user.html')


@admin.route('/delete_user/<int:id_usuario>', methods=['POST'])
@login_required
def delete_user(id_usuario):
    if not current_user.es_admin:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('admin.manage_users_view'))

    usuario = Usuario.query.get_or_404(id_usuario)
    usuario.es_borrado = True  # Marcar el usuario como eliminado lógicamente
    db.session.commit()
    flash('Usuario eliminado exitosamente.', 'success')
    return redirect(url_for('admin.manage_users_view'))

@admin.route('/delete_disease/<int:id_enfermedad>', methods=['POST'])
@login_required
def delete_disease(id_enfermedad):
    if not current_user.es_admin:
        return jsonify({'error': 'Acceso denegado'}), 403

    enfermedad_a_eliminar = Enfermedad.query.get(id_enfermedad)
    if enfermedad_a_eliminar:
        # Eliminar relaciones EnfermedadSintoma
        relaciones = EnfermedadSintoma.query.filter_by(enfermedad_id=id_enfermedad).all()
        for relacion in relaciones:
            db.session.delete(relacion)

            # Verificar si el síntoma está asociado con otras enfermedades
            otras_relaciones = EnfermedadSintoma.query.filter(EnfermedadSintoma.sintoma_id == relacion.sintoma_id, EnfermedadSintoma.enfermedad_id != id_enfermedad).first()
            if not otras_relaciones:
                # Si el síntoma no está asociado con otras enfermedades, elimínalo
                sintoma_a_eliminar = Sintoma.query.get(relacion.sintoma_id)
                db.session.delete(sintoma_a_eliminar)

        # Eliminar la enfermedad
        db.session.delete(enfermedad_a_eliminar)
        
        # Confirma todos los cambios en la base de datos
        db.session.commit()
        return jsonify({'success': 'Enfermedad y síntomas asociados eliminados con éxito.'}), 200
    else:
        return jsonify({'error': 'Enfermedad no encontrada.'}), 404
    

@admin.route('/generate_report')
@login_required
def generate_report():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Título del reporte y fecha
    report_title = 'Reporte de Usuarios Registrados - Dog-Dialog'
    fecha_reporte = datetime.now().strftime("%Y-%m-%d")

    # Preparación de datos para la tabla
    table_data = [['ID', 'Nombre', 'Correo', 'Fecha de Creación']]
    usuarios = Usuario.query.all()
    for usuario in usuarios:
        table_data.append([usuario.id, usuario.nombre_usuario, usuario.correo, usuario.fecha_creacion.strftime("%Y-%m-%d")])

    # Elementos del documento
    elements = []
    elements.append(Paragraph(report_title, getSampleStyleSheet()['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f'Fecha: {fecha_reporte}', getSampleStyleSheet()['Normal']))
    elements.append(Spacer(1, 12))
    
    # Crear y añadir la tabla
    table = Table(table_data)
    table.setStyle(TableStyle([('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                               ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                               ('BACKGROUND', (0,0), (-1,0), colors.grey)]))
    elements.append(table)

    # Construir documento
    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    buffer.close()
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_usuarios_{fecha_reporte}.pdf'
    return response

@admin.route('/generate_diagnostics_report')
@login_required
def generate_diagnostics_report():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Título y fecha del reporte
    report_title = 'Reporte de Diagnósticos - Dog-Dialog'
    fecha_reporte = f'Fecha: {datetime.now().strftime("%Y-%m-%d")}'

    # Datos de la tabla
    table_data = [['ID Diagnóstico', 'Usuario', 'Mascota', 'Enfermedad', 'Porcentaje', 'Fecha']]
    diagnosticos = Diagnostico.query.all()
    for diagnostico in diagnosticos:
        usuario = Usuario.query.get(diagnostico.usuario_id).nombre_usuario if Usuario.query.get(diagnostico.usuario_id) else "Desconocido"
        mascota = Mascota.query.get(diagnostico.id_mascota).nombre if Mascota.query.get(diagnostico.id_mascota) else "Desconocida"
        enfermedad = Enfermedad.query.get(diagnostico.enfermedad_id).nombre if Enfermedad.query.get(diagnostico.enfermedad_id) else "Desconocida"
        table_data.append([diagnostico.id,usuario,mascota, enfermedad, f'{diagnostico.porcentaje}%', diagnostico.fecha_creacion.strftime('%Y-%m-%d')])

    # Configuración del documento
    elements = []
    elements.append(Paragraph(report_title, getSampleStyleSheet()['Title']))
    elements.append(Paragraph(fecha_reporte, getSampleStyleSheet()['Normal']))
    elements.append(Spacer(1, 12))

    # Creación de la tabla
    table = Table(table_data)
    table.setStyle(TableStyle([('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                               ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                               ('BACKGROUND', (0,0), (-1,0), colors.grey)]))
    elements.append(table)

    # Construcción y respuesta del documento
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    buffer.close()
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_diagnosticos.pdf'
    return response



@admin.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('admin.login_admin'))


