"""
Module de sécurité pour l'application Flask
Gère le chiffrement des mots de passe, la validation XSS, et autres fonctions de sécurité
"""
import bcrypt
import bleach
import re
from html import escape

# Configuration pour bleach (sanitization HTML)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    '*': ['class']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def hash_password(password):
    """
    Hash un mot de passe avec bcrypt
    
    Args:
        password: Mot de passe en clair
    
    Returns:
        str: Mot de passe hashé
    """
    if not password:
        raise ValueError("Le mot de passe ne peut pas être vide")
    
    # Générer un salt et hasher le mot de passe
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = bon équilibre sécurité/performance
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(password, hashed):
    """
    Vérifie si un mot de passe correspond au hash
    
    Args:
        password: Mot de passe en clair
        hashed: Mot de passe hashé (bcrypt)
    
    Returns:
        bool: True si le mot de passe correspond
    """
    if not password or not hashed:
        return False
    
    try:
        # Si le hash est en format SHA256 (ancien système), retourner False
        # pour forcer la migration vers bcrypt
        if len(hashed) == 64 and re.match(r'^[a-f0-9]{64}$', hashed):
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def sanitize_html(html_content):
    """
    Nettoie le contenu HTML pour prévenir les attaques XSS
    
    Args:
        html_content: Contenu HTML à nettoyer
    
    Returns:
        str: Contenu HTML nettoyé
    """
    if not html_content:
        return ""
    
    # Utiliser bleach pour nettoyer le HTML
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    return cleaned


def sanitize_text(text):
    """
    Nettoie le texte pour prévenir les attaques XSS (échappe les caractères HTML)
    
    Args:
        text: Texte à nettoyer
    
    Returns:
        str: Texte nettoyé
    """
    if not text:
        return ""
    
    # Échapper les caractères HTML spéciaux
    return escape(text)


def sanitize_input_advanced(text, max_length=None, allow_html=False):
    """
    Nettoie une entrée utilisateur de manière avancée
    
    Args:
        text: Texte à nettoyer
        max_length: Longueur maximale autorisée
        allow_html: Si True, permet le HTML (sera nettoyé), sinon échappe tout
    
    Returns:
        str: Texte nettoyé
    """
    if not text:
        return ""
    
    # Supprimer les espaces en début/fin
    text = text.strip()
    
    # Nettoyer selon le type
    if allow_html:
        text = sanitize_html(text)
    else:
        text = sanitize_text(text)
    
    # Appliquer la longueur maximale
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_csrf_token(token, session_token):
    """
    Valide un token CSRF
    
    Args:
        token: Token à valider
        session_token: Token stocké en session
    
    Returns:
        bool: True si le token est valide
    """
    if not token or not session_token:
        return False
    
    # Comparaison sécurisée pour éviter les attaques par timing
    return bcrypt.checkpw(token.encode('utf-8'), session_token.encode('utf-8'))


def generate_csrf_token():
    """
    Génère un token CSRF sécurisé
    
    Returns:
        str: Token CSRF
    """
    import secrets
    token = secrets.token_urlsafe(32)
    return token

