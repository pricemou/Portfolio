import os
import sys
import socket

# Configuration UTF-8 pour Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        pass

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
from dotenv import load_dotenv
from database import get_mongo_client, init_database
from functools import wraps
from bson import ObjectId
import json
import re
from werkzeug.exceptions import BadRequest, InternalServerError

# Flask-Limiter (optionnel)
FLASK_LIMITER_AVAILABLE = False
Limiter = None
get_remote_address = None
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    FLASK_LIMITER_AVAILABLE = True
except ImportError:
    # Fallback si Flask-Limiter n'est pas installé
    class Limiter:
        def __init__(self, *args, **kwargs):
            pass
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    
    def get_remote_address():
        from flask import request
        return request.remote_addr or '127.0.0.1'

# Flask-WTF CSRF (optionnel)
try:
    from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
    CSRF_AVAILABLE = True
except ImportError:
    CSRF_AVAILABLE = False
    class CSRFProtect:
        def __init__(self, *args, **kwargs):
            pass
        def exempt(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

# Flask-Mail sera importé après la création de l'app Flask
FLASK_MAIL_AVAILABLE = False
Mail = None
Message = None
mail = None

# Import des validators
try:
    from utils.validators import (
        validate_email, validate_url, validate_required,
        sanitize_input, validate_date, validate_integer
    )
except ImportError:
    # Fallback si le module n'existe pas encore
    def validate_email(email):
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_url(url):
        if not url:
            return True
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?$'
        return re.match(pattern, url) is not None
    
    def validate_required(data, fields):
        errors = []
        for field in fields:
            if field not in data or not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                errors.append(f"Le champ '{field}' est requis")
        return errors
    
    def sanitize_input(text, max_length=None):
        if not text:
            return ""
        text = text.strip()
        if max_length and len(text) > max_length:
            text = text[:max_length]
        return text

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

app = Flask(__name__)

# Configuration depuis les variables d'environnement
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')

# Configuration CSRF
if CSRF_AVAILABLE:
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 heure
    app.config['WTF_CSRF_SSL_STRICT'] = not app.config['DEBUG']  # SSL strict en production
    csrf = CSRFProtect(app)
else:
    app.config['WTF_CSRF_ENABLED'] = False
    csrf = CSRFProtect(app)  # Utilise le fallback
    print("⚠️ Flask-WTF non installé - CSRF protection désactivée")

# Configuration Flask-Limiter pour rate limiting
if FLASK_LIMITER_AVAILABLE:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",  # En production, utiliser Redis: "redis://localhost:6379"
        strategy="fixed-window"
    )
else:
    limiter = Limiter()  # Utilise le fallback (pas de rate limiting)
    print("⚠️ Flask-Limiter non installé - Rate limiting désactivé")

# Variables personnalisées pour le portfolio
app.config['PORTFOLIO_NAME'] = os.getenv('PORTFOLIO_NAME', 'Pricemou claude')
app.config['PORTFOLIO_TITLE'] = os.getenv('PORTFOLIO_TITLE', 'Développeur Full-Stack & Data Science')
app.config['PORTFOLIO_EMAIL'] = os.getenv('PORTFOLIO_EMAIL', 'contact@example.com')
app.config['PORTFOLIO_DESCRIPTION'] = os.getenv('PORTFOLIO_DESCRIPTION', 'Développeur Full-Stack & Data Science passionné')

# Clé d'administration
app.config['ADMIN_KEY'] = os.getenv('ADMIN_KEY', 'admin-secret-key-change-me')

# Configuration Flask-Mail pour l'envoi d'emails
try:
    from flask_mail import Mail, Message
    FLASK_MAIL_AVAILABLE = True
    
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME', '')
    
    # Initialiser Flask-Mail
    mail = Mail(app)
    print("Flask-Mail configure et pret")
except ImportError:
    FLASK_MAIL_AVAILABLE = False
    Mail = None
    Message = None
    mail = None
    print("Flask-Mail non installe - les emails ne seront pas envoyes. Installez avec: pip install Flask-Mail")

# Import des fonctions de sécurité
try:
    from utils.security import (
        hash_password, check_password,
        sanitize_html, sanitize_text, sanitize_input_advanced
    )
except ImportError:
    # Fallback si le module n'existe pas encore
    import bcrypt
    from html import escape
    
    def hash_password(password):
        """Hash un mot de passe avec bcrypt"""
        if not password:
            raise ValueError("Le mot de passe ne peut pas être vide")
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def check_password(password, hashed):
        """Vérifie si un mot de passe correspond au hash"""
        if not password or not hashed:
            return False
        try:
            # Si le hash est en format SHA256 (ancien système), retourner False
            if len(hashed) == 64 and re.match(r'^[a-f0-9]{64}$', hashed):
                return False
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def sanitize_html(html_content):
        """Nettoie le contenu HTML pour prévenir les attaques XSS"""
        if not html_content:
            return ""
        return escape(html_content)
    
    def sanitize_text(text):
        """Nettoie le texte pour prévenir les attaques XSS"""
        if not text:
            return ""
        return escape(text)
    
    def sanitize_input_advanced(text, max_length=None, allow_html=False):
        """Nettoie une entrée utilisateur de manière avancée"""
        if not text:
            return ""
        text = text.strip()
        if allow_html:
            text = sanitize_html(text)
        else:
            text = sanitize_text(text)
        if max_length and len(text) > max_length:
            text = text[:max_length]
        return text

def init_admin_user(db):
    """Initialise l'utilisateur admin par défaut si nécessaire"""
    if db is None:
        return
    
    try:
        admin_collection = db.admin_users
        default_username = os.getenv('ADMIN_USERNAME', 'admin')
        default_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        # Vérifier si un admin existe déjà
        existing_admin = admin_collection.find_one({"username": default_username})
        
        if not existing_admin:
            admin_collection.insert_one({
                "username": default_username,
                "password": hash_password(default_password),
                "created_at": datetime.now(),
                "last_login": None
            })
            print(f"✅ Utilisateur admin créé - Username: {default_username}, Password: {default_password}")
            print("⚠️  Changez le mot de passe par défaut en production !")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation de l'utilisateur admin: {e}")

# Connexion MongoDB
mongo_client, mongo_db = get_mongo_client()

# Initialiser la base de données si la connexion est réussie
if mongo_db is not None:
    init_database(mongo_db)
    init_admin_user(mongo_db)
    app.config['MONGO_DB'] = mongo_db
