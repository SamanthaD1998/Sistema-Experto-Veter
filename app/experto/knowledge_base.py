from experta import KnowledgeEngine, Rule, Fact, MATCH

class EnfermedadFact(Fact):
    pass

class DiagnosticoSistemaExperto(KnowledgeEngine):
    UMBRAL_DIAGNOSTICO = 80
    UMBRAL_DIAGNOSTICO_ALT = 30

    def __init__(self, enfermedades_con_reglas=None):
        super().__init__()
        self.enfermedades_con_reglas = enfermedades_con_reglas or {}
        self.diagnostico = "No se pudo determinar un diagnóstico específico basado en los síntomas ingresados. Recomendamos consultar a un veterinario para asegurar el bienestar de tu mascota."
        self.diagnostico_alternativo = "Diagnóstico alternativo no determinado"
        self.principales_por_enfermedad = {}
        self.secundarios_por_enfermedad = {}
        self.pesos_por_enfermedad = {}

        if enfermedades_con_reglas:
            for enfermedad, info in enfermedades_con_reglas.items():
                self.principales_por_enfermedad[enfermedad] = info['principales']
                self.secundarios_por_enfermedad[enfermedad] = info['secundarios']
                self.pesos_por_enfermedad[enfermedad] = info['pesos']

    @Rule(EnfermedadFact(sintomas=MATCH.sintomas))
    def diagnostico_dinamico(self, sintomas):
        self.diagnosticos_alternativos = []
        for enfermedad in self.enfermedades_con_reglas.keys():
            principales = self.principales_por_enfermedad[enfermedad]
            secundarios = self.secundarios_por_enfermedad[enfermedad]
            pesos = self.pesos_por_enfermedad[enfermedad]

            todos_los_sintomas = set(principales + secundarios)
            sintomas_presentes = set(sintomas).intersection(todos_los_sintomas)

            principales_presentes = set(principales).issubset(sintomas)
            combinacion_valida = set(principales).intersection(sintomas) and set(secundarios).intersection(sintomas)

            sintomas_con_estado = [
            {"nombre": sintoma, "seleccionado": sintoma in sintomas_presentes}
            for sintoma in todos_los_sintomas
            ]
            
            if principales_presentes or combinacion_valida:
                probabilidad = self.calcular_probabilidad(enfermedad, sintomas, principales, secundarios, pesos)         
                if probabilidad >= self.UMBRAL_DIAGNOSTICO:
                    self.diagnostico = f"{enfermedad} (Probabilidad: {probabilidad}%)"
                elif probabilidad >= self.UMBRAL_DIAGNOSTICO_ALT:
                    self.diagnosticos_alternativos.append({
                        "enfermedad": enfermedad,
                        "probabilidad": probabilidad,
                        "sintomas": sintomas_con_estado
                    })
                return

    def calcular_probabilidad(self, nombre_enfermedad, sintomas, principales, secundarios, pesos):
        porcentaje_restante = 100 - sum(pesos.values())
        num_sintomas_secundarios = len(secundarios)
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios if num_sintomas_secundarios > 0 else 0
        probabilidad = sum(pesos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in principales or sintoma in secundarios)
        return probabilidad

def obtener_datos_enfermedades():
    from app.models import Enfermedad as EnfermedadModel, EnfermedadSintoma
    enfermedades_con_sintomas = {}
    enfermedades = EnfermedadModel.query.all()
    for enfermedad in enfermedades:
        sintomas = [{
            'nombre': es.sintoma.nombre,
            'es_principal': es.es_principal,
            'peso': es.peso
        } for es in enfermedad.enfermedades_sintomas]
        enfermedades_con_sintomas[enfermedad.nombre] = sintomas
        print(f"Enfermedad: {enfermedad.nombre}, Síntomas: {sintomas}")
    return enfermedades_con_sintomas

def generar_reglas_dinamicas(enfermedades_con_sintomas):
    reglas_dinamicas = {}
    for enfermedad, sintomas in enfermedades_con_sintomas.items():
        info_enfermedad = {
            'principales': [s['nombre'] for s in sintomas if s['es_principal']],
            'secundarios': [s['nombre'] for s in sintomas if not s['es_principal']],
            'pesos': {s['nombre']: s['peso'] for s in sintomas}
        }
        reglas_dinamicas[enfermedad] = info_enfermedad
        print(f"Reglas para {enfermedad}: {info_enfermedad}")
    return reglas_dinamicas

