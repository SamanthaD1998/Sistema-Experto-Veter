import os

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_muy_dificil_de_adivinar'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:admin@127.0.0.1:5432/se_canino'
    SQLALCHEMY_TRACK_MODIFICATIONS = False 


