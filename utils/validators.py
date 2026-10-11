"""
Module de validation pour les formulaires et données
"""
import re
from datetime import datetime
from urllib.parse import urlparse

def validate_email(email):
    """Valide le format d'un email"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url):
    """Valide le format d'une URL http(s) (chemins Unsplash, query strings, etc.)."""
    if not url:
        return True  # URL optionnelle
    try:
        parsed = urlparse(str(url).strip())
    except Exception:
        return False
    if parsed.scheme not in ('http', 'https'):
        return False
    if not parsed.netloc:
        return False
    return True


def valid_project_image_path(path):
    """Accepte URL http(s), chemins locaux images/ ou uploads/ (éventuellement préfixés static/)."""
    if not path:
        return True
    p = str(path).strip()
    if not p:
        return True
    if validate_url(p):
        return True
    if p.startswith('/static/'):
        p = p[len('/static/'):]
    elif p.startswith('static/'):
        p = p[len('static/'):]
    return p.startswith('images/') or p.startswith('uploads/')

def validate_required(data, fields):
    """Valide que les champs requis sont présents et non vides"""
    errors = []
    for field in fields:
        if field not in data or not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            errors.append(f"Le champ '{field}' est requis")
    return errors

def sanitize_input(text, max_length=None):
    """Nettoie et valide un texte d'entrée"""
    if not text:
        return ""
    # Supprimer les espaces en début/fin
    text = text.strip()
    # Limiter la longueur si spécifié
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text

def validate_date(date_string, format='%Y-%m-%d'):
    """Valide le format d'une date"""
    try:
        datetime.strptime(date_string, format)
        return True
    except (ValueError, TypeError):
        return False

def validate_integer(value, min_value=None, max_value=None):
    """Valide qu'une valeur est un entier dans une plage donnée"""
    try:
        int_value = int(value)
        if min_value is not None and int_value < min_value:
            return False
        if max_value is not None and int_value > max_value:
            return False
        return True
    except (ValueError, TypeError):
        return False