else:
    app.config['MONGO_DB'] = None
    print("⚠️  L'application fonctionnera sans base de données MongoDB")

def get_homepage_data(db):
    """Récupère les données de la page d'accueil depuis MongoDB"""
    if db is None:
        return None
    
    try:
        homepage_data = db.homepage.find_one({"type": "header"})
        return homepage_data
    except Exception as e:
        print(f"Erreur lors de la récupération des données homepage: {e}")
        return None

def get_skills_data(db):
    """Récupère les compétences depuis MongoDB"""
    if db is None:
        return []
    
    try:
        skills = list(db.skills.find().sort("order", 1))
        return skills
    except Exception as e:
        print(f"Erreur lors de la récupération des compétences: {e}")
        return []

def get_partners_data(db):
    """Récupère les partenaires depuis MongoDB"""
    if db is None:
        return []
    
    try:
        partners = list(db.partners.find().sort("order", 1))
        return partners
    except Exception as e:
        print(f"Erreur lors de la récupération des partenaires: {e}")
        return []

@app.route('/')
def index():
    current_year = datetime.now().year
    mongo_db = app.config.get('MONGO_DB')
    
    # Tracking analytics
    if mongo_db is not None:
        try:
            from utils.analytics import track_page_view, track_visitor
            track_page_view(
                mongo_db,
                '/',
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                request.headers.get('Referer', '')
            )
            track_visitor(
                mongo_db,
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                '/'
            )
        except Exception as e:
            app.logger.debug(f"Erreur tracking analytics: {e}")
    
    # Récupérer les données dynamiques depuis MongoDB
    homepage_data = get_homepage_data(mongo_db) if mongo_db is not None else None
    skills = get_skills_data(mongo_db) if mongo_db is not None else []
    partners = get_partners_data(mongo_db) if mongo_db is not None else []
    
    # Valeurs par défaut si MongoDB n'est pas disponible
    if not homepage_data:
        homepage_data = {
            "badge": app.config['PORTFOLIO_TITLE'],
            "title_line1": "De l'idée à la donnée.",
            "title_line2": "Du code à l'insight !",
            "description": app.config['PORTFOLIO_DESCRIPTION'],
            "email": app.config['PORTFOLIO_EMAIL'],
            "cta_text": "Discutons !",
            "about_title": "Présentation",
            "about_name": app.config['PORTFOLIO_NAME'],
            "about_subtitle": "Développeur Full-Stack & Data Science passionné par l'innovation et l'excellence technique.",
            "about_description": "Je suis un développeur Full-Stack et Data Scientist avec une passion pour créer des solutions technologiques complètes et performantes."
        }
    
    if not skills:
        skills = [
            {"title": "Full-Stack Development", "icon": "icons/code.svg", "description": "Développement d'applications web complètes, du frontend au backend, avec les dernières technologies.", "projects_count": 15},
            {"title": "Data Science", "icon": "icons/design.svg", "description": "Analyse de données, machine learning et visualisation pour extraire des insights précieux.", "projects_count": 12},
            {"title": "Architecture & DevOps", "icon": "icons/phone.svg", "description": "Conception d'architectures scalables et déploiement avec les meilleures pratiques DevOps.", "projects_count": 8}
        ]
    
    if not partners:
        partners = [
            {"name": "wallety", "image": "images/partners/wallety.png"},
            {"name": "artisty", "image": "images/partners/artisty.png"},
            {"name": "khedma-lik", "image": "images/partners/khedma-lik.png"},
            {"name": "directy", "image": "images/partners/directy.png"},
            {"name": "telefy", "image": "images/partners/telefy.png"}
        ]
    
    return render_template('index.html', 
                         current_year=current_year,
                         homepage_data=homepage_data,
                         skills=skills,
                         partners=partners)

@app.route('/works')
def works():
    """Page des réalisations"""
    current_year = datetime.now().year
    mongo_db = app.config.get('MONGO_DB')
    
    # Tracking analytics
    if mongo_db is not None:
        try:
            from utils.analytics import track_page_view, track_visitor
            track_page_view(
                mongo_db,
                '/works',
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                request.headers.get('Referer', '')
            )
            track_visitor(
                mongo_db,
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                '/works'
            )
        except Exception as e:
            app.logger.debug(f"Erreur tracking analytics: {e}")
    
    # Récupérer les projets depuis MongoDB (si disponible)
    projects = []
    if mongo_db is not None:
        try:
            projects_collection = mongo_db.projects
            # Récupérer uniquement les projets publiés, triés par ordre puis par date
            projects = list(projects_collection.find({"status": "published"}).sort("order", 1).sort("created_at", -1))
            # Convertir ObjectId en string pour le template
            for project in projects:
                if '_id' in project:
                    project['_id'] = str(project['_id'])
                # Ajouter le compteur de vues (par défaut 0)
                if 'views' not in project:
                    project['views'] = 0
        except Exception as e:
            app.logger.error(f"Erreur lors de la récupération des projets: {e}")
    
    return render_template('works.html', 
                         current_year=current_year,
                         projects=projects)

@app.route('/services')
def services():
    """Page des services"""
    current_year = datetime.now().year
    mongo_db = app.config.get('MONGO_DB')
    
    # Tracking analytics
    if mongo_db is not None:
        try:
            from utils.analytics import track_page_view, track_visitor
            track_page_view(
                mongo_db,
                '/services',
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                request.headers.get('Referer', '')
            )
            track_visitor(
                mongo_db,
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                '/services'
            )
        except Exception as e:
            app.logger.debug(f"Erreur tracking analytics: {e}")
    
    # Récupérer les services depuis MongoDB (si disponible)
    services_list = []
    if mongo_db is not None:
        try:
            services_collection = mongo_db.services
            # Récupérer les services triés par ordre puis par date
            services_list = list(services_collection.find().sort("order", 1).sort("created_at", -1))
            # Convertir ObjectId en string pour le template
            for service in services_list:
                if '_id' in service:
                    service['_id'] = str(service['_id'])
        except Exception as e:
            app.logger.error(f"Erreur lors de la récupération des services: {e}")
    
    return render_template('services.html', current_year=current_year, services=services_list)

