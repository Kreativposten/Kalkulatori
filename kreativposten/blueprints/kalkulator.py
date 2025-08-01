from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import json
from datetime import date
from ..pricing import calculate_price
from ..models import Angebot, ArtikelVariante, Kunde
from .. import db

kalkulator = Blueprint('kalkulator', __name__)

@kalkulator.route('/kalkulator')
def calculator_page():
    load_id = request.args.get('load_id')
    angebot_daten = None
    if load_id:
        angebot = Angebot.query.get(load_id)
        if angebot:
            angebot_daten = angebot.kalkulations_daten

    standard_produkte_query = ArtikelVariante.query.filter_by(ist_standard=True).all()
    standard_produkte = [{'id': v.id, 'produkt_name': v.produkt.name, 'hersteller': v.produkt.hersteller, 'farbe': v.farbe, 'groesse': v.groesse, 'ek_netto': v.einkaufspreis_netto} for v in standard_produkte_query]
    
    katalog_produkte_query = ArtikelVariante.query.all()
    katalog_produkte = [{'id': v.id, 'produkt_name': v.produkt.name, 'hersteller': v.produkt.hersteller, 'farbe': v.farbe, 'groesse': v.groesse, 'ek_netto': v.einkaufspreis_netto} for v in katalog_produkte_query]

    return render_template('index.html', angebot_daten=angebot_daten, standard_produkte=standard_produkte, katalog_produkte=katalog_produkte)

@kalkulator.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    results = calculate_price(data)
    return jsonify(results)

def get_next_angebot_nr():
    today = date.today()
    prefix = f"{today.strftime('%d%m%y')}-"
    last_angebot = Angebot.query.filter(Angebot.angebot_nr.like(f"{prefix}%")).order_by(Angebot.angebot_nr.desc()).first()
    
    if last_angebot:
        try:
            last_nr = int(last_angebot.angebot_nr.split('-')[-1])
            new_nr = last_nr + 1
            return f"{prefix}{new_nr}"
        except (ValueError, IndexError):
            return f"{prefix}1"
    else:
        return f"{prefix}1"

@kalkulator.route('/save-angebot', methods=['POST'])
def save_angebot():
    data = request.get_json()
    angebot_id = data.get('id')
    kunde_name = data.get('kunde', {}).get('name')
    kunde = None
    if kunde_name:
        kunde = Kunde.query.filter_by(name=kunde_name).first()
        if not kunde:
            kunde = Kunde(name=kunde_name, firma=data.get('kunde', {}).get('firma'))
            db.session.add(kunde)

    if angebot_id:
        angebot = Angebot.query.get(angebot_id)
        if angebot:
            angebot.kunde_name = kunde_name
            angebot.kalkulations_daten = json.dumps(data)
            angebot.status = 'Entwurf'
            if kunde:
                angebot.kunde = kunde
    else:
        angebot_nr = get_next_angebot_nr()
        angebot = Angebot(angebot_nr=angebot_nr, kunde_name=kunde_name, datum=date.today(), kalkulations_daten=json.dumps(data), status='Entwurf')
        if kunde:
            angebot.kunde = kunde
        db.session.add(angebot)

    db.session.commit()
    return jsonify({'status': 'success', 'id': angebot.id, 'angebot_nr': angebot.angebot_nr})
