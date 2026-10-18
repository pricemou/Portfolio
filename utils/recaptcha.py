"""Vérification reCAPTCHA v2 (case « Je ne suis pas un robot »)."""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

SITEVERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
MSG_REQUIRED = "Cochez « Je ne suis pas un robot » pour continuer."
MSG_EXPIRED = "La vérification a expiré. Cochez à nouveau la case."
MSG_UNAVAILABLE = "La vérification anti-robot est momentanément indisponible. Réessayez."

# Clés du domaine claude225.pythonanywhere.com.
# La clé de site est publique (elle est dans le HTML). La clé secrète sert à la vérification.
_SITE_KEY = "6Lcfq_UtAAAAAIuZHZ5omo790G4XpB47eWjd7MHW"
_SECRET_KEY = "6Lcfq_UtAAAAAAC2celAOcUYzfCauKaNEROqkixr"


def recaptcha_site_key() -> str:
    return (os.getenv("RECAPTCHA_SITE_KEY") or _SITE_KEY).strip()


def recaptcha_secret_key() -> str:
    return (os.getenv("RECAPTCHA_SECRET_KEY") or _SECRET_KEY).strip()


def recaptcha_enabled() -> bool:
    return bool(recaptcha_site_key() and recaptcha_secret_key())


def verify_recaptcha(token, remote_ip=None):
    """Valide le jeton du widget.

    Sans clés configurées, la vérification est ignorée pour ne pas bloquer
    un environnement local. Retourne (ok, message).
    """
    if not recaptcha_enabled():
        return True, None

    token = (token or "").strip()
    if not token:
        return False, MSG_REQUIRED

    payload = urllib.parse.urlencode({
        "secret": recaptcha_secret_key(),
        "response": token,
        "remoteip": remote_ip or "",
    }).encode("utf-8")
    request = urllib.request.Request(SITEVERIFY_URL, data=payload, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning("reCAPTCHA indisponible: %s", exc)
        return False, MSG_UNAVAILABLE

    if data.get("success"):
        return True, None

    codes = data.get("error-codes") or []
    if "invalid-input-secret" in codes:
        logger.error("RECAPTCHA_SECRET_KEY refusée par Google")
    if "timeout-or-duplicate" in codes:
        return False, MSG_EXPIRED
    return False, MSG_REQUIRED