@app.route('/contact')
def contact():
    """Page de contact"""
    current_year = datetime.now().year
    portfolio_email = app.config.get('PORTFOLIO_EMAIL', 'contact@example.com')
    mongo_db = app.config.get('MONGO_DB')
    
    # Tracking analytics
    if mongo_db is not None:
        try:
            from utils.analytics import track_page_view, track_visitor
            track_page_view(
                mongo_db,
                '/contact',
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                request.headers.get('Referer', '')
            )
            track_visitor(
                mongo_db,
                request.remote_addr,
                request.headers.get('User-Agent', ''),
                '/contact'
            )
        except Exception as e:
            app.logger.debug(f"Erreur tracking analytics: {e}")
    
    return render_template('contact.html', current_year=current_year, portfolio_email=portfolio_email)

@app.route('/api/contact', methods=['POST'])
@app.route('/contact/submit', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting: 5 requêtes par minute pour le formulaire public
@csrf.exempt  # CSRF exempt car formulaire public avec validation serveur
def contact_submit():
    """Reçoit et stocke un message de contact"""
    try:
        # Accepter à la fois JSON et form-data
        if request.is_json:
            data = request.get_json()
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            subject = data.get('subject', '').strip()
            message = data.get('message', '').strip()
        else:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
        
        # Validation des champs requis
        required_fields = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Champs manquants: {", ".join(missing_fields)}'
            }), 400
        
        # Validation de l'email
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Format d\'email invalide'
            }), 400
        
        # Nettoyer et valider les données avec sanitization XSS avancée
        cleaned_data = {
            'name': sanitize_input_advanced(name, max_length=100),
            'email': sanitize_input_advanced(email, max_length=200),
            'subject': sanitize_input_advanced(subject, max_length=200),
            'message': sanitize_input_advanced(message, max_length=2000),
            'created_at': datetime.now(),
            'read': False,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')[:500]
        }
        
        # Stocker dans MongoDB
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is not None:
            try:
                contacts_collection = mongo_db.contacts
                result = contacts_collection.insert_one(cleaned_data)
                contact_id = str(result.inserted_id)
                app.logger.info(f"Nouveau message de contact sauvegarde dans l'espace admin (ID: {contact_id}) - De: {email}")
                
                # Optionnel: Envoyer un email de notification
                send_contact_notification_email(cleaned_data)
                
                response_data = {
                    'success': True,
                    'message': 'Votre message a été envoyé avec succès. Je vous répondrai dans les plus brefs délais.',
                    'contact_id': contact_id
                }
                app.logger.info(f"Contact sauvegarde avec succes dans MongoDB: {email} - ID: {contact_id}")
                response = jsonify(response_data)
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response, 200
            except Exception as e:
                app.logger.error(f"Erreur lors du stockage du contact dans MongoDB: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': 'Erreur lors de l\'enregistrement du message. Veuillez réessayer.'
                }), 500
        else:
            # Mode sans MongoDB - juste logger
            app.logger.warning(f"Message de contact reçu mais MongoDB non disponible - Message NON sauvegardé: {email} - {subject}")
            app.logger.warning("Le message ne sera pas visible dans l'espace admin sans MongoDB")
            response_data = {
                'success': False,
                'error': 'Service temporairement indisponible. Veuillez réessayer plus tard.'
            }
            return jsonify(response_data), 503
            
    except Exception as e:
        app.logger.error(f"Erreur contact_submit: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'envoi du message. Veuillez réessayer.'
        }), 500

