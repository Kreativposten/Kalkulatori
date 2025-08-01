from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from ..models import Angebot, AuftragsDatei, AuftragsEreignis, Aufgabe, Kunde
from .. import db
import qrcode
import base64
from io import BytesIO
from weasyprint import HTML
from datetime import datetime

main = Blueprint('main', __name__)

# --- Bestehende Routen ---

@main.route('/')
def dashboard():
    return render_template('dashboard.html')

@main.route('/produktion')
def produktion():
    projekte = Angebot.query.all()
    return render_template('produktion.html', projekte=projekte)

@main.route('/get-projekte')
def get_projekte():
    projekte_query = Angebot.query.order_by(Angebot.datum.desc()).all()
    projekte_liste = [
        {
            'id': p.id,
            'angebot_nr': p.angebot_nr,
            'kunde_name': p.kunde_name,
            'datum': p.datum.strftime('%d.%m.%Y'),
            'status': p.status
        } for p in projekte_query
    ]
    return jsonify(projekte_liste)

@main.route('/auftraege')
def auftraege():
    return render_template('auftraege.html')
    
@main.route('/beschaffung')
def beschaffung():
    # Dummy-Daten, da noch keine Logik vorhanden
    bestellungen = []
    return render_template('beschaffung.html', bestellungen=bestellungen)

@main.route('/auftrag/<int:auftrag_id>')
def auftrag_details(auftrag_id):
    auftrag = Angebot.query.get_or_404(auftrag_id)
    
    # QR-Codes generieren
    portal_url = url_for('portal.view_portal', token=auftrag.kunden_token, _external=True)
    upload_url = url_for('portal.upload_by_token', token=auftrag.kunden_token, _external=True)
    
    portal_qr_code = generate_qr_code_base64(portal_url)
    upload_qr_code = generate_qr_code_base64(upload_url)

    ereignisse = auftrag.auftrags_ereignisse.order_by(AuftragsEreignis.erstellt_am.asc()).all()
    alle_dateien = auftrag.auftrags_dateien.order_by(AuftragsDatei.upload_datum.desc()).all()

    aktive_freigaben = [d for d in alle_dateien if d.freigabe_status == 'Freigabe ausstehend']
    design_dateien = [d for d in alle_dateien if d.dokument_typ in [None, 'Druckdatei', 'Design']]
    admin_dokumente = [d for d in alle_dateien if d.dokument_typ in ['Angebot', 'Rechnung']]
    
    return render_template('auftrag_details.html', 
        auftrag=auftrag, 
        portal_url=portal_url,
        upload_url=upload_url,
        portal_qr_code=portal_qr_code, 
        upload_qr_code=upload_qr_code,
        ereignisse=ereignisse,
        aktive_freigaben=aktive_freigaben,
        design_dateien=design_dateien,
        admin_dokumente=admin_dokumente
    )

def generate_qr_code_base64(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

@main.route('/produktionsmappe/<int:auftrag_id>')
def produktionsmappe(auftrag_id):
    # Diese Route ist ein Platzhalter. Die Logik befindet sich in der Regel
    # in der `kalkulator.py` oder einer dedizierten `document_generator.py`
    # Hier wird angenommen, dass es eine Funktion gibt, die die PDF generiert.
    # Du müsstest die Logik aus der Angebots-PDF-Generierung anpassen.
    flash('Die Generierung der Produktionsmappe ist noch nicht implementiert.', 'danger')
    return redirect(url_for('main.auftrag_details', auftrag_id=auftrag_id))

# --- NEUE ROUTEN FÜR KUNDENVERWALTUNG ---

@main.route('/kunden')
def kunden_verwalten():
    alle_kunden = Kunde.query.order_by(Kunde.name).all()
    return render_template('kunden.html', kunden=alle_kunden, active_page='kunden')

@main.route('/kunden/neu', methods=['POST'])
def kunde_anlegen():
    name = request.form.get('name')
    firma = request.form.get('firma')
    email = request.form.get('email')
    telefon = request.form.get('telefon')

    if not name:
        flash('Der Name ist ein Pflichtfeld.', 'danger')
        return redirect(url_for('main.kunden_verwalten'))

    neuer_kunde = Kunde(name=name, firma=firma, email=email, telefon=telefon)
    db.session.add(neuer_kunde)
    db.session.commit()

    flash(f'Kunde "{name}" wurde erfolgreich angelegt.', 'success')
    return redirect(url_for('main.kunden_verwalten'))

@main.route('/kunde/<int:kunde_id>/details')
def kunde_details(kunde_id):
    kunde = Kunde.query.get_or_404(kunde_id)
    return render_template('kunde_details.html', kunde=kunde, active_page='kunden')

@main.route('/kunde/<int:kunde_id>/bearbeiten', methods=['GET', 'POST'])
def kunde_bearbeiten(kunde_id):
    kunde = Kunde.query.get_or_404(kunde_id)

    if request.method == 'POST':
        kunde.name = request.form.get('name')
        kunde.firma = request.form.get('firma')
        kunde.email = request.form.get('email')
        kunde.telefon = request.form.get('telefon')
        
        db.session.commit()
        flash('Kundendaten wurden erfolgreich aktualisiert.', 'success')
        return redirect(url_for('main.kunde_details', kunde_id=kunde.id))

    return render_template('kunde_bearbeiten.html', kunde=kunde, active_page='kunden')
