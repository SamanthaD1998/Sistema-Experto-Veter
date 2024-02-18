from flask import Blueprint, flash,render_template, redirect, url_for, request,jsonify,session
from flask_login import login_required,current_user
from app.experto.diagnosis_helper import procesar_entrada_formulario, obtener_diagnostico
from app.models import Sintoma,Enfermedad,Diagnostico,db,obtener_sintomas_unicos,Mascota
from app.experto.knowledge_base import DiagnosticoSistemaExperto, EnfermedadFact
from app.experto.diagnosis_helper import obtener_datos_enfermedades, generar_reglas_dinamicas


diagnosis = Blueprint('diagnosis', __name__, url_prefix='/diagnosis')

@login_required
@diagnosis.route('/enter-symptoms', methods=['GET', 'POST'])
def enter_symptoms_view():
    id_mascota_seleccionada = session.get('mascota_seleccionada_id')
    sintomas = obtener_sintomas_unicos()
    mensaje_error = None  

    if request.method == 'POST':
        form_data = request.form
        sintomas_seleccionados = procesar_entrada_formulario(form_data)
        num_sintomas = len(sintomas_seleccionados)

        if num_sintomas < 2:
            mensaje_error = 'Por favor, selecciona al menos 2 síntomas.'
        elif num_sintomas > 7:
            mensaje_error = 'Por favor, selecciona máximo 7 síntomas.'
        else:
            # Almacena los síntomas seleccionados en la sesión para poder acceder a ellos más tarde
            session['sintomas_seleccionados'] = sintomas_seleccionados

            # Aquí continúa tu lógica existente, por ejemplo, calcular el diagnóstico principal
            diagnostico, diagnosticos_alternativos = obtener_diagnostico(sintomas_seleccionados)
            session['diagnosticos_alternativos'] = diagnosticos_alternativos
            return redirect(url_for('diagnosis.results_view', diagnostico=diagnostico))

    return render_template('diagnosis/enter_symptoms.html', sintomas=sintomas, mensaje_error=mensaje_error)

@diagnosis.route('/re-diagnosticar', methods=['POST'])
@login_required
def re_diagnosticar():
    id_mascota_seleccionada = session.get('mascota_seleccionada_id')
    # Extraer los síntomas seleccionados del formulario
    sintomas_seleccionados = []
    for key in request.form:
        if key.startswith('sintoma_') and request.form[key] == 'on':
            sintoma = key.replace('sintoma_', '')
            sintomas_seleccionados.append(sintoma)

    if not sintomas_seleccionados:
        flash('Por favor, selecciona al menos un síntoma.', 'warning')
        return redirect(url_for('diagnosis.enter_symptoms_view'))

    # Obtener el nuevo diagnóstico basado en los síntomas seleccionados
    diagnostico, diagnosticos_alternativos = obtener_diagnostico(sintomas_seleccionados)

    # Almacenar los resultados en la sesión para acceder a ellos en la vista de resultados
    session['diagnostico'] = diagnostico
    session['diagnosticos_alternativos'] = diagnosticos_alternativos

    # Redirigir a la página de resultados con el nuevo diagnóstico
    return redirect(url_for('diagnosis.results_view',diagnostico=diagnostico))

@login_required
@diagnosis.route('/results')
def results_view():
    
    diagnostico_completo = request.args.get('diagnostico', 'No se pudo determinar un diagnóstico.')

    diagnosticos_alternativos = session.get('diagnosticos_alternativos', [])  

    enfermedad_nombre, probabilidad = diagnostico_completo.split(' (Probabilidad: ') if 'Probabilidad' in diagnostico_completo else (diagnostico_completo, '')

# Guardar diagnóstico en la base de datos
    if 'Probabilidad' in diagnostico_completo:
        enfermedad = Enfermedad.query.filter_by(nombre=enfermedad_nombre).first()
        id_mascota = session['mascota_seleccionada_id'] 
        nuevo_diagnostico = Diagnostico(
            usuario_id=current_user.id if current_user.is_authenticated else None,
            id_mascota=id_mascota,
            enfermedad_id=enfermedad.id if enfermedad else None,
            porcentaje=probabilidad.replace('%)', '') 
        )
        db.session.add(nuevo_diagnostico)
        db.session.commit()

    return render_template('diagnosis/results.html', enfermedad=enfermedad_nombre, probabilidad=probabilidad , diagnosticos_alternativos=diagnosticos_alternativos)


@login_required
@diagnosis.route('/record')
def record_view():
    # Obtener los diagnósticos del usuario actual
    diagnosticos = Diagnostico.query.filter_by(usuario_id=current_user.id).order_by(Diagnostico.fecha_creacion.desc()).all()

    return render_template('diagnosis/record.html', diagnosticos=diagnosticos)

@login_required
@diagnosis.route('/select_pet', methods=['GET', 'POST'])
def select_pet_view():
    mascotas = Mascota.query.filter_by(usuario_id=current_user.id).all()

    if request.method == 'POST':
        id_mascota_seleccionada = request.form.get('mascotaSeleccionada')
        if id_mascota_seleccionada:
            # Guarda el ID de la mascota seleccionada en la sesión para usarlo más tarde
            session['mascota_seleccionada_id'] = id_mascota_seleccionada
            # Redirige al usuario a la página de selección de síntomas
            return redirect(url_for('diagnosis.enter_symptoms_view'))

    return render_template('diagnosis/select_pet.html', mascotas=mascotas)

@login_required
@diagnosis.route('/register_pet', methods=['POST'])
def register_pet():
    nombre_mascota = request.form.get('nombreMascota')

    # Verifica si ya existe una mascota con ese nombre para el usuario actual
    mascota_existente = Mascota.query.filter_by(usuario_id=current_user.id, nombre=nombre_mascota).first()

    if mascota_existente:
        # Si la mascota ya existe, devuelve un error
        return jsonify({'success': False, 'message': 'Ya existe una mascota con ese nombre.'})
    else:
        # Si la mascota no existe, procede a registrarla
        nueva_mascota = Mascota(usuario_id=current_user.id, nombre=nombre_mascota)
        db.session.add(nueva_mascota)
        db.session.commit()
        # Devuelve un mensaje de éxito
        return jsonify({'success': True, 'message': 'Mascota registrada con éxito.'})
    
@login_required
@diagnosis.route('/info')
def info_view():
    enfermedades = Enfermedad.query.all()
    return render_template('diagnosis/info.html', enfermedades=enfermedades)







