# kreativposten/blueprints/api.py
import datetime
from flask import Blueprint, jsonify, request
from collections import defaultdict
from ..models import db, ArtikelVariante, Angebot, AuftragsEreignis, Aufgabe, Produkt
from ..pricing import perform_calculation
from ..utils import log_ereignis

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/produkt/<int:produkt_id>/varianten-data')
def get_varianten_data(produkt_id):
    """
    Liefert eine strukturierte Liste aller Farben und der dazugehörigen Größen für ein Produkt.
    """
    varianten = ArtikelVariante.query.filter_by(produkt_id=produkt_id).all()
    
    # defaultdict erspart uns die Prüfung, ob ein Key schon existiert
    farben_und_groessen = defaultdict(list)
    
    for v in varianten:
        # Füge die Größe nur hinzu, wenn sie nicht schon in der Liste für diese Farbe ist
        if v.groesse not in farben_und_groessen[v.farbe]:
            farben_und_groessen[v.farbe].append(v.groesse)
            
    return jsonify(dict(farben_und_groessen))


@api_bp.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    result = perform_calculation(data)
    return jsonify(result)

@api_bp.route('/api/variante/check')
def check_variante_status():
    produkt_id = request.args.get('produkt_id', type=int)
    farbe = request.args.get('farbe')
    groesse = request.args.get('groesse')
    
    if not all([produkt_id, farbe, groesse]):
        return jsonify({'error': 'Fehlende Parameter'}), 400

    variante = ArtikelVariante.query.filter_by(produkt_id=produkt_id, farbe=farbe, groesse=groesse).first()
    
    if variante:
        return jsonify({'lagerbestand': variante.lagerbestand, 'exists': True})
    else:
        return jsonify({'lagerbestand': 0, 'exists': False})

@api_bp.route('/get-projekte', methods=['GET'])
def get_projekte():
    projekte = Angebot.query.order_by(Angebot.datum.desc()).all()
    return jsonify([{ "id": p.id, "angebot_nr": p.angebot_nr, "kunde_name": p.kunde_name, "datum": p.datum.strftime('%d.%m.%Y'), "status": p.status } for p in projekte])

@api_bp.route('/api/auftrag/<string:token_or_id>/nachricht', methods=['POST'])
def send_message(token_or_id):
    data = request.get_json()
    inhalt = data.get('inhalt')
    
    auftrag = None
    try:
        auftrag = Angebot.query.get(int(token_or_id))
        sender = 'Admin'
    except ValueError:
        auftrag = Angebot.query.filter_by(kunden_token=token_or_id).first()
        sender = 'Kunde'

    if not auftrag:
        return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404

    if inhalt:
        log_ereignis(auftrag.id, 'nachricht', inhalt, sender)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Nachricht leer'}), 400

@api_bp.route('/api/auftrag/<int:auftrag_id>/ereignisse', methods=['GET'])
def get_auftrag_ereignisse(auftrag_id):
    since_timestamp_str = request.args.get('since')
    query = AuftragsEreignis.query.filter_by(auftrag_id=auftrag_id)
    
    if since_timestamp_str:
        try:
            if since_timestamp_str.endswith('Z'):
                since_timestamp_str = since_timestamp_str[:-1] + '+00:00'
            since_timestamp = datetime.datetime.fromisoformat(since_timestamp_str)
            query = query.filter(AuftragsEreignis.erstellt_am > since_timestamp)
        except ValueError:
            pass

    ereignisse = query.order_by(AuftragsEreignis.erstellt_am.asc()).all()

    ereignis_list = [{
        'typ': e.typ,
        'sender': e.sender,
        'inhalt': e.inhalt,
        'zeit_iso': e.erstellt_am.isoformat() + "Z"
    } for e in ereignisse]
    return jsonify(ereignis_list)

@api_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = Aufgabe.query.filter_by(erledigt=False).order_by(Aufgabe.erstellt_am.asc()).all()
    return jsonify([{'id': t.id, 'inhalt': t.inhalt, 'erledigt': t.erledigt} for t in tasks])

@api_bp.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    inhalt = data.get('inhalt')
    if inhalt:
        new_task = Aufgabe(inhalt=inhalt)
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'success': True, 'task': {'id': new_task.id, 'inhalt': new_task.inhalt, 'erledigt': new_task.erledigt}})
    return jsonify({'success': False, 'error': 'Inhalt fehlt'}), 400

@api_bp.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    task = Aufgabe.query.get_or_404(task_id)
    task.erledigt = not task.erledigt
    db.session.commit()
    return jsonify({'success': True, 'task': {'id': task.id, 'inhalt': task.inhalt, 'erledigt': task.erledigt}})

@api_bp.route('/api/datei/<int:datei_id>/freigeben', methods=['POST'])
def datei_freigeben(datei_id):
    datei = db.session.get(AuftragsDatei, datei_id)
    if not datei: return jsonify(success=False, message="Datei nicht gefunden"), 404
    
    datei.freigabe_status = 'Freigegeben'
    if datei.auftrag.status == 'Korrekturabzug an Kunden gesendet':
        datei.auftrag.status = 'Freigabe vom Kunden erhalten'
        
    log_ereignis(datei.auftrag_id, 'freigabe', f"Korrekturabzug '{datei.original_filename}' wurde freigegeben.", 'Kunde', datei.id)
    db.session.commit()
    return jsonify(success=True)

@api_bp.route('/api/datei/<int:datei_id>/aenderung', methods=['POST'])
def datei_aenderung(datei_id):
    datei = db.session.get(AuftragsDatei, datei_id)
    if not datei: return jsonify(success=False, message="Datei nicht gefunden"), 404

    kommentar = request.form.get('kommentar', '')
    datei.freigabe_status = 'Änderungswunsch'
    datei.freigabe_kommentar = kommentar
    if datei.auftrag.status == 'Korrekturabzug an Kunden gesendet':
        datei.auftrag.status = 'Änderungswunsch vom Kunden'
        
    log_ereignis(datei.auftrag_id, 'aenderung', f"Änderungswunsch zu '{datei.original_filename}': {kommentar}", 'Kunde', datei.id)
    db.session.commit()
    return jsonify(success=True)