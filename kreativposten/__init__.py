# kreativposten/__init__.py
import os
from flask import Flask
from flask_mail import Mail
from .config import Config
from .models import db
from .utils import nl2br

# Initialisiere die Extensions hier, aber ohne App-Objekt
mail = Mail()

def create_app(config_class=Config):
    """
    Diese Funktion ist eine "Application Factory". Sie erstellt und 
    konfiguriert die Flask-Anwendung.
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Lade die Konfiguration
    app.config.from_object(config_class)

    # Initialisiere die Extensions mit der App
    db.init_app(app)
    mail.init_app(app)

    # Registriere den Template-Filter
    app.jinja_env.filters['nl2br'] = nl2br

    # Importiere und registriere die Blueprints INNERHALB der Funktion
    from .blueprints.main import main_bp
    from .blueprints.kalkulator import kalkulator_bp
    from .blueprints.stammdaten import stammdaten_bp
    from .blueprints.portal import portal_bp
    from .blueprints.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(kalkulator_bp)
    app.register_blueprint(stammdaten_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(api_bp)

    return app