# kreativposten/blueprints/portal.py
import os
import json
import uuid
import base64
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, current_app, jsonify, send_from_directory
from weasyprint import HTML
from werkzeug.utils import secure_filename
from ..models import db, Angebot, AuftragsDatei, AuftragsEreignis, Produkt
from ..utils import generate_qr_code_base64, log_ereignis, sende_email
from ..pricing import perform_calculation, MWST_SATZ

portal_bp = Blueprint('portal', __name__, template_folder='../templates')

PORTAL_PHASEN = { 
    'Entwurf': 1, 'Angebot an Kunden gesendet': 1, 'Warten auf Angebot-Freigabe': 1, 
    'Auftrag angenommen': 2, 'Warten auf Korrektur-Freigabe': 2, 'Freigabe vom Kunden erhalten': 3,
    'Änderungswunsch vom Kunden': 2, 'Korrekturabzug an Kunden gesendet': 2,
    'Warte auf Produktion': 3, 'In Produktion': 3, 
    'Abholbereit': 4, 'Fertig zur Abholung': 4, 'Vom Kunden abgeholt': 4, 'Abgeschlossen': 4
}


def _get_pdf_context(angebot_id):
    """Hilfsfunktion, um den Kontext für die PDF-Generierung zu erstellen."""
    angebot = Angebot.query.get_or_404(angebot_id)
    angebot_data = json.loads(angebot.angebot_data)
    
    # Führe die Kalkulation erneut aus, um sicherzustellen, dass alle Daten aktuell sind
    calc_result = perform_calculation(angebot_data)
    angebot_data.update(calc_result)

    # QR Code für das Portal hinzufügen
    if angebot.kunden_token:
        portal_url = url_for('portal.portal_view', token=angebot.kunden_token, _external=True)
        angebot_data['portal_qr_code'] = generate_qr_code_base64(portal_url)

    # Base64-kodierte Bilder für die PDF-Einbettung vorbereiten
    for pos_data in angebot_data.get('positionen', []):
        for druck in pos_data.get('drucke_details', []):
            filename = druck.get('filename')
            if filename:
                img_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(img_path):
                    with open(img_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                        # Annahme des Mime-Typs basierend auf der Dateiendung
                        ext = filename.split('.')[-1].lower()
                        mime_type = f"image/{ext}" if ext in ['jpg', 'jpeg', 'png', 'gif'] else "image/jpeg"
                        druck['src'] = f"data:{mime_type};base64,{encoded_string}"

    logo_path = os.path.join(current_app.root_path, '..', 'Logo Kreativposten Vektorisiert.jpg')
    logo_b64 = None
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as image_file:
            logo_b64 = base64.b64encode(image_file.read()).decode("utf-8")
            logo_b64 = f"data:image/jpeg;base64,{logo_b64}"
            
    return angebot, angebot_data, logo_b64


@portal_bp.route('/portal/<token>')
def portal_view(token):
    auftrag = Angebot.query.filter_by(kunden_token=token).first_or_404()
    alle_dateien = AuftragsDatei.query.filter_by(auftrag_id=auftrag.id).order_by(AuftragsDatei.upload_datum.desc()).all()
    ereignisse = AuftragsEreignis.query.filter_by(auftrag_id=auftrag.id).order_by(AuftragsEreignis.erstellt_am.asc()).all()
    aktuelle_phase = PORTAL_PHASEN.get(auftrag.status, 1)
    return render_template('portal.html', auftrag=auftrag, ereignisse=ereignisse, aktuelle_phase=aktuelle_phase,
                           alle_dateien=alle_dateien)

@portal_bp.route('/auftrag/<int:angebot_id>')
def auftrag_details(angebot_id):
    auftrag = Angebot.query.get_or_404(angebot_id)
    auftrag_data = json.loads(auftrag.angebot_data)
    portal_url, upload_url = None, None
    portal_qr_code, upload_qr_code = None, None
    
    if auftrag.kunden_token:
        portal_url = url_for('portal.portal_view', token=auftrag.kunden_token, _external=True)
        upload_url = url_for('portal.upload_by_token', token=auftrag.kunden_token, _external=True)
        portal_qr_code = generate_qr_code_base64(portal_url)
        upload_qr_code = generate_qr_code_base64(upload_url)

    alle_dateien = AuftragsDatei.query.filter_by(auftrag_id=auftrag.id).order_by(AuftragsDatei.upload_datum.desc()).all()
    ereignisse = AuftragsEreignis.query.filter_by(auftrag_id=auftrag.id).order_by(AuftragsEreignis.erstellt_am.asc()).all()
    
    return render_template('auftrag_details.html', auftrag=auftrag, auftrag_data=auftrag_data,
                           portal_url=portal_url, upload_url=upload_url, 
                           portal_qr_code=portal_qr_code, upload_qr_code=upload_qr_code,
                           ereignisse=ereignisse, alle_dateien=alle_dateien, active_page='auftraege')

@portal_bp.route('/angebot/<int:angebot_id>/senden', methods=['POST'])
def angebot_senden(angebot_id):
    angebot, angebot_data, logo_b64 = _get_pdf_context(angebot_id)
    
    pdf_filename = f"Angebot_{angebot.angebot_nr}.pdf"
    pdf_path = os.path.join(current_app.config['QUOTES_FOLDER'], pdf_filename)
    
    rendered_html = render_template('angebot_vorlage.html', data=angebot_data, logo_base64=logo_b64)
    HTML(string=rendered_html, base_url=request.url_root).write_pdf(pdf_path)

    kunden_email = json.loads(angebot.angebot_data).get('kunde', {}).get('email')
    
    if kunden_email:
        sende_email(
            kunden_email,
            f"Ihr Angebot von Kreativposten: {angebot.angebot_nr}",
            'email/angebot_gesendet.html', # Du musst dieses Template noch erstellen
            angebot=angebot,
            portal_url=angebot_data['portal_qr_code']
        )
        angebot.status = 'Angebot an Kunden gesendet'
        log_ereignis(angebot.id, 'status', f"Status geändert zu: Angebot an Kunden gesendet.", 'Admin')
        flash('Angebot erfolgreich an den Kunden versendet!', 'success')
    else:
        flash("Fehler: Kunden-E-Mail-Adresse nicht gefunden. Angebot wurde nicht per E-Mail versendet.", 'warning')

    db.session.commit()
    return redirect(url_for('portal.auftrag_details', angebot_id=angebot.id))


@portal_bp.route('/portal/<token>/angebot-annehmen', methods=['POST'])
def angebot_annehmen(token):
    auftrag = Angebot.query.filter_by(kunden_token=token).first_or_404()
    if auftrag.status in ['Angebot an Kunden gesendet', 'Warten auf Angebot-Freigabe']:
        auftrag.status = 'Auftrag angenommen'
        db.session.commit()
        log_ereignis(auftrag.id, 'status', "Kunde hat Angebot online angenommen.", 'Kunde')
        
        # Admin und Kunde benachrichtigen
        # sende_email(...)
        
        return jsonify(success=True)
    return jsonify(success=False, message='Angebot kann nicht mehr angenommen werden.'), 400

@portal_bp.route('/upload-datei-admin/<int:auftrag_id>', methods=['POST'])
def upload_datei_admin(auftrag_id):
    auftrag = Angebot.query.get_or_404(auftrag_id)
    if 'datei' not in request.files:
        flash('Keine Datei ausgewählt.', 'danger')
        return redirect(url_for('portal.auftrag_details', angebot_id=auftrag_id))

    file = request.files['datei']
    if file.filename == '':
        flash('Keine Datei ausgewählt.', 'danger')
        return redirect(url_for('portal.auftrag_details', angebot_id=auftrag_id))

    if file:
        original_fn = secure_filename(file.filename)
        unique_fn = str(uuid.uuid4()) + "_" + original_fn
        filepath = os.path.join(current_app.config['AUFTRAGS_DATEIEN_FOLDER'], unique_fn)
        file.save(filepath)

        dokument_typ = 'Kundendatei'
        freigabe_status = None
        inhalt = f"Datei hochgeladen: {original_fn}"

        if request.form.get('is_korrekturabzug'):
            dokument_typ = 'Korrekturabzug'
            freigabe_status = 'Freigabe ausstehend'
            inhalt = f"Korrekturabzug hochgeladen: {original_fn}. Freigabe ausstehend."
            auftrag.status = 'Korrekturabzug an Kunden gesendet'
            log_ereignis(auftrag.id, 'status', "Status geändert zu: Korrekturabzug an Kunden gesendet.", 'Admin')
            
        neue_datei = AuftragsDatei(
            auftrag_id=auftrag.id,
            original_filename=original_fn,
            saved_filename=unique_fn,
            hochgeladen_von='Admin',
            dokument_typ=dokument_typ,
            freigabe_status=freigabe_status
        )
        db.session.add(neue_datei)
        db.session.flush()
        log_ereignis(auftrag.id, 'upload', inhalt, 'Admin', neue_datei.id)
        db.session.commit()

        flash('Datei erfolgreich hochgeladen.', 'success')
    return redirect(url_for('portal.auftrag_details', angebot_id=auftrag_id))

@portal_bp.route('/upload_by_token/<token>', methods=['GET', 'POST'])
def upload_by_token(token):
    auftrag = Angebot.query.filter_by(kunden_token=token).first_or_404()
    if request.method == 'POST':
        if 'datei' not in request.files:
            flash('Keine Datei ausgewählt.', 'danger')
            return redirect(url_for('portal.upload_by_token', token=token))
        file = request.files['datei']
        if file.filename == '':
            flash('Keine Datei ausgewählt.', 'danger')
            return redirect(url_for('portal.upload_by_token', token=token))
        if file:
            original_fn = secure_filename(file.filename)
            unique_fn = str(uuid.uuid4()) + "_" + original_fn
            filepath = os.path.join(current_app.config['AUFTRAGS_DATEIEN_FOLDER'], unique_fn)
            file.save(filepath)

            neue_datei = AuftragsDatei(
                auftrag_id=auftrag.id,
                original_filename=original_fn,
                saved_filename=unique_fn,
                druckposition=request.form.get('druckposition'),
                hochgeladen_von='Kunde',
                dokument_typ='Kundendatei'
            )
            db.session.add(neue_datei)
            db.session.flush()
            log_ereignis(auftrag.id, 'upload', f"Kunde hat Datei '{original_fn}' hochgeladen.", 'Kunde', neue_datei.id)
            db.session.commit()
            flash('Datei erfolgreich hochgeladen!', 'success')
            return redirect(url_for('portal.upload_by_token', token=token))

    dateien = AuftragsDatei.query.filter_by(auftrag_id=auftrag.id).order_by(AuftragsDatei.upload_datum.desc()).all()
    return render_template('upload_by_qr.html', auftrag=auftrag, dateien=dateien)


@portal_bp.route('/view/auftragsdatei/<filename>')
def view_auftragsdatei(filename):
    return send_from_directory(current_app.config['AUFTRAGS_DATEIEN_FOLDER'], filename)

@portal_bp.route('/download/auftragsdatei/<filename>')
def download_auftragsdatei(filename):
    return send_from_directory(current_app.config['AUFTRAGS_DATEIEN_FOLDER'], filename, as_attachment=True)


@portal_bp.route('/produktionsmappe/<int:auftrag_id>')
def produktionsmappe(auftrag_id):
    auftrag, auftrag_data, logo_b64 = _get_pdf_context(auftrag_id)
    remote_url = url_for('portal.remote_auftrag', angebot_id=auftrag.id, _external=True)
    qr_code_image = generate_qr_code_base64(remote_url)
    
    return render_template('produktionsmappe_vorlage.html', data={'auftrag': auftrag, 'auftrag_data': auftrag_data, 'qr_code_image': qr_code_image})


@portal_bp.route('/remote/auftrag/<int:angebot_id>')
def remote_auftrag(angebot_id):
    auftrag = Angebot.query.get_or_404(angebot_id)
    auftrag_data = json.loads(auftrag.angebot_data)
    # Daten anreichern, falls nötig
    for pos in auftrag_data.get('positions', []):
        produkt_id = pos.get('produkt_id')
        if produkt_id:
            produkt = Produkt.query.get(produkt_id)
            pos['textil'] = produkt.name if produkt else 'Unbekanntes Textil'
    return render_template('remote.html', auftrag=auftrag, auftrag_data=auftrag_data)


@portal_bp.route('/generate-pdf-final/<int:angebot_id>')
def generate_pdf_final(angebot_id):
    angebot, angebot_data, logo_b64 = _get_pdf_context(angebot_id)
    pdf_filename = f"Angebot_{angebot.angebot_nr}.pdf"
    
    rendered_html = render_template('angebot_vorlage.html', data=angebot_data, logo_base64=logo_b64)
    pdf_file = HTML(string=rendered_html, base_url=request.url_root).write_pdf()

    return Response(pdf_file, mimetype="application/pdf", headers={"Content-Disposition": f"inline;filename={pdf_filename}"})