from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, abort, send_from_directory
from ..models import Angebot, AuftragsDatei, AuftragsEreignis
from .. import db
import os
from werkzeug.utils import secure_filename
from weasyprint import HTML
from flask_mail import Message
from ..utils import send_email_async
import json
from datetime import datetime
from ..pricing import perform_calculation, MWST_SATZ

portal = Blueprint('portal', __name__)

PHASEN_MAP = {
    'Angebot an Kunden gesendet': 1,
    'Auftrag angenommen': 2,
    'Warten auf Korrektur-Freigabe': 2,
    'In Produktion': 3,
    'Abholbereit': 4,
    'Abgeschlossen': 4
}

@portal.route('/portal/<token>')
def view_portal(token):
    auftrag = Angebot.query.filter_by(kunden_token=token).first_or_404()
    aktuelle_phase = PHASEN_MAP.get(auftrag.status, 0)
    alle_dateien = auftrag.auftrags_dateien.order_by(AuftragsDatei.upload_datum.desc()).all()
    ereignisse = auftrag.auftrags_ereignisse.order_by(AuftragsEreignis.erstellt_am.asc()).all()
    return render_template('portal.html', auftrag=auftrag, aktuelle_phase=aktuelle_phase, alle_dateien=alle_dateien, ereignisse=ereignisse)

@portal.route('/upload/<token>', methods=['GET', 'POST'])
def upload_by_token(token):
    auftrag = Angebot.query.filter_by(kunden_token=token).first_or_404()
    if request.method == 'POST':
        if 'datei' not in request.files:
            flash('Keine Datei ausgewählt', 'danger')
            return redirect(request.url)
        file = request.files['datei']
        if file.filename == '':
            flash('Keine Datei ausgewählt', 'danger')
            return redirect(request.url)
        if file:
            original_filename = secure_filename(file.filename)
            saved_filename = f"{auftrag.kunden_token[:8]}_{original_filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
            file.save(upload_path)
            
            neue_datei = AuftragsDatei(auftrag_id=auftrag.id, original_filename=original_filename, saved_filename=saved_filename, hochgeladen_von='Kunde', dokument_typ='Druckdatei')
            db.session.add(neue_datei)
            db.session.commit()
            
            flash('Datei erfolgreich hochgeladen!', 'success')
            return redirect(request.url)
    
    dateien = auftrag.auftrags_dateien.filter_by(hochgeladen_von='Kunde').order_by(AuftragsDatei.upload_datum.desc()).all()
    return render_template('upload_by_qr.html', auftrag=auftrag, dateien=dateien)
