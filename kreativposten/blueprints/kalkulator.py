# kreativposten/blueprints/kalkulator.py
import os
import uuid
import json
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..models import db, Produkt, Angebot, ArtikelVariante
from ..pricing import MARGE_PROZENT, MWST_SATZ, perform_calculation
from ..utils import log_ereignis

kalkulator_bp = Blueprint('kalkulator', __name__, template_folder='../templates')

@kalkulator_bp.route('/kalkulator')
def calculator_page():
    # Helper-Funktion, um Produktdaten für das Template aufzubereiten
    def prepare_product_data(produkte):
        produkt_dicts = []
        for p in produkte:
            # HIER WAR DER TIPPFEHLER: ek_netto_basis statt ek_net_basis
            vk_brutto = (p.ek_netto_basis * (1 + MARGE_PROZENT)) * (1 + MWST_SATZ) if p.ek_netto_basis is not None else 0.0
            produkt_dicts.append({
                'id': p.id,
                'name': p.name,
                'basis_vk_brutto': vk_brutto,
                'einkaufspreis_netto_produkt_fuer_kalkulation': p.ek_netto_basis
            })
        return sorted(produkt_dicts, key=lambda x: x['name'])

    # 1. Standardprodukte holen
    standard_produkte_query = db.session.query(Produkt).join(ArtikelVariante).filter(ArtikelVariante.ist_standard == True).distinct().all()
    standard_produkte_data = prepare_product_data(standard_produkte_query)
    standard_ids = {p.id for p in standard_produkte_query}

    # 2. Katalogprodukte holen (alle, die nicht Standard sind)
    katalog_produkte_query = Produkt.query.filter(Produkt.id.notin_(standard_ids)).all()
    katalog_produkte_data = prepare_product_data(katalog_produkte_query)

    return render_template('index.html', 
                           active_page='kalkulator', 
                           standard_produkte=standard_produkte_data,
                           katalog_produkte=katalog_produkte_data)


@kalkulator_bp.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Keine Datei im Request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Keine Datei ausgewählt'}), 400
    if file:
        original_fn = secure_filename(file.filename)
        unique_fn = str(uuid.uuid4()) + "_" + original_fn
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_fn))
        return jsonify({'success': True, 'filename': unique_fn})
    return jsonify({'success': False, 'error': 'Unbekannter Fehler'}), 500

@kalkulator_bp.route('/save-angebot', methods=['POST'])
def save_angebot():
    data = request.get_json()
    angebot_id = data.get('id')
    
    calc_result = perform_calculation(data)
    angebot_nr = calc_result.get('angebot_nr', 'TEMP-NR')
    data['angebot_nr'] = angebot_nr
    
    existing_angebot = Angebot.query.get(angebot_id) if angebot_id else None
    
    if existing_angebot:
        existing_angebot.angebot_nr = angebot_nr
        existing_angebot.kunde_name = data.get('kunde',{}).get('firma') or data.get('kunde',{}).get('name') or "Unbenannt"
        existing_angebot.angebot_data = json.dumps(data)
        message = f"Entwurf {angebot_nr} wurde aktualisiert!"
        db.session.commit()
        return jsonify({'success': True, 'message': message, 'angebot_id': existing_angebot.id, 'angebot_nr': angebot_nr})
    else:
        neues_angebot = Angebot(
            angebot_nr=angebot_nr,
            kunde_name=data.get('kunde',{}).get('firma') or data.get('kunde',{}).get('name') or "Unbenannt", 
            angebot_data=json.dumps(data), 
            kunden_token=str(uuid.uuid4()),
            status='Entwurf'
        )
        db.session.add(neues_angebot)
        db.session.commit()
        log_ereignis(neues_angebot.id, 'system', f"Angebot {neues_angebot.angebot_nr} wurde als Entwurf erstellt.", 'Admin')
        message = f"Neuer Entwurf {neues_angebot.angebot_nr} wurde gespeichert!"
        return jsonify({'success': True, 'message': message, 'angebot_id': neues_angebot.id, 'angebot_nr': angebot_nr})