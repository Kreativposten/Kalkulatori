# kreativposten/blueprints/main.py
from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', active_page='dashboard')

@main_bp.route('/auftraege')
def auftraege():
    return render_template('auftraege.html', active_page='auftraege')

@main_bp.route('/produktion')
def produktion():
    return render_template('produktion.html', active_page='produktion')

@main_bp.route('/beschaffung')
def beschaffung():
    # Logik für diese Seite wird später hinzugefügt
    return render_template('beschaffung.html', bestellungen=[], active_page='beschaffung')

# NEUE ROUTE, um hochgeladene Dateien sicher auszuliefern
@main_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Liefert eine Datei aus dem UPLOAD_FOLDER aus."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)