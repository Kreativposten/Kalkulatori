# kreativposten/config.py
import os

# Basispfad des Projekts (der Ordner, der 'run.py' enthält)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'eine-sehr-geheime-zeichenkette-fuer-den-notfall'
    
    # Datenbank-Konfiguration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'angebote.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload-Ordner Konfiguration (jetzt relativ zum Projekt-Root)
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    QUOTES_FOLDER = os.path.join(basedir, 'quotes')
    AUFTRAGS_DATEIEN_FOLDER = os.path.join(basedir, 'auftragsdateien')
    CHAT_FILES_FOLDER = os.path.join(basedir, 'chatfiles')

    # E-Mail Konfiguration - BITTE ANPASSEN ODER ÜBER ENVIRONMENT VARIABLEN SETZEN!
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'ihre-email@example.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'ihr-email-passwort')
    MAIL_DEFAULT_SENDER = ('Ihr Firmenname', os.environ.get('MAIL_USERNAME', 'ihre-email@example.com'))
