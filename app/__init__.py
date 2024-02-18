from flask import Flask
from flask_migrate import Migrate
from config import Config
from .models import db 
from flask_mail import Mail

mail = Mail()

def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

   
    app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
    app.config['MAIL_PORT'] = 587  
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'dogdialog10@gmail.com'  
    app.config['MAIL_PASSWORD'] = 'mczm qakv pgmf epds'  
    app.config['MAIL_DEFAULT_SENDER'] = 'dogdialog10@gmail.com'  

 
    mail.init_app(app)

    # Configuración de las extensiones con la app
    from .models import setup_db, setup_login_manager
    setup_db(app)
    setup_login_manager(app)

    migrate = Migrate(app, db)  # Asegúrate de que 'db' esté disponible aquí; de lo contrario, ajusta la importación

    # Registro de blueprints
    from .blueprints.admin import admin as admin_blueprint
    from .blueprints.auth import auth as auth_blueprint
    from .blueprints.diagnosis.views import diagnosis as diagnosis_blueprint
    from .blueprints.user import user as user_blueprint
    from .blueprints.main import main as main_blueprint

    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(diagnosis_blueprint)
    app.register_blueprint(user_blueprint, url_prefix='/user')
    app.register_blueprint(main_blueprint)
    
    return app



