from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'

    from .blueprints.main import main as main_blueprint
    from .blueprints.kalkulator import kalkulator as kalkulator_blueprint
    from .blueprints.stammdaten import stammdaten as stammdaten_blueprint
    from .blueprints.portal import portal as portal_blueprint
    from .blueprints.api import api as api_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(kalkulator_blueprint)
    app.register_blueprint(stammdaten_blueprint, url_prefix='/stammdaten')
    app.register_blueprint(portal_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    return app
