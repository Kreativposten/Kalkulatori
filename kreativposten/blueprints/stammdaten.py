# kreativposten/blueprints/stammdaten.py
import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from ..models import db, Produkt, ArtikelVariante, Lieferant, Bestellposition, Lagerbewegung

stammdaten_bp = Blueprint('stammdaten', __name__, template_folder='../templates')

@stammdaten_bp.route('/stammdaten')
def stammdaten():
    return render_template('stammdaten.html', active_page='stammdaten')

# NEUE ROUTE für die Übersicht der Standardtextilien
@stammdaten_bp.route('/stammdaten/standardtextilien')
def standardtextilien_uebersicht():
    standard_artikel = ArtikelVariante.query.filter_by(ist_standard=True).join(Produkt).order_by(Produkt.name, ArtikelVariante.farbe, ArtikelVariante.groesse).all()
    return render_template('standardtextilien.html', artikel=standard_artikel, active_page='stammdaten')

# NEUE ROUTE, um den Standard-Status umzuschalten
@stammdaten_bp.route('/stammdaten/artikel/<int:variante_id>/toggle-standard', methods=['POST'])
def toggle_standard_status(variante_id):
    variante = ArtikelVariante.query.get_or_404(variante_id)
    variante.ist_standard = not variante.ist_standard
    db.session.commit()
    flash(f'Standard-Status für {variante.produkt.name} ({variante.farbe}/{variante.groesse}) wurde geändert.', 'success')
    return redirect(url_for('stammdaten.produkt_varianten_verwalten', produkt_id=variante.produkt_id))

@stammdaten_bp.route('/stammdaten/produkte', methods=['GET', 'POST'])
def produkte_verwalten():
    if request.method == 'POST':
        neues_produkt = Produkt(
            name=request.form['name'],
            hersteller=request.form['hersteller'],
            beschreibung=request.form['beschreibung'],
            ek_netto_basis=float(request.form['einkaufspreis_netto_produkt']) if request.form.get('einkaufspreis_netto_produkt') else None
        )
        db.session.add(neues_produkt)
        db.session.commit()
        flash('Neues Produkt erfolgreich angelegt.', 'success')
        return redirect(url_for('stammdaten.produkte_verwalten'))
    
    alle_produkte = Produkt.query.order_by(Produkt.name).all()
    return render_template('produkte.html', produkte=alle_produkte, active_page='stammdaten')

@stammdaten_bp.route('/stammdaten/artikel', methods=['GET'])
def artikel_uebersicht():
    alle_produkte = Produkt.query.order_by(Produkt.name).all()
    return render_template('artikel_uebersicht.html', produkte=alle_produkte, active_page='stammdaten')


