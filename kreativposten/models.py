# kreativposten/models.py
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# --- Datenbank Modelle ---
class Angebot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    angebot_nr = db.Column(db.String(100), nullable=False, unique=True)
    kunde_name = db.Column(db.String(200))
    datum = db.Column(db.DateTime, default=datetime.datetime.now)
    angebot_data = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Entwurf')
    kunden_token = db.Column(db.String(36), unique=True, nullable=True)

class AuftragsDatei(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(300))
    saved_filename = db.Column(db.String(300), unique=True)
    upload_datum = db.Column(db.DateTime, default=datetime.datetime.now)
    druckposition = db.Column(db.String(100), nullable=True)
    notizen = db.Column(db.Text, nullable=True)
    hochgeladen_von = db.Column(db.String(50), default='Kunde', nullable=False)
    dokument_typ = db.Column(db.String(50), default='Kundendatei', nullable=False)
    freigabe_status = db.Column(db.String(50), nullable=True)
    freigabe_kommentar = db.Column(db.Text, nullable=True)
    auftrag_id = db.Column(db.Integer, db.ForeignKey('angebot.id'), nullable=False)
    auftrag = db.relationship('Angebot', backref=db.backref('dateien', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'saved_filename': self.saved_filename,
            'freigabe_status': self.freigabe_status
        }

class Aufgabe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inhalt = db.Column(db.String(500), nullable=False)
    erledigt = db.Column(db.Boolean, default=False, nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.datetime.now)

class AuftragsEreignis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auftrag_id = db.Column(db.Integer, db.ForeignKey('angebot.id'), nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.datetime.now)
    typ = db.Column(db.String(50), nullable=False) 
    sender = db.Column(db.String(50), nullable=False)
    inhalt = db.Column(db.Text, nullable=False)
    bezogene_datei_id = db.Column(db.Integer, db.ForeignKey('auftrags_datei.id'), nullable=True)
    
    auftrag = db.relationship('Angebot', backref=db.backref('ereignisse', lazy=True, cascade="all, delete-orphan"))
    datei = db.relationship('AuftragsDatei')

class Produkt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    hersteller = db.Column(db.String(200))
    beschreibung = db.Column(db.Text)
    # GUTE BENENNUNG: Wir nennen die Spalte jetzt so, wie sie gemeint ist.
    ek_netto_basis = db.Column(db.Float, comment="Basis-Einkaufspreis Netto für das Produkt als Kalkulationsgrundlage")
    
    varianten = db.relationship('ArtikelVariante', backref='produkt', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hersteller': self.hersteller,
            'beschreibung': self.beschreibung,
            'ek_netto_basis': self.ek_netto_basis
        }

class ArtikelVariante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produkt_id = db.Column(db.Integer, db.ForeignKey('produkt.id'), nullable=False)
    farbe = db.Column(db.String(100))
    groesse = db.Column(db.String(50))
    sku = db.Column(db.String(100), unique=True, nullable=False)
    hersteller_sku = db.Column(db.String(100))
    einkaufspreis_netto = db.Column(db.Float)
    lagerbestand = db.Column(db.Integer, nullable=False, default=0)
    ist_standard = db.Column(db.Boolean, default=False, nullable=False)
    lieferant_id = db.Column(db.Integer, db.ForeignKey('lieferant.id'), nullable=True)
    __table_args__ = (db.UniqueConstraint('produkt_id', 'farbe', 'groesse', name='_produkt_farbe_groesse_uc'),)

class Lieferant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    kontaktperson = db.Column(db.String(200))
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(50))
    varianten = db.relationship('ArtikelVariante', backref='lieferant', lazy=True)
    bestellungen = db.relationship('Bestellung', backref='lieferant', lazy=True)

class Lagerbewegung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menge = db.Column(db.Integer, nullable=False)
    typ = db.Column(db.String(100), nullable=False)
    datum = db.Column(db.DateTime, default=datetime.datetime.now)
    notiz = db.Column(db.Text)
    variante_id = db.Column(db.Integer, db.ForeignKey('artikel_variante.id'), nullable=False)
    variante = db.relationship('ArtikelVariante', backref=db.backref('bewegungen', lazy=True))
    auftrag_id = db.Column(db.Integer, db.ForeignKey('angebot.id'), nullable=True)
    auftrag = db.relationship('Angebot')

class Bestellung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bestell_nr = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Entwurf')
    erstellt_am = db.Column(db.DateTime, default=datetime.datetime.now)
    lieferant_id = db.Column(db.Integer, db.ForeignKey('lieferant.id'), nullable=False)
    positionen = db.relationship('Bestellposition', backref='bestellung', lazy=True, cascade="all, delete-orphan")

class Bestellposition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menge = db.Column(db.Integer, nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey('artikel_variante.id'), nullable=False)
    bestellung_id = db.Column(db.Integer, db.ForeignKey('bestellung.id'), nullable=False)
    variante = db.relationship('ArtikelVariante')