def send_contact_notification_email(contact_data):
    """Envoie un email de notification pour un nouveau message de contact"""
    try:
        # Vérifier si Flask-Mail est disponible
        if not FLASK_MAIL_AVAILABLE or mail is None:
            app.logger.debug("Flask-Mail non disponible - notification email ignorée")
            return False
        
        # Vérifier si la configuration email est complète
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = app.config.get('MAIL_PASSWORD')
        
        if not mail_username or not mail_password:
            app.logger.debug("Configuration email non complète - notification email ignorée")
            app.logger.warning("Pour activer les emails, configurez MAIL_USERNAME et MAIL_PASSWORD dans .env")
            app.logger.warning("Pour Gmail, vous DEVEZ utiliser un mot de passe d'application (pas votre mot de passe normal)")
            app.logger.warning("Voir CONFIGURATION_EMAIL.md pour les instructions")
            return False
        
        # Email de destination (peut être configuré dans .env ou utiliser PORTFOLIO_EMAIL)
        recipient_email = os.getenv('NOTIFICATION_EMAIL', 'pricemoufromon97@gmail.com')
        
        # Créer le message email
        subject = f"Nouveau message de contact: {contact_data['subject']}"
        body = f"""Nouveau message reçu depuis le formulaire de contact:

De: {contact_data['name']}
Email: {contact_data['email']}
Sujet: {contact_data['subject']}

Message:
{contact_data['message']}

---
Date: {contact_data['created_at'].strftime('%d/%m/%Y %H:%M:%S')}
IP: {contact_data.get('ip_address', 'N/A')}
"""
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #4DBA87;">Nouveau message de contact</h2>
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>De:</strong> {contact_data['name']}</p>
        <p><strong>Email:</strong> <a href="mailto:{contact_data['email']}">{contact_data['email']}</a></p>
        <p><strong>Sujet:</strong> {contact_data['subject']}</p>
    </div>
    <div style="background: #fff; padding: 15px; border-left: 4px solid #4DBA87; margin: 20px 0;">
        <p><strong>Message:</strong></p>
        <p style="white-space: pre-wrap;">{contact_data['message']}</p>
    </div>
    <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <p>Date: {contact_data['created_at'].strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p>IP: {contact_data.get('ip_address', 'N/A')}</p>
    </div>
</body>
</html>
"""
        
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body,
            html=html_body
        )
        
        # Envoyer l'email
        mail.send(msg)
        app.logger.info(f"Email de notification envoye a {recipient_email} pour le message de {contact_data['email']}")
        return True
        
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email de notification: {e}", exc_info=True)
        return False

def login_required(f):
    """Décorateur pour protéger les routes nécessitant une connexion"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session.get('admin_logged_in'):
            if request.is_json:
                return jsonify({'error': 'Non authentifié. Veuillez vous connecter.'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour protéger les routes admin (compatibilité avec l'ancien système)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier d'abord la session
        if 'admin_logged_in' in session and session.get('admin_logged_in'):
            return f(*args, **kwargs)
        
        # Fallback sur l'ancien système de clé pour compatibilité API
        admin_key = request.headers.get('X-Admin-Key') or request.args.get('admin_key')
        expected_key = app.config.get('ADMIN_KEY', 'admin-secret-key-change-me')
        
        if admin_key and admin_key == expected_key:
            return f(*args, **kwargs)
        
        if request.is_json:
            return jsonify({'error': 'Non authentifié. Veuillez vous connecter.'}), 401
        return redirect(url_for('admin_login'))
    return decorated_function

def json_serial(obj):
    """Sérialise les ObjectId MongoDB en string"""
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion administrateur"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validation des champs
        # Validation des champs
        if not username or not password:
            flash('Veuillez remplir tous les champs', 'error')
            return render_template('admin_login.html')
        
        # Nettoyer et valider les entrées
        username = sanitize_input(username, max_length=50)
        password = password.strip() if password else ''
        
        # Validation basique
        if len(username) < 3:
            flash('Le nom d\'utilisateur doit contenir au moins 3 caractères', 'error')
            return render_template('admin_login.html')
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
            return render_template('admin_login.html')
        
        # Nettoyer et valider les entrées
        username = sanitize_input(username, max_length=50)
        password = password.strip() if password else ''
        
        # Validation basique
        if len(username) < 3:
            flash('Le nom d\'utilisateur doit contenir au moins 3 caractères', 'error')
            return render_template('admin_login.html')
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
            return render_template('admin_login.html')
        
        mongo_db = app.config.get('MONGO_DB')
        
        if mongo_db is None:
            # Mode sans MongoDB - utiliser les variables d'environnement
            expected_username = os.getenv('ADMIN_USERNAME', 'admin')
            expected_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            
            if username == expected_username and password == expected_password:
                session['admin_logged_in'] = True
                session['admin_username'] = username
                return redirect(url_for('admin'))
            else:
                flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
                return render_template('admin_login.html')
        else:
            # Mode avec MongoDB
            try:
                admin_collection = mongo_db.admin_users
                admin_user = admin_collection.find_one({"username": username})
                
                # Vérifier le mot de passe avec bcrypt (ou SHA256 pour migration)
                password_valid = False
                if admin_user:
                    stored_password = admin_user['password']
                    # Essayer bcrypt d'abord
                    password_valid = check_password(password, stored_password)
                    
                    # Si bcrypt échoue et que c'est un hash SHA256, vérifier avec SHA256
                    # puis migrer vers bcrypt
                    if not password_valid and len(stored_password) == 64:
                        import hashlib
                        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
                        if sha256_hash == stored_password:
                            password_valid = True
                            # Migrer vers bcrypt
                            admin_collection.update_one(
                                {"_id": admin_user['_id']},
                                {"$set": {"password": hash_password(password)}}
                            )
                
                if admin_user and password_valid:
                    # Enregistrer la connexion dans l'historique
                    login_history_collection = mongo_db.login_history
                    login_history_collection.insert_one({
                        "admin_id": str(admin_user['_id']),
                        "username": username,
                        "ip_address": request.remote_addr,
                        "user_agent": request.headers.get('User-Agent', '')[:500],
                        "login_time": datetime.now(),
                        "success": True
                    })
                    
                    # Mettre à jour la dernière connexion
                    admin_collection.update_one(
                        {"username": username},
                        {"$set": {"last_login": datetime.now()}}
                    )
                    session['admin_logged_in'] = True
                    session['admin_username'] = username
                    session['admin_id'] = str(admin_user['_id'])
                    return redirect(url_for('admin'))
                else:
                    flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
                    return render_template('admin_login.html')
            except Exception as e:
                app.logger.error(f"Erreur lors de la connexion: {e}")
                flash('Erreur lors de la connexion. Veuillez réessayer.', 'error')
                return render_template('admin_login.html')
    
    # Si déjà connecté, rediriger vers admin
    if 'admin_logged_in' in session and session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Déconnexion administrateur"""
    session.clear()
    flash('Vous avez été déconnecté avec succès', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin():
    """Page d'administration"""
    return render_template('admin.html', admin_username=session.get('admin_username', 'Admin'))

# ========== API Routes pour Homepage ==========
@app.route('/api/homepage', methods=['GET'])
def get_homepage_api():
    """Récupère les données de la page d'accueil"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            # Retourner des données par défaut si MongoDB n'est pas disponible
            return jsonify({
                "badge": app.config['PORTFOLIO_TITLE'],
                "title_line1": "De l'idée à la donnée.",
                "title_line2": "Du code à l'insight !",
                "description": app.config['PORTFOLIO_DESCRIPTION'],
                "email": app.config['PORTFOLIO_EMAIL'],
                "cta_text": "Discutons !",
                "about_title": "Présentation",
                "about_name": app.config['PORTFOLIO_NAME'],
                "about_subtitle": "Développeur Full-Stack & Data Science passionné par l'innovation et l'excellence technique.",
                "about_description": "Je suis un développeur Full-Stack et Data Scientist avec une passion pour créer des solutions technologiques complètes et performantes."
            })
        
        data = get_homepage_data(mongo_db)
        if data and '_id' in data:
            data['_id'] = str(data['_id'])
        return jsonify(data or {})
    except Exception as e:
        app.logger.error(f"Erreur get_homepage_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/homepage', methods=['PUT'])
@admin_required
@limiter.limit("10 per minute")  # Rate limiting: 10 requêtes par minute
@csrf.exempt  # CSRF exempt car API avec authentification admin
def update_homepage_api():
    """Met à jour les données de la page d'accueil"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Validation des champs
        max_lengths = {
            'badge': 100,
            'title_line1': 200,
            'title_line2': 200,
            'description': 500,
            'email': 100,
            'cta_text': 50,
            'about_title': 100,
            'about_name': 100,
            'about_subtitle': 300,
            'about_description': 1000
        }
        
        # Nettoyer et valider les données
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_data[key] = sanitize_input(value, max_lengths.get(key))
                if max_lengths.get(key) and len(cleaned_data[key]) > max_lengths[key]:
                    return jsonify({'error': f'Le champ {key} dépasse la longueur maximale ({max_lengths[key]} caractères)'}), 400
            else:
                cleaned_data[key] = value
        
        # Valider l'email si présent
        if 'email' in cleaned_data and cleaned_data['email']:
            if not validate_email(cleaned_data['email']):
                return jsonify({'error': 'Format d\'email invalide'}), 400
        
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        # Ajouter le type pour la recherche
        cleaned_data['type'] = 'header'
        
        result = mongo_db.homepage.update_one(
            {"type": "header"},
            {"$set": cleaned_data},
            upsert=True
        )
        return jsonify({'success': True, 'message': 'Données mises à jour'})
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Erreur update_homepage_api: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Skills ==========
@app.route('/api/skills', methods=['GET'])
def get_skills_api():
    """Récupère toutes les compétences"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            # Retourner un tableau vide si MongoDB n'est pas disponible
            return jsonify([])
        
        skills = get_skills_data(mongo_db)
        if not isinstance(skills, list):
            skills = []
        for skill in skills:
            if '_id' in skill:
                skill['_id'] = str(skill['_id'])
        return jsonify(skills)
    except Exception as e:
        app.logger.error(f"Erreur get_skills_api: {e}")
        return jsonify([])  # Retourner un tableau vide en cas d'erreur

@app.route('/api/skills', methods=['POST'])
@admin_required
def create_skill_api():
    """Crée une nouvelle compétence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Validation des champs requis
        required_fields = ['title', 'description']
        validation_errors = validate_required(data, required_fields)
        if validation_errors:
            return jsonify({'error': '; '.join(validation_errors)}), 400
        
        # Nettoyer et valider les données
        cleaned_data = {
            'title': sanitize_input(data.get('title', ''), max_length=100),
            'description': sanitize_input(data.get('description', ''), max_length=500),
            'icon': sanitize_input(data.get('icon', ''), max_length=200),
            'projects_count': int(data.get('projects_count', 0)) if str(data.get('projects_count', 0)).isdigit() else 0,
            'order': int(data.get('order', 0)) if str(data.get('order', 0)).isdigit() else 0
        }
        
        # Valider l'URL de l'icône si présente
        if cleaned_data['icon'] and not validate_url(cleaned_data['icon']) and not cleaned_data['icon'].startswith('icons/'):
            return jsonify({'error': 'Format d\'URL d\'icône invalide'}), 400
        
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        # Ajouter la date de création
        cleaned_data['created_at'] = datetime.now()
        
        result = mongo_db.skills.insert_one(cleaned_data)
        return jsonify({'success': True, 'id': str(result.inserted_id), 'message': 'Compétence créée'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_skill_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills/<skill_id>', methods=['PUT'])
@admin_required
def update_skill_api(skill_id):
    """Met à jour une compétence"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'MongoDB non disponible'}), 500
    
    try:
        data = request.get_json()
        result = mongo_db.skills.update_one(
            {"_id": ObjectId(skill_id)},
            {"$set": data}
        )
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Compétence mise à jour'})
        return jsonify({'error': 'Compétence non trouvée'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills/<skill_id>', methods=['DELETE'])
@admin_required
def delete_skill_api(skill_id):
    """Supprime une compétence"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'MongoDB non disponible'}), 500
    
    try:
        result = mongo_db.skills.delete_one({"_id": ObjectId(skill_id)})
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Compétence supprimée'})
        return jsonify({'error': 'Compétence non trouvée'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Partners ==========
@app.route('/api/partners', methods=['GET'])
def get_partners_api():
    """Récupère tous les partenaires"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            # Retourner un tableau vide si MongoDB n'est pas disponible
            return jsonify([])
        
        partners = get_partners_data(mongo_db)
        if not isinstance(partners, list):
            partners = []
        for partner in partners:
            if '_id' in partner:
                partner['_id'] = str(partner['_id'])
        return jsonify(partners)
    except Exception as e:
        app.logger.error(f"Erreur get_partners_api: {e}")
        return jsonify([])  # Retourner un tableau vide en cas d'erreur

@app.route('/api/partners', methods=['POST'])
@admin_required
def create_partner_api():
    """Crée un nouveau partenaire"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Validation des champs requis
        required_fields = ['name', 'logo']
        validation_errors = validate_required(data, required_fields)
        if validation_errors:
            return jsonify({'error': '; '.join(validation_errors)}), 400
        
        # Nettoyer et valider les données
        cleaned_data = {
            'name': sanitize_input(data.get('name', ''), max_length=100),
            'logo': sanitize_input(data.get('logo', ''), max_length=500),
            'website': sanitize_input(data.get('website', ''), max_length=500),
            'order': int(data.get('order', 0)) if str(data.get('order', 0)).isdigit() else 0
        }
        
        # Valider les URLs
        if cleaned_data['website'] and not validate_url(cleaned_data['website']):
            return jsonify({'error': 'Format d\'URL de site web invalide'}), 400
        
        if cleaned_data['logo'] and not validate_url(cleaned_data['logo']) and not cleaned_data['logo'].startswith('images/'):
            return jsonify({'error': 'Format d\'URL de logo invalide'}), 400
        
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        # Ajouter la date de création
        cleaned_data['created_at'] = datetime.now()
        
        result = mongo_db.partners.insert_one(cleaned_data)
        return jsonify({'success': True, 'id': str(result.inserted_id), 'message': 'Partenaire créé'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_partner_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/partners/<partner_id>', methods=['PUT'])
@admin_required
def update_partner_api(partner_id):
    """Met à jour un partenaire"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'MongoDB non disponible'}), 500
    
    try:
        data = request.get_json()
        result = mongo_db.partners.update_one(
            {"_id": ObjectId(partner_id)},
            {"$set": data}
        )
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Partenaire mis à jour'})
        return jsonify({'error': 'Partenaire non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/partners/<partner_id>', methods=['DELETE'])
@admin_required
def delete_partner_api(partner_id):
    """Supprime un partenaire"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'MongoDB non disponible'}), 500
    
    try:
        result = mongo_db.partners.delete_one({"_id": ObjectId(partner_id)})
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Partenaire supprimé'})
        return jsonify({'error': 'Partenaire non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Projects ==========
@app.route('/api/projects', methods=['GET'])
def get_projects_api():
    """Récupère la liste des projets"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify([])
        
        projects = list(mongo_db.projects.find().sort("created_at", -1))
        # Convertir ObjectId en string
        for project in projects:
            if '_id' in project:
                project['_id'] = str(project['_id'])
        
        return jsonify(projects)
    except Exception as e:
        app.logger.error(f"Erreur get_projects_api: {e}")
        return jsonify([])

@app.route('/api/projects', methods=['POST'])
@admin_required
@limiter.limit("20 per minute")  # Rate limiting: 20 requêtes par minute
@csrf.exempt
def create_project_api():
    """Crée un nouveau projet"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Validation des champs requis
        required_fields = ['title', 'description', 'technologies']
        validation_errors = validate_required(data, required_fields)
        if validation_errors:
            return jsonify({'error': '; '.join(validation_errors)}), 400
        
        # Nettoyer et valider les données
        cleaned_data = {
            'title': sanitize_input(data.get('title', ''), max_length=200),
            'description': sanitize_input(data.get('description', ''), max_length=1000),
            'technologies': sanitize_input(data.get('technologies', ''), max_length=200),
            'image': sanitize_input(data.get('image', ''), max_length=500),
            'link': sanitize_input(data.get('link', ''), max_length=500),
            'github_link': sanitize_input(data.get('github_link', ''), max_length=500),
            'status': sanitize_input(data.get('status', 'published'), max_length=50),
            'order': int(data.get('order', 0)) if str(data.get('order', 0)).isdigit() else 0,
            'featured': bool(data.get('featured', False)),
            'views': 0  # Initialiser le compteur de vues à 0
        }
        
        # Valider les URLs
        if cleaned_data['link'] and not validate_url(cleaned_data['link']):
            return jsonify({'error': 'Format d\'URL de lien invalide'}), 400
        
        if cleaned_data['github_link'] and not validate_url(cleaned_data['github_link']):
            return jsonify({'error': 'Format d\'URL GitHub invalide'}), 400
        
        if cleaned_data['image'] and not validate_url(cleaned_data['image']) and not cleaned_data['image'].startswith('images/'):
            return jsonify({'error': 'Format d\'URL d\'image invalide'}), 400
        
        # Valider le statut
        valid_statuses = ['draft', 'published', 'archived']
        if cleaned_data['status'] not in valid_statuses:
            cleaned_data['status'] = 'published'
        
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        # Ajouter la date de création
        cleaned_data['created_at'] = datetime.now()
        cleaned_data['updated_at'] = datetime.now()
        
        result = mongo_db.projects.insert_one(cleaned_data)
        return jsonify({'success': True, 'id': str(result.inserted_id), 'message': 'Projet créé'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_project_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
@admin_required
def update_project_api(project_id):
    """Met à jour un projet"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'Base de données non disponible'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Nettoyer et valider les données (même logique que create)
        cleaned_data = {}
        max_lengths = {
            'title': 200,
            'description': 1000,
            'technologies': 200,
            'image': 500,
            'link': 500,
            'github_link': 500,
            'status': 50
        }
        
        for key, value in data.items():
            if key in max_lengths:
                if isinstance(value, str):
                    cleaned_data[key] = sanitize_input(value, max_length=max_lengths[key])
                else:
                    cleaned_data[key] = value
            elif key in ['order', 'featured']:
                if key == 'order':
                    cleaned_data[key] = int(value) if str(value).isdigit() else 0
                else:
                    cleaned_data[key] = bool(value)
        
        # Valider les URLs
        if 'link' in cleaned_data and cleaned_data['link'] and not validate_url(cleaned_data['link']):
            return jsonify({'error': 'Format d\'URL de lien invalide'}), 400
        
        if 'github_link' in cleaned_data and cleaned_data['github_link'] and not validate_url(cleaned_data['github_link']):
            return jsonify({'error': 'Format d\'URL GitHub invalide'}), 400
        
        if 'image' in cleaned_data and cleaned_data['image'] and not validate_url(cleaned_data['image']) and not cleaned_data['image'].startswith('images/'):
            return jsonify({'error': 'Format d\'URL d\'image invalide'}), 400
        
        # Valider le statut
        if 'status' in cleaned_data:
            valid_statuses = ['draft', 'published', 'archived']
            if cleaned_data['status'] not in valid_statuses:
                cleaned_data['status'] = 'published'
        
        # Ajouter la date de mise à jour
        cleaned_data['updated_at'] = datetime.now()
        
        result = mongo_db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": cleaned_data}
        )
        if result.modified_count > 0 or result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Projet mis à jour'})
        return jsonify({'error': 'Projet non trouvé'}), 404
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur update_project_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
@admin_required
@limiter.limit("10 per minute")
@csrf.exempt
def delete_project_api(project_id):
    """Supprime un projet"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'Base de données non disponible'}), 503
    
    try:
        result = mongo_db.projects.delete_one({"_id": ObjectId(project_id)})
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Projet supprimé'})
        return jsonify({'error': 'Projet non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur delete_project_api: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Services ==========
@app.route('/api/services', methods=['GET'])
def get_services_api():
    """Récupère la liste des services"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify([])
        
        services = list(mongo_db.services.find().sort("order", 1).sort("created_at", -1))
        # Convertir ObjectId en string
        for service in services:
            if '_id' in service:
                service['_id'] = str(service['_id'])
        
        return jsonify(services)
    except Exception as e:
        app.logger.error(f"Erreur get_services_api: {e}")
        return jsonify([])

@app.route('/api/services', methods=['POST'])
@admin_required
@limiter.limit("20 per minute")
@csrf.exempt
def create_service_api():
    """Crée un nouveau service"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Validation des champs requis
        required_fields = ['title', 'description']
        validation_errors = validate_required(data, required_fields)
        if validation_errors:
            return jsonify({'error': '; '.join(validation_errors)}), 400
        
        # Nettoyer et valider les données
        cleaned_data = {
            'title': sanitize_input(data.get('title', ''), max_length=200),
            'description': sanitize_input(data.get('description', ''), max_length=1000),
            'icon': sanitize_input(data.get('icon', ''), max_length=500),
            'order': int(data.get('order', 0)) if str(data.get('order', 0)).isdigit() else 0
        }
        
        # Valider l'URL de l'icône si présente
        if cleaned_data['icon'] and not validate_url(cleaned_data['icon']) and not cleaned_data['icon'].startswith('icons/'):
            return jsonify({'error': 'Format d\'URL d\'icône invalide'}), 400
        
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        # Ajouter la date de création
        cleaned_data['created_at'] = datetime.now()
        cleaned_data['updated_at'] = datetime.now()
        
        result = mongo_db.services.insert_one(cleaned_data)
        return jsonify({'success': True, 'id': str(result.inserted_id), 'message': 'Service créé'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_service_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/services/<service_id>', methods=['PUT'])
@admin_required
@limiter.limit("20 per minute")
@csrf.exempt
def update_service_api(service_id):
    """Met à jour un service"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'Base de données non disponible'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Nettoyer et valider les données
        cleaned_data = {}
        max_lengths = {
            'title': 200,
            'description': 1000,
            'icon': 500
        }
        
        for key, value in data.items():
            if key in max_lengths:
                if isinstance(value, str):
                    cleaned_data[key] = sanitize_input(value, max_length=max_lengths[key])
                else:
                    cleaned_data[key] = value
            elif key == 'order':
                cleaned_data[key] = int(value) if str(value).isdigit() else 0
        
        # Valider l'URL de l'icône si présente
        if 'icon' in cleaned_data and cleaned_data['icon'] and not validate_url(cleaned_data['icon']) and not cleaned_data['icon'].startswith('icons/'):
            return jsonify({'error': 'Format d\'URL d\'icône invalide'}), 400
        
        # Ajouter la date de mise à jour
        cleaned_data['updated_at'] = datetime.now()
        
        result = mongo_db.services.update_one(
            {"_id": ObjectId(service_id)},
            {"$set": cleaned_data}
        )
        if result.modified_count > 0 or result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Service mis à jour'})
        return jsonify({'error': 'Service non trouvé'}), 404
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur update_service_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/services/<service_id>', methods=['DELETE'])
@admin_required
@limiter.limit("10 per minute")
@csrf.exempt
def delete_service_api(service_id):
    """Supprime un service"""
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is None:
        return jsonify({'error': 'Base de données non disponible'}), 503
    
    try:
        result = mongo_db.services.delete_one({"_id": ObjectId(service_id)})
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Service supprimé'})
        return jsonify({'error': 'Service non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur delete_service_api: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Contacts ==========
@app.route('/api/contacts', methods=['GET'])
@admin_required
def get_contacts_api():
    """Récupère la liste des messages de contact"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify([])
        
        # Récupérer les paramètres de filtrage
        read_filter = request.args.get('read')
        limit = request.args.get('limit', type=int)
        
        query = {}
        if read_filter is not None:
            query['read'] = read_filter.lower() == 'true'
        
        # Récupérer les contacts
        contacts = list(mongo_db.contacts.find(query).sort("created_at", -1))
        
        # Limiter le nombre de résultats si spécifié
        if limit:
            contacts = contacts[:limit]
        
        # Convertir ObjectId en string
        for contact in contacts:
            if '_id' in contact:
                contact['_id'] = str(contact['_id'])
            if 'created_at' in contact and isinstance(contact['created_at'], datetime):
                contact['created_at'] = contact['created_at'].isoformat()
        
        return jsonify(contacts)
    except Exception as e:
        app.logger.error(f"Erreur get_contacts_api: {e}")
        return jsonify([])

@app.route('/api/contacts/<contact_id>/read', methods=['PUT'])
@admin_required
def mark_contact_read_api(contact_id):
    """Marque un message comme lu ou non lu"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        data = request.get_json()
        read_status = data.get('read', True)
        
        result = mongo_db.contacts.update_one(
            {"_id": ObjectId(contact_id)},
            {"$set": {"read": read_status}}
        )
        
        if result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Statut mis à jour'})
        return jsonify({'error': 'Message non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur mark_contact_read_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/<contact_id>', methods=['DELETE'])
@admin_required
def delete_contact_api(contact_id):
    """Supprime un message de contact"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        result = mongo_db.contacts.delete_one({"_id": ObjectId(contact_id)})
        
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Message supprimé'})
        return jsonify({'error': 'Message non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur delete_contact_api: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Gestion du Profil Admin ==========
@app.route('/api/admin/profile', methods=['GET'])
@login_required
def get_admin_profile():
    """Récupère les informations du profil administrateur"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        admin_id = session.get('admin_id')
        admin_username = session.get('admin_username')
        
        if mongo_db is None or not admin_id:
            # Mode sans MongoDB - retourner les infos de session
            return jsonify({
                'username': admin_username,
                'email': os.getenv('ADMIN_EMAIL', ''),
                'created_at': None,
                'last_login': None
            })
        
        admin_collection = mongo_db.admin_users
        admin_user = admin_collection.find_one({"_id": ObjectId(admin_id)})
        
        if not admin_user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        profile_data = {
            'username': admin_user.get('username', ''),
            'email': admin_user.get('email', ''),
            'full_name': admin_user.get('full_name', ''),
            'created_at': admin_user.get('created_at').isoformat() if admin_user.get('created_at') else None,
            'last_login': admin_user.get('last_login').isoformat() if admin_user.get('last_login') else None
        }
        
        return jsonify(profile_data)
    except Exception as e:
        app.logger.error(f"Erreur get_admin_profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/profile', methods=['PUT'])
@login_required
@limiter.limit("10 per minute")
@csrf.exempt
def update_admin_profile():
    """Met à jour les informations du profil administrateur"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        admin_id = session.get('admin_id')
        
        if mongo_db is None:
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        if not admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        admin_collection = mongo_db.admin_users
        update_data = {}
        
        # Mettre à jour l'email si fourni
        if 'email' in data:
            email = sanitize_input(data['email'], max_length=200)
            if email and validate_email(email):
                update_data['email'] = email
            elif email:
                return jsonify({'error': 'Format d\'email invalide'}), 400
        
        # Mettre à jour le nom complet si fourni
        if 'full_name' in data:
            update_data['full_name'] = sanitize_input(data['full_name'], max_length=100)
        
        if not update_data:
            return jsonify({'error': 'Aucune donnée à mettre à jour'}), 400
        
        update_data['updated_at'] = datetime.now()
        
        result = admin_collection.update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": update_data}
        )
        
        if result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Profil mis à jour avec succès'})
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur update_admin_profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/change-password', methods=['POST'])
@login_required
@limiter.limit("5 per minute")  # Limite stricte pour changement de mot de passe
@csrf.exempt
def change_admin_password():
    """Change le mot de passe de l'administrateur"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        admin_id = session.get('admin_id')
        admin_username = session.get('admin_username')
        
        if not admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': 'Tous les champs sont requis'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Le nouveau mot de passe doit contenir au moins 6 caractères'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Les mots de passe ne correspondent pas'}), 400
        
        if new_password == current_password:
            return jsonify({'error': 'Le nouveau mot de passe doit être différent de l\'ancien'}), 400
        
        # Vérifier l'ancien mot de passe
        if mongo_db is None:
            # Mode sans MongoDB - utiliser les variables d'environnement
            expected_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            if current_password != expected_password:
                return jsonify({'error': 'Mot de passe actuel incorrect'}), 400
            
            # En production, il faudrait mettre à jour la variable d'environnement
            return jsonify({'error': 'Changement de mot de passe non disponible sans MongoDB'}), 503
        else:
            admin_collection = mongo_db.admin_users
            admin_user = admin_collection.find_one({"_id": ObjectId(admin_id)})
            
            if not admin_user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            # Vérifier le mot de passe actuel
            if admin_user['password'] != hash_password(current_password):
                return jsonify({'error': 'Mot de passe actuel incorrect'}), 400
            
            # Mettre à jour le mot de passe
            admin_collection.update_one(
                {"_id": ObjectId(admin_id)},
                {"$set": {
                    "password": hash_password(new_password),
                    "password_changed_at": datetime.now()
                }}
            )
            
            app.logger.info(f"Mot de passe change pour l'utilisateur {admin_username}")
            return jsonify({'success': True, 'message': 'Mot de passe changé avec succès'})
    except Exception as e:
        app.logger.error(f"Erreur change_admin_password: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/login-history', methods=['GET'])
@login_required
def get_login_history():
    """Récupère l'historique des connexions"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        admin_id = session.get('admin_id')
        
        if not admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        if mongo_db is None:
            return jsonify({'history': [], 'total': 0, 'limit': 50, 'skip': 0})
        
        # Récupérer les paramètres de pagination
        limit = request.args.get('limit', type=int) or 50
        skip = request.args.get('skip', type=int) or 0
        
        login_history_collection = mongo_db.login_history
        history = list(
            login_history_collection.find({"admin_id": admin_id})
            .sort("login_time", -1)
            .limit(limit)
            .skip(skip)
        )
        
        # Convertir ObjectId et datetime
        for entry in history:
            if '_id' in entry:
                entry['_id'] = str(entry['_id'])
            if 'login_time' in entry and isinstance(entry['login_time'], datetime):
                entry['login_time'] = entry['login_time'].isoformat()
        
        # Compter le total
        total = login_history_collection.count_documents({"admin_id": admin_id})
        
        return jsonify({
            'history': history,
            'total': total,
            'limit': limit,
            'skip': skip
        })
    except Exception as e:
        app.logger.error(f"Erreur get_login_history: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Analytics ==========
@app.route('/api/analytics/stats', methods=['GET'])
@admin_required
@limiter.limit("30 per minute")
@csrf.exempt
def get_analytics_stats():
    """Récupère les statistiques globales"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        
        if mongo_db is None:
            return jsonify({
                'total_views': 0,
                'total_visitors': 0,
                'total_projects': 0,
                'total_services': 0,
                'total_contacts': 0,
                'engagement_rate': 0,
                'views_by_day': [],
                'visitors_by_day': [],
                'top_projects': []
            })
        
        from utils.analytics import get_statistics
        
        days = request.args.get('days', type=int) or 30
        stats = get_statistics(mongo_db, days)
        
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Erreur get_analytics_stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/project/<project_id>', methods=['GET'])
@admin_required
@limiter.limit("30 per minute")
@csrf.exempt
def get_project_analytics(project_id):
    """Récupère les statistiques d'un projet spécifique"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        
        if mongo_db is None:
            return jsonify({'views': 0, 'views_by_day': []})
        
        from utils.analytics import get_project_statistics
        
        stats = get_project_statistics(mongo_db, project_id)
        
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Erreur get_project_analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/track-project-view', methods=['POST'])
@limiter.limit("30 per minute")  # Rate limiting pour tracking public
@csrf.exempt
def track_project_view_api():
    """Endpoint pour tracker une vue de projet (public, pas d'authentification requise)"""
    try:
        mongo_db = app.config.get('MONGO_DB')
        
        if mongo_db is None:
            return jsonify({'success': True})
        
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'project_id requis'}), 400
        
        from utils.analytics import track_project_view
        
        track_project_view(
            mongo_db,
            project_id,
            request.remote_addr,
            request.headers.get('User-Agent', '')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Erreur track_project_view_api: {e}")
        return jsonify({'error': str(e)}), 500

# Les fonctions de validation sont importées depuis utils.validators

# ========== Handlers d'erreur ==========
@app.errorhandler(404)
def not_found_error(error):
    """Gère les erreurs 404"""
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'error': 'Ressource non trouvée'}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Gère les erreurs 500"""
    app.logger.error(f'Erreur serveur: {error}', exc_info=True)
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    return render_template('errors/500.html'), 500

@app.errorhandler(400)
def bad_request_error(error):
    """Gère les erreurs 400 (Bad Request)"""
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'error': 'Requête invalide'}), 400
    flash('Requête invalide', 'error')
    return redirect(url_for('index')), 400

@app.errorhandler(401)
def unauthorized_error(error):
    """Gère les erreurs 401 (Unauthorized)"""
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'error': 'Non autorisé'}), 401
    flash('Vous devez être connecté pour accéder à cette page', 'error')
    return redirect(url_for('admin_login')), 401

@app.errorhandler(403)
def forbidden_error(error):
    """Gère les erreurs 403 (Forbidden)"""
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'error': 'Accès interdit'}), 403
    flash('Accès interdit', 'error')
    return redirect(url_for('index')), 403

if __name__ == '__main__':
    import socket
    
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = app.config['DEBUG']
    
    # Vérifier si le port est disponible
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return True
            except OSError:
                return False
    
    # Si le port n'est pas disponible, essayer les ports suivants
    original_port = port
    if not is_port_available(port):
        print(f"Le port {port} est deja utilise. Recherche d'un port disponible...")
        for test_port in range(port + 1, port + 10):
            if is_port_available(test_port):
                port = test_port
                print(f"Utilisation du port {port} a la place")
                break
        else:
            print(f"Aucun port disponible entre {original_port} et {original_port + 10}")
            print("Arretez l'autre application qui utilise le port ou changez le port dans .env")
            sys.exit(1)
    
    app.run(host=host, port=port, debug=debug)

