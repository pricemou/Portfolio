"""Alertes email pour événements de sécurité critiques (avec anti-bruit)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta

_last_sent: dict[str, datetime] = {}


def _cooldown_ok(key: str, minutes: int = 30) -> bool:
    now = datetime.utcnow()
    last = _last_sent.get(key)
    if last and now - last < timedelta(minutes=minutes):
        return False
    _last_sent[key] = now
    return True


def send_security_alert(subject: str, body: str, dedupe_key: str = "generic") -> bool:
    """Envoie une alerte si Flask-Mail est configuré. Retourne True si envoyé."""
    if not _cooldown_ok(dedupe_key):
        return False
    to_addr = os.getenv("NOTIFICATION_EMAIL") or os.getenv("MAIL_USERNAME")
    if not to_addr:
        return False
    try:
        from flask import current_app
        mail = current_app.extensions.get("mail")
        if mail is None:
            return False
        from flask_mail import Message
        msg = Message(
            subject=f"[Portfolio] {subject}",
            recipients=[to_addr],
            body=body,
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur alerte email: {e}")
        return False
