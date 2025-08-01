# kreativposten/pricing.py
import re
import datetime
from .models import Produkt

# --- Preislogik Konstanten ---
MWST_SATZ = 0.19
MARGE_PROZENT = 0.50 

DRUCK_PREISE = {"Kein": 0, "Klein": 10.00, "Mittel": 11.50, "Groß": 13.00}
ZUSCHLAG_FREISTELLEN = {"Kein": 0, "Klein": 1.00, "Mittel": 1.75, "Groß": 2.50}
DRINGLICHKEITS_ZUSCHLAEGE = {"Standard": 0, "Express": 0.15, "Overnight": 0.30}

def get_textil_rabatt(menge): 
    return 0.2 if menge >= 100 else 0.15 if menge >= 25 else 0.1 if menge >= 5 else 0.05 if menge >= 2 else 0

def get_druck_rabatt(menge): 
    return 0.2 if menge >= 100 else 0.15 if menge >= 25 else 0.1 if menge >= 15 else 0.05 if menge >= 10 else 0

def _calculate_druck_costs(pos_data):
    menge = pos_data['total_menge']
    drucke_details_raw = pos_data.get('drucke_details', [])
    drucke_mit_preisen = sorted([(d, DRUCK_PREISE.get(d['typ'], 0)) for d in drucke_details_raw], key=lambda x: x[1], reverse=True)
    druck_rabatt_prozent_val = get_druck_rabatt(menge)
    zuschlag_freistellen_brutto, druck_details_live, druck_gesamt_vor_rabatt = 0, [], 0
    
    for druck_details, preis in drucke_mit_preisen:
        if druck_details.get('freistellen'):
            zuschlag_freistellen_brutto += ZUSCHLAG_FREISTELLEN.get(druck_details.get('typ'), 0) * menge
            
    if drucke_mit_preisen:
        druck_details, preis = drucke_mit_preisen[0]
        einzelpreis1 = preis
        druck_gesamt_vor_rabatt += einzelpreis1 * menge
        druck_details_live.append({"name": druck_details.get('position', druck_details.get('typ')), "einzelpreis_vor_mengenrabatt": einzelpreis1, "ist_mehrfach_rabattiert": False})
        
        for druck_details, preis in drucke_mit_preisen[1:]:
            preis_mit_60_rabatt = preis * 0.4
            druck_gesamt_vor_rabatt += preis_mit_60_rabatt * menge
            druck_details_live.append({"name": druck_details.get('position', druck_details.get('typ')), "einzelpreis_vor_mengenrabatt": preis_mit_60_rabatt, "ist_mehrfach_rabattiert": True})
            
    druck_gesamtrabatt_betrag = druck_gesamt_vor_rabatt * druck_rabatt_prozent_val
    druck_kosten_brutto = druck_gesamt_vor_rabatt - druck_gesamtrabatt_betrag
    
    return {
        "druck_details_live": druck_details_live,
        "druck_gesamt_brutto": druck_kosten_brutto,
        "zuschlag_freistellen_brutto": zuschlag_freistellen_brutto,
        "druck_rabatt_prozent": druck_rabatt_prozent_val * 100,
        "druck_gesamt_vor_rabatt": druck_gesamt_vor_rabatt,
        "druck_gesamtrabatt_betrag": druck_gesamtrabatt_betrag,
        "druck_einzelpreis_vor_rabatt": druck_gesamt_vor_rabatt / menge if menge > 0 else 0
    }