"""
@Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_parvovirus(self, sintomas):
        sintomas_principales = {'direadad','vomitos'}
        sintomas_secundarios = {'deshidratacion', 'perdida de apetito', 'cansancio'}
        pesos_fijos = {
        'diarrea_severa': 30,
        'vomitos': 25
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Parvovidadd (Probabilidad: {probabilidad}%)"


    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_distemper(self, sintomas):
        sintomas_principales = {'secrecion_nasal', 'convulsiones'}
        sintomas_secundarios = {'fiebre', 'tos', 'diarrea', 'cansancio', 'temblores'}

        pesos_fijos = {
        'secrecion_nasal': 40,
        'convulsiones': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Distemper Canino (Probabilidad: {probabilidad}%)"

    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_tvt(self, sintomas):
        sintomas_principales = {'masas con aspecto de coliflor en genitales', 'sangrado excesivo'}
        sintomas_secundarios = {'dificultad para orinar o defecar', 'inflamación o lesiones en genitales'}
        pesos_fijos = {
        'masas con aspecto de coliflor en genitales': 40,
        'sangrado excesivo': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Tumor Venéreo Transmisible (Probabilidad: {probabilidad}%)"    


    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_traqueobronquitis(self, sintomas):
        sintomas_principales = {'tos seca y fuerte', 'arcadas'}
        sintomas_secundarios = {'perdida de apetito', 'fiebre', 'cansancio', 'intolerancia al ejercicio', 'depresion'}
        pesos_fijos = {
        'tos seca y fuerte': 40,
        'arcadas': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Traqueobronquitis Canina (Probabilidad: {probabilidad}%)"  


    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_dermatitis_acaros(self, sintomas):
        sintomas_principales = {'costras en la piel', 'picazon intensa'}
        sintomas_secundarios = {'erupciones', 'perdida de pelo', 'enrojecimiento'}
        pesos_fijos = {
        'tos seca y fuerte': 40,
        'arcadas': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Dermatitis por Ácaros (Probabilidad: {probabilidad}%)"  
        

    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_dermatitis_pulgas(self, sintomas):
        sintomas_principales = {'mordeduras o lamido constante', 'picazon intensa'}
        sintomas_secundarios = {'perdida de pelo', 'inflamacion'}
        pesos_fijos = {
        'mordeduras o lamido constante': 40,
        'picazon intensa': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Dermatitis Alérgica por Pulgas (Probabilidad: {probabilidad}%)" 


    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_dermatitis_hongos(self, sintomas):
        sintomas_principales = {'perdida de pelo en areas circulares', 'picazon intensa'}
        sintomas_secundarios = {'costras en la piel', 'lesiones escamosas o inflamadas'}
        pesos_fijos = {
        'mordeduras o lamido constante': 40,
        'picazon intensa': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Dermatitis por Hongos (Probabilidad: {probabilidad}%)" 


    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_laringotraqueitis(self, sintomas):
        sintomas_principales = {'tos fuerte', 'arcadas'}
        sintomas_secundarios = {'expulsion de baba densa blanquecina', 'ronquera', 'perdida de capacidad de ladrar', 'nauseas'}
        pesos_fijos = {
        'tos fuerte': 40,
        'arcadas': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Laringotraqueitis Infecciosa (Probabilidad: {probabilidad}%)" 


    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_leptospirosis(self, sintomas):
        sintomas_principales = {'fiebre', 'diarrea'}
        sintomas_secundarios = {'vomito', 'dolores musculares', 'dificultad al caminar', 'poca actividad fisica', 'escalofrios'}
        pesos_fijos = {
        'fiebre': 40,
        'diarrea': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Leptospirosis (Probabilidad: {probabilidad}%)" 



    @Rule(Enfermedad(sintomas=MATCH.sintomas))
    def diagnostico_hepatitis(self, sintomas):
        sintomas_principales = {'mucosas de color amarillo', 'coloracion amarilla en la piel'}
        sintomas_secundarios = {'vomito', 'diarrea', 'higado agrandado y doloroso a la palpacion', 'sangrado de las encias', 'perdida completa del apetito'}
        pesos_fijos = {
        'fiebre': 40,
        'diarrea': 30
        }
        porcentaje_restante = 100 - sum(pesos_fijos.values())
        num_sintomas_secundarios = len(sintomas_secundarios)

        # Dividir el porcentaje restante entre los síntomas secundarios
        peso_por_sintoma_secundario = porcentaje_restante / num_sintomas_secundarios

        # Calcular la probabilidad
        probabilidad = sum(pesos_fijos.get(sintoma, peso_por_sintoma_secundario) for sintoma in sintomas if sintoma in sintomas_principales or sintoma in sintomas_secundarios)


        if sintomas_principales.issubset(sintomas) or \
        (sintomas_principales.intersection(sintomas) and sintomas_secundarios.intersection(sintomas)):
            self.diagnostico = f"Hepatitis Infecciosa (Probabilidad: {probabilidad}%)"  
        
        """



    





        






    