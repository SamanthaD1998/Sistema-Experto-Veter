from flask import Blueprint
from .views import enter_symptoms_view, results_view,record_view,select_pet_view,info_view

diagnosis = Blueprint('diagnosis', __name__, url_prefix='/diagnosis')

# Ingresar síntomas
diagnosis.add_url_rule('/enter_symptoms', 'enter_symptoms', enter_symptoms_view, methods=['GET', 'POST'])

# Mostrar resultados
diagnosis.add_url_rule('/results', 'results', results_view, methods=['GET', 'POST'])

diagnosis.add_url_rule('/record', 'record', record_view, methods=['GET', 'POST'])

diagnosis.add_url_rule('/select_pet', 'select_pet', select_pet_view, methods=['GET', 'POST'])

diagnosis.add_url_rule('/info', 'info', info_view, methods=['GET', 'POST'])

diagnosis.add_url_rule('/info', 'info', info_view, methods=['GET', 'POST'])

