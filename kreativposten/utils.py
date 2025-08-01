# kreativposten/utils.py
import os
import re
import qrcode
import io
import base64
from flask import current_app, render_template
from flask_mail import Message
from markupsafe import Markup, escape
from .models import db, AuftragsEreignis

# E-Mail-Funktion, die auf 'mail' aus der App zugreift
def sende_email(empfaenger, betreff, template, **kwargs):
    mail = current_app.extensions.get('mail')
    if not empfaenger:
        print(f"E-Mail-Versand an leere Adresse unterdrückt. Betreff: {betreff}")
        return
    try:
        msg = Message(betreff, recipients=[empfaenger])
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
        print(f"E-Mail an {empfaenger} gesendet. Betreff: {betreff}")
    except Exception as e:
        print(f"E-Mail-Fehler: {e}")

# Logging-Funktion
def log_ereignis(auftrag_id, typ, inhalt, sender='System', datei_id=None):
    ereignis = AuftragsEreignis(
        auftrag_id=auftrag_id,
        typ=typ,
        inhalt=inhalt,
        sender=sender,
        bezogene_datei_id=datei_id
    )
    db.session.add(ereignis)
    db.session.commit()

# QR-Code-Generator
def generate_qr_code_base64(url):
    qr_img = qrcode.make(url, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6)
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Template-Filter für Zeilenumbrüche
_nl2br_re = re.compile(r'\r\n|\r|\n')
def nl2br(value):
    if not value:
        return ""
    escaped_value = escape(value)
    result = _nl2br_re.sub('<br>\n', escaped_value)
    return Markup(result)