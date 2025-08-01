from . import db
from sqlalchemy.sql import func
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Aufgabe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inhalt = db.Column(db.String(200), nullable=False)
    erledigt = db.Column(db.Boolean, default=False)
    erstellt_am = db.Column(db.DateTime(timezone=True), server_default=func.now())

class Produkt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hersteller = db.Column(db.String(100))
    beschreibung = db.Column(db.Text)
    ek_netto_basis = db.Column(db.Float)
    varianten = db.relationship('ArtikelVariante', backref='produkt', lazy=True, cascade="all, delete-orphan")

class ArtikelVariante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produkt_id = db.Column(db.Integer, db.ForeignKey('produkt.id'), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    hersteller_sku = db.Column(db.String(50))
    farbe = db.Column(db.String(50))
    groesse = db.Column(db.String(20))
    einkaufspreis_netto = db.Column(db.Float)
    lagerbestand = db.Column(db.Integer, default=0)
    ist_standard = db.Column(db.Boolean, default=False)
    lieferant_id = db.Column(db.Integer, db.ForeignKey('lieferant.id'), nullable=True)
    bestellpositionen = db.relationship('Bestellposition', back_populates='artikel_variante')
    lagerbewegungen = db.relationship('Lagerbewegung', back_populates='artikel_variante')


class Lieferant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    kontaktperson = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefon = db.Column(db.String(50))
    artikel = db.relationship('ArtikelVariante', backref='lieferant', lazy=True)
    bestellungen = db.relationship('Bestellung', back_populates='lieferant')


class Angebot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    angebot_nr = db.Column(db.String(50), unique=True, nullable=False)
    kunde_name = db.Column(db.String(150))
    datum = db.Column(db.Date, nullable=False)
    kalkulations_daten = db.Column(db.Text)
    status = db.Column(db.String(50), default='Entwurf')
    kunden_token = db.Column(db.String(36), unique=True, nullable=False, default=generate_uuid)
    auftrags_ereignisse = db.relationship('AuftragsEreignis', backref='auftrag', lazy='dynamic', cascade="all, delete-orphan")
    auftrags_dateien = db.relationship('AuftragsDatei', backref='auftrag', lazy='dynamic', cascade="all, delete-orphan")
    kunde_id = db.Column(db.Integer, db.ForeignKey('kunde.id'), nullable=True)

class AuftragsEreignis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auftrag_id = db.Column(db.Integer, db.ForeignKey('angebot.id'), nullable=False)
    typ = db.Column(db.String(50), nullable=False)
    inhalt = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(50))
    erstellt_am = db.Column(db.DateTime(timezone=True), server_default=func.now())

class AuftragsDatei(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auftrag_id = db.Column(db.Integer, db.ForeignKey('angebot.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    saved_filename = db.Column(db.String(255), nullable=False)
    upload_datum = db.Column(db.DateTime(timezone=True), server_default=func.now())
    hochgeladen_von = db.Column(db.String(50))
    dokument_typ = db.Column(db.String(50))
    freigabe_status = db.Column(db.String(50), default='N/A')

    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'saved_filename': self.saved_filename,
            'upload_datum': self.upload_datum.isoformat(),
            'hochgeladen_von': self.hochgeladen_von,
            'dokument_typ': self.dokument_typ,
            'freigabe_status': self.freigabe_status,
        }

class Kunde(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    firma = db.Column(db.String(150))
    email = db.Column(db.String(150))
    telefon = db.Column(db.String(50))
    erstellt_am = db.Column(db.DateTime(timezone=True), server_default=func.now())
    auftraege = db.relationship('Angebot', backref='kunde', lazy=True)


# --- NEUE MODELLE FÜR BESCHAFFUNG ---
class Bestellung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bestell_nr = db.Column(db.String(50), unique=True, nullable=False)
    lieferant_id = db.Column(db.Integer, db.ForeignKey('lieferant.id'), nullable=False)
    erstellt_am = db.Column(db.DateTime(timezone=True), server_default=func.now())
    status = db.Column(db.String(50), default='Offen')
    lieferant = db.relationship('Lieferant', back_populates='bestellungen')
    positionen = db.relationship('Bestellposition', back_populates='bestellung', cascade="all, delete-orphan")

class Bestellposition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bestellung_id = db.Column(db.Integer, db.ForeignKey('bestellung.id'), nullable=False)
    artikel_variante_id = db.Column(db.Integer, db.ForeignKey('artikel_variante.id'), nullable=False)
    menge = db.Column(db.Integer, nullable=False)
    einzelpreis_netto = db.Column(db.Float)
    bestellung = db.relationship('Bestellung', back_populates='positionen')
    artikel_variante = db.relationship('ArtikelVariante', back_populates='bestellpositionen')

class Lagerbewegung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artikel_variante_id = db.Column(db.Integer, db.ForeignKey('artikel_variante.id'), nullable=False)
    menge = db.Column(db.Integer, nullable=False) # Positiv für Zugang, negativ für Abgang
    typ = db.Column(db.String(50)) # z.B. 'Wareneingang', 'Verkauf', 'Korrektur'
    referenz = db.Column(db.String(100)) # z.B. Bestellnummer, Auftragsnummer
    erstellt_am = db.Column(db.DateTime(timezone=True), server_default=func.now())
    artikel_variante = db.relationship('ArtikelVariante', back_populates='lagerbewegungen')
