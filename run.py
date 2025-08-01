# run.py
import os
from kreativposten import create_app, db

# App erstellen
app = create_app()

# Datenbank-Setup und Ordner-Erstellung im Kontext der App
with app.app_context():
    # Stellt sicher, dass die Datenbank-Tabellen existieren
    db.create_all()
    
    # Stellt sicher, dass alle notwendigen Ordner existieren
    for folder_key in ['UPLOAD_FOLDER', 'QUOTES_FOLDER', 'AUFTRAGS_DATEIEN_FOLDER', 'CHAT_FILES_FOLDER']:
        folder_path = app.config.get(folder_key)
        if folder_path and not os.path.exists(folder_path):
            os.makedirs(folder_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)