def perform_calculation(data):
    kunde = data.get('kunde', {})
    positions_from_form = data.get('positions', [])
    adjustments = data.get('manual_adjustments', {})
    
    positions_total_brutto = 0
    live_positions_details = []

    for i, pos_form in enumerate(positions_from_form):
        produkt_id = pos_form.get('produkt_id')
        produkt_typ = pos_form.get('produkt_typ')

        total_menge_position = sum(var.get('menge', 0) for var in pos_form.get('varianten', []))
        if total_menge_position == 0: continue

        produkt_name = "Unbekannt"
        textil_gesamt_brutto = 0
        textil_einzel_brutto_dein_vk = 0
        textil_gesamt_vor_rabatt = 0
        textil_gesamrabatt_betrag = 0
        textil_rabatt_prozent = 0

        # NUR Textilkosten berechnen, wenn es kein mitgebrachtes Textil ist
        if produkt_typ != 'mitgebracht' and produkt_id:
            produkt = Produkt.query.get(produkt_id)
            if not produkt: continue
            
            produkt_name = produkt.name
            ek_netto_produkt_basis = produkt.ek_netto_basis or 0
            vk_netto = ek_netto_produkt_basis * (1 + MARGE_PROZENT)
            textil_einzel_brutto_dein_vk = vk_netto * (1 + MWST_SATZ)
            
            textil_rabatt_prozent = get_textil_rabatt(total_menge_position)
            textil_gesamt_vor_rabatt = textil_einzel_brutto_dein_vk * total_menge_position
            textil_gesamrabatt_betrag = textil_gesamt_vor_rabatt * textil_rabatt_prozent
            textil_gesamt_brutto = textil_gesamt_vor_rabatt - textil_gesamrabatt_betrag
        elif produkt_typ == 'mitgebracht':
            produkt_name = pos_form.get('produkt_beschreibung', 'Mitgebrachtes Textil')

        druck_data = { 'drucke_details': pos_form.get('drucke', []), 'total_menge': total_menge_position }
        druck_costs = _calculate_druck_costs(druck_data)

        pos_gesamt_brutto = textil_gesamt_brutto + druck_costs['druck_gesamt_brutto'] + druck_costs['zuschlag_freistellen_brutto']
        positions_total_brutto += pos_gesamt_brutto

        live_pos_data = {
            "pos": i + 1, "name": produkt_name, "menge": total_menge_position,
            "artikel_liste": [f"{v['menge']}x {v.get('groesse', '')} {v.get('farbe', '')}".strip() for v in pos_form.get('varianten', []) if v.get('menge', 0) > 0],
            "pos_gesamt_brutto": pos_gesamt_brutto,
            "textil_einzel_brutto": textil_einzel_brutto_dein_vk,
            "textil_gesamt_vor_rabatt": textil_gesamt_vor_rabatt,
            "textil_gesamrabatt_betrag": textil_gesamrabatt_betrag,
            "textil_rabatt_prozent": textil_rabatt_prozent * 100,
            "textil_einzel_n_rabatt": textil_gesamt_brutto / total_menge_position if total_menge_position > 0 else 0,
            "textil_gesamt_brutto": textil_gesamt_brutto
        }
        live_pos_data.update(druck_costs)
        live_positions_details.append(live_pos_data)

    dringlichkeits_zuschlag_brutto = positions_total_brutto * DRINGLICHKEITS_ZUSCHLAEGE.get(data.get('dringlichkeit', 'Standard'), 0)
    
    berechneter_total_brutto = positions_total_brutto + dringlichkeits_zuschlag_brutto
    
    if adjustments.get('surcharge', {}).get('applied'):
        berechneter_total_brutto += adjustments['surcharge']['amount']
    if adjustments.get('additional_costs', {}).get('applied'):
        berechneter_total_brutto += adjustments['additional_costs']['amount']

    rabatt_betrag_brutto = 0
    if adjustments.get('discount', {}).get('applied'):
        rabatt_betrag_brutto = berechneter_total_brutto * (adjustments['discount']['percent'] / 100)
        berechneter_total_brutto -= rabatt_betrag_brutto
    
    final_brutto = adjustments.get('fixed_price', 0) if adjustments.get('mode') == 'fixed' else berechneter_total_brutto
    final_netto = final_brutto / (1 + MWST_SATZ)
    final_mwst = final_brutto - final_netto

    date_str = datetime.datetime.now().strftime('%d-%m-%Y')
    identifier_raw = kunde.get('name', 'KUNDE')
    identifier_base = re.sub(r'[^a-zA-Z0-9]', '', identifier_raw).upper()
    angebot_nr = f"{date_str}-{identifier_base}"

    return {
        "positionen": live_positions_details,
        "positions_total_brutto": positions_total_brutto,
        "dringlichkeits_zuschlag_brutto": dringlichkeits_zuschlag_brutto,
        "rabatt_betrag_brutto": rabatt_betrag_brutto,
        "final_brutto": final_brutto,
        "final_netto": final_netto,
        "final_mwst": final_mwst,
        "angebot_nr": angebot_nr,
        "berechneter_total_brutto": berechneter_total_brutto
    }