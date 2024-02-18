from .knowledge_base import DiagnosticoSistemaExperto, EnfermedadFact, obtener_datos_enfermedades, generar_reglas_dinamicas

def obtener_diagnostico(sintomas):
    enfermedades_con_sintomas = obtener_datos_enfermedades()
    reglas_dinamicas = generar_reglas_dinamicas(enfermedades_con_sintomas)

    engine = DiagnosticoSistemaExperto(enfermedades_con_reglas=reglas_dinamicas)
    engine.reset()

    engine.declare(EnfermedadFact(sintomas=set(sintomas)))
    engine.run()
    return engine.diagnostico, engine.diagnosticos_alternativos


def procesar_entrada_formulario(form_data):
    sintomas = [key for key, value in form_data.items() if value == 'on']
    return sintomas



