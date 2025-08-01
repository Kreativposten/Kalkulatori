from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from .config import Config
import os

# 1. Initialisiere die Erweiterungen außerhalb der Factory
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    # 2. Erstelle die App-Instanz
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 3. Verbinde die Erweiterungen mit der App
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Wichtig: Login-Manager Konfiguration
    login_manager.login_view = 'auth.login' # Annahme: es gibt eine 'auth' Blueprint mit einer 'login' Route

    # 4. Importiere und registriere die Blueprints innerhalb der Factory
    from .blueprints.main import main as main_blueprint
    from .blueprints.kalkulator import kalkulator as kalkulator_blueprint
    from .blueprints.stammdaten import stammdaten as stammdaten_blueprint
    from .blueprints.portal import portal as portal_blueprint
    from .blueprints.api import api as api_blueprint
    # from .blueprints.auth import auth as auth_blueprint # Auskommentiert, falls nicht vorhanden

    app.register_blueprint(main_blueprint)
    app.register_blueprint(kalkulator_blueprint)
    app.register_blueprint(stammdaten_blueprint, url_prefix='/stammdaten')
    app.register_blueprint(portal_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
    # app.register_blueprint(auth_blueprint) # Auskommentiert, falls nicht vorhanden
    
    with app.app_context():
        # Stelle sicher, dass die Modelle der DB bekannt sind
        from . import models
        
        # Erstelle alle Tabellen, falls die DB nicht existiert
        # db.create_all() # Normalerweise durch 'flask db upgrade' gehandhabt

    return app