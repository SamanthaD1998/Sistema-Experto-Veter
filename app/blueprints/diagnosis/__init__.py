from flask import Blueprint

diagnosis = Blueprint('diagnosis', __name__)

from . import routes, views