@stammdaten_bp.route('/stammdaten/produkt/<int:produkt_id>/varianten', methods=['GET', 'POST'])
def produkt_varianten_verwalten(produkt_id):
    produkt = Produkt.query.get_or_404(produkt_id)
    
    if request.method == 'POST':
        sku = request.form['sku']
        farbe = request.form['farbe']
        groesse = request.form['groesse']
        
        existing_variant_by_props = ArtikelVariante.query.filter_by(
            produkt_id=produkt.id, farbe=farbe, groesse=groesse
        ).first()
        if existing_variant_by_props:
            flash(f"Fehler: Eine Variante von '{produkt.name}' mit Farbe '{farbe}' und Größe '{groesse}' existiert bereits (SKU: {existing_variant_by_props.sku}).", 'danger')
            return redirect(url_for('stammdaten.produkt_varianten_verwalten', produkt_id=produkt.id))

        existing_variant_by_sku = ArtikelVariante.query.filter_by(sku=sku).first()
        if existing_variant_by_sku:
            flash(f"Fehler: Eine Variante mit der SKU '{sku}' existiert bereits (Produkt: {existing_variant_by_sku.produkt.name}).", 'danger')
            return redirect(url_for('stammdaten.produkt_varianten_verwalten', produkt_id=produkt.id))
        
        lieferant_id = request.form.get('lieferant_id')
        lieferant_obj = Lieferant.query.get(int(lieferant_id)) if lieferant_id and lieferant_id != '' else None

        neue_variante = ArtikelVariante(
            produkt_id=produkt.id,
            farbe=farbe,
            groesse=groesse,
            sku=sku,
            hersteller_sku=request.form['hersteller_sku'],
            einkaufspreis_netto=float(request.form['einkaufspreis_netto']) if request.form.get('einkaufspreis_netto') else None,
            lagerbestand=int(request.form['lagerbestand']) if request.form.get('lagerbestand') else 0,
            ist_standard= 'ist_standard' in request.form,
            lieferant_id=lieferant_obj.id if lieferant_obj else None
        )
        db.session.add(neue_variante)
        try:
            db.session.commit()
            flash(f'Neue Variante ({farbe} / {groesse}) für {produkt.name} erfolgreich angelegt.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Fehler beim Anlegen der Variante: {e}", 'danger')
        return redirect(url_for('stammdaten.produkt_varianten_verwalten', produkt_id=produkt.id))
    
    varianten = ArtikelVariante.query.filter_by(produkt_id=produkt.id).options(db.joinedload(ArtikelVariante.lieferant)).order_by(ArtikelVariante.farbe, ArtikelVariante.groesse).all()
    alle_lieferanten = Lieferant.query.order_by(Lieferant.name).all()
    return render_template('artikel_varianten.html', produkt=produkt, varianten=varianten, lieferanten=alle_lieferanten, active_page='stammdaten')


@stammdaten_bp.route('/stammdaten/artikel/bearbeiten/<int:variante_id>', methods=['GET', 'POST'])
def artikel_bearbeiten(variante_id):
    variante = ArtikelVariante.query.get_or_404(variante_id)
    produkt = variante.produkt

    if request.method == 'POST':
        new_farbe = request.form['farbe']
        new_groesse = request.form['groesse']
        new_sku = request.form['sku']

        if new_farbe != variante.farbe or new_groesse != variante.groesse:
            existing_variant_by_props = ArtikelVariante.query.filter(
                ArtikelVariante.produkt_id == produkt.id,
                ArtikelVariante.farbe == new_farbe,
                ArtikelVariante.groesse == new_groesse,
                ArtikelVariante.id != variante.id
            ).first()
            if existing_variant_by_props:
                flash(f"Fehler: Eine Variante von '{produkt.name}' mit Farbe '{new_farbe}' und Größe '{new_groesse}' existiert bereits (SKU: {existing_variant_by_props.sku}).", 'danger')
                return redirect(url_for('stammdaten.artikel_bearbeiten', variante_id=variante.id))

        if new_sku != variante.sku:
            existing_variant_by_sku = ArtikelVariante.query.filter(
                ArtikelVariante.sku == new_sku,
                ArtikelVariante.id != variante.id
            ).first()
            if existing_variant_by_sku:
                flash(f"Fehler: Eine Variante mit der SKU '{new_sku}' existiert bereits (Produkt: {existing_variant_by_sku.produkt.name}).", 'danger')
                return redirect(url_for('stammdaten.artikel_bearbeiten', variante_id=variante.id))
        
        variante.farbe = new_farbe
        variante.groesse = new_groesse
        variante.sku = new_sku
        variante.hersteller_sku = request.form['hersteller_sku']
        variante.einkaufspreis_netto = float(request.form['einkaufspreis_netto']) if request.form.get('einkaufspreis_netto') else None
        variante.lagerbestand = int(request.form['lagerbestand']) if request.form.get('lagerbestand') else 0
        variante.ist_standard = 'ist_standard' in request.form
        variante.lieferant_id = int(request.form['lieferant_id']) if request.form.get('lieferant_id') else None
        
        try:
            db.session.commit()
            flash('Artikel erfolgreich aktualisiert.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Fehler beim Aktualisieren des Artikels: {e}", 'danger')
        return redirect(url_for('stammdaten.produkt_varianten_verwalten', produkt_id=produkt.id))

    alle_lieferanten = Lieferant.query.order_by(Lieferant.name).all()
    return render_template('artikel_bearbeiten.html', artikel=variante, produkt=produkt, lieferanten=alle_lieferanten, active_page='stammdaten')


@stammdaten_bp.route('/stammdaten/artikel/loeschen/<int:variante_id>', methods=['POST'])
def artikel_loeschen(variante_id):
    variante = ArtikelVariante.query.get_or_404(variante_id)
    produkt_id = variante.produkt_id

    try:
        in_bestellung = Bestellposition.query.filter_by(variante_id=variante.id).first()
        if in_bestellung:
            flash(f"Artikel '{variante.sku}' kann nicht gelöscht werden, da er in Bestellungen verwendet wird.", 'danger')
            return redirect(url_for('stammdaten.produkt_varianten_verwalten', produkt_id=produkt_id))

        Lagerbewegung.query.filter_by(variante_id=variante.id).delete()
        
        db.session.delete(variante)
        db.session.commit()
        flash('Artikel und zugehörige Lagerbewegungen erfolgreich gelöscht.', 'success')
    except Exception as e:
            db.session.rollback()
            flash(f"Fehler beim Löschen des Artikels: {e}", 'danger')
    return redirect(url_for('stammdaten.produkt_varianten_verwalten', produkt_id=produkt_id))


@stammdaten_bp.route('/stammdaten/lieferanten', methods=['GET', 'POST'])
def lieferanten_verwalten():
    if request.method == 'POST':
        neuer_lieferant = Lieferant(
            name=request.form['name'],
            kontaktperson=request.form['kontaktperson'],
            email=request.form['email'],
            telefon=request.form['telefon']
        )
        db.session.add(neuer_lieferant)
        db.session.commit()
        flash('Neuer Lieferant erfolgreich angelegt.', 'success')
        return redirect(url_for('stammdaten.lieferanten_verwalten'))
    
    alle_lieferanten = Lieferant.query.order_by(Lieferant.name).all()
    return render_template('lieferanten.html', lieferanten=alle_lieferanten, active_page='stammdaten')

@stammdaten_bp.route('/admin/import-artikeldaten', methods=['GET', 'POST'])
def import_artikeldaten():
    if request.method == 'POST':
        project_root = os.path.join(current_app.root_path, '..')
        style_list_path = os.path.join(project_root, 'X021118_Article_Export_2025-07_NEW(EUR).xlsx - Style List.csv')
        sku_list_path = os.path.join(project_root, 'X021118_Article_Export_2025-07_NEW(EUR).xlsx - SKU List.csv')

        if not os.path.exists(style_list_path) or not os.path.exists(sku_list_path):
            flash('Fehler: Die CSV-Dateien (Style List, SKU List) wurden nicht gefunden.', 'danger')
            return redirect(url_for('stammdaten.import_artikeldaten'))
        
        try:
            df_styles = pd.read_csv(style_list_path)
            df_skus = pd.read_csv(sku_list_path)

            imported_products_count = 0
            style_code_to_name = df_styles.set_index('Style')['Name1'].to_dict()

            for index, row in df_styles.iterrows():
                style_code = str(row['Style']).strip()
                product_name_from_style = str(row['Name1']).strip()
                manufacturer_name = str(row['Manufacturer']).strip() if 'Manufacturer' in row and pd.notna(row['Manufacturer']) else 'Unbekannt'
                
                if manufacturer_name == 'Unbekannt':
                    sku_manufacturer_series = df_skus[df_skus['Style'] == style_code]['Manufacturer']
                    if not sku_manufacturer_series.empty:
                        sku_manufacturer = sku_manufacturer_series.iloc[0]
                        if pd.notna(sku_manufacturer):
                            manufacturer_name = str(sku_manufacturer).strip()

                if not style_code or not product_name_from_style:
                    continue

                produkt = Produkt.query.filter_by(name=product_name_from_style).first()
                if not produkt:
                    produkt = Produkt(
                        name=product_name_from_style,
                        hersteller=manufacturer_name,
                        beschreibung=row['Product-Description (german)'] if 'Product-Description (german)' in row and pd.notna(row['Product-Description (german)']) else None,
                        ek_netto_basis=None
                    )
                    db.session.add(produkt)
                    imported_products_count += 1
                else:
                    produkt.hersteller = manufacturer_name
                    produkt.beschreibung = row['Product-Description (german)'] if 'Product-Description (german)' in row and pd.notna(row['Product-Description (german)']) else produkt.beschreibung
                db.session.flush()

            imported_variants_count = 0
            updated_variants_count = 0

            for col in ['VKEinzel', 'Ihr Preis']:
                if col in df_skus.columns:
                    df_skus[col] = df_skus[col].astype(str).str.replace(',', '.', regex=False)
                    df_skus[col] = pd.to_numeric(df_skus[col], errors='coerce') 

            for index, row in df_skus.iterrows():
                sku = str(row['SKU']).strip()
                style_code = str(row['Style']).strip()
                farbe = str(row['Colour']).strip()
                groesse = str(row['Size']).strip()
                hersteller_sku = str(row['ManufacturerSKU']).strip() if pd.notna(row['ManufacturerSKU']) else None
                einkaufspreis_netto_variante = row['Ihr Preis'] if 'Ihr Preis' in row and pd.notna(row['Ihr Preis']) else None
                
                if not sku or not style_code or not farbe or not groesse:
                    continue

                product_name_for_lookup = style_code_to_name.get(style_code)
                produkt = None
                if product_name_for_lookup:
                    produkt = Produkt.query.filter_by(name=product_name_for_lookup).first()
                
                if not produkt:
                    continue

                lieferant_name = str(row['Manufacturer']).strip()
                lieferant = Lieferant.query.filter_by(name=lieferant_name).first()
                if not lieferant:
                    lieferant = Lieferant(name=lieferant_name)
                    db.session.add(lieferant)
                    db.session.flush()

                variante = ArtikelVariante.query.filter_by(produkt_id=produkt.id, farbe=farbe, groesse=groesse).first()

                if not variante:
                    variante = ArtikelVariante(
                        produkt_id=produkt.id,
                        farbe=farbe,
                        groesse=groesse,
                        sku=sku,
                        hersteller_sku=hersteller_sku,
                        einkaufspreis_netto=einkaufspreis_netto_variante,
                        lagerbestand=0,
                        ist_standard=False,
                        lieferant_id=lieferant.id
                    )
                    db.session.add(variante)
                    imported_variants_count += 1
                else:
                    variante.sku = sku
                    variante.hersteller_sku = hersteller_sku
                    variante.einkaufspreis_netto = einkaufspreis_netto_variante
                    variante.lieferant_id = lieferant.id
                    updated_variants_count += 1
                
                if produkt.ek_netto_basis is None or produkt.ek_netto_basis == 0.0:
                    if einkaufspreis_netto_variante is not None and einkaufspreis_netto_variante > 0:
                        produkt.ek_netto_basis = float(einkaufspreis_netto_variante)
                
            db.session.commit()
            flash(f'Import erfolgreich! {imported_products_count} neue Produkte und {imported_variants_count} neue Varianten importiert, {updated_variants_count} Varianten aktualisiert.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Fehler beim Importieren der Artikeldaten: {e}", 'danger')
            import traceback
            traceback.print_exc()
        return redirect(url_for('stammdaten.import_artikeldaten'))
        
    return render_template('import_artikeldaten.html', active_page='stammdaten')