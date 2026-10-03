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
from database import get_db, init_database, row_to_dict, rows_to_list
from functools import wraps
# ObjectId n'est plus nécessaire avec SQLite
import json
import hashlib
import re
from werkzeug.exceptions import BadRequest, InternalServerError

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

# Variables personnalisées pour le portfolio
app.config['PORTFOLIO_NAME'] = os.getenv('PORTFOLIO_NAME', 'Claude Pricemou')
app.config['PORTFOLIO_TITLE'] = os.getenv('PORTFOLIO_TITLE', 'Développeur Full Stack & Science des données')
app.config['PORTFOLIO_EMAIL'] = os.getenv('PORTFOLIO_EMAIL', 'pricemoufromon97@gmail.com')
app.config['PORTFOLIO_DESCRIPTION'] = os.getenv('PORTFOLIO_DESCRIPTION', 'Développeur Full Stack freelance à Trois-Rivières')
app.config['SITE_URL'] = os.getenv('SITE_URL', 'https://claude225.pythonanywhere.com')

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

# Fonctions utilitaires pour l'authentification
# Utiliser bcrypt pour le hashage sécurisé des mots de passe
try:
    from utils.security import hash_password, check_password
except ImportError:
    # Fallback si le module n'existe pas
    import bcrypt
    def hash_password(password):
        """Hash un mot de passe avec bcrypt"""
        if not password:
            raise ValueError("Le mot de passe ne peut pas être vide")
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def check_password(password, hashed):
        """Vérifie un mot de passe avec bcrypt"""
        if not password or not hashed:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

def init_admin_user():
    """Initialise l'utilisateur admin par défaut si nécessaire"""
    try:
        with get_db() as conn:
            if conn is None:
                return
            
            cursor = conn.cursor()
            default_username = os.getenv('ADMIN_USERNAME', 'admin')
            default_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            
            # Vérifier si un admin existe déjà
            cursor.execute('SELECT * FROM admin_users WHERE username = ?', (default_username,))
            existing_admin = cursor.fetchone()
            
            if not existing_admin:
                cursor.execute('''
                    INSERT INTO admin_users (username, password, created_at)
                    VALUES (?, ?, ?)
                ''', (default_username, hash_password(default_password), datetime.now()))
                conn.commit()
                print(f"✅ Utilisateur admin créé - Username: {default_username}, Password: {default_password}")
                print("⚠️  Changez le mot de passe par défaut en production !")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation de l'utilisateur admin: {e}")

# Initialiser la base de données SQLite d'abord
if init_database():
    print("✅ Base de données SQLite initialisée")
    # Ensuite initialiser l'utilisateur admin
    init_admin_user()
else:
    print("⚠️  Erreur lors de l'initialisation de la base de données SQLite")

from utils.i18n import get_lang, translate
from utils.security import generate_csrf_token

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(get_remote_address, app=app, default_limits=[])
except Exception:
    limiter = None

def _limit_contact(fn):
    if limiter is None:
        return fn
    return limiter.limit("5 per hour")(fn)

@app.context_processor
def inject_i18n():
    lang = get_lang(request)
    return {
        'lang': lang,
        't': lambda key: translate(key, lang),
    }

@app.route('/lang/<lang>')
def set_language(lang):
    if lang not in ('fr', 'en'):
        lang = 'fr'
    dest = request.args.get('next') or request.referrer or url_for('index')
    resp = redirect(dest)
    resp.set_cookie('lang', lang, max_age=60 * 60 * 24 * 365, samesite='Lax')
    return resp

def get_key_stats():
    years = max(1, datetime.now().year - 2019)
    stats = {'projects': 0, 'years': years, 'services': 0}
    try:
        with get_db() as conn:
            if conn is None:
                return stats
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'published'")
            stats['projects'] = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM services')
            stats['services'] = cursor.fetchone()[0]
    except Exception as e:
        app.logger.error(f"Erreur key_stats: {e}")
    return stats

def ensure_db_connection():
    """
    Retourne une connexion à la base de données SQLite
    """
    try:
        return get_db()
    except Exception as e:
        app.logger.error(f"❌ Erreur lors de la connexion SQLite: {e}")
        return None

def get_homepage_data():
    """Récupère les données de la page d'accueil depuis SQLite"""
    try:
        with get_db() as conn:
            if conn is None:
                return None
            
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM homepage WHERE type = ? LIMIT 1', ('header',))
            row = cursor.fetchone()
            return row_to_dict(row)
    except Exception as e:
        print(f"Erreur lors de la récupération des données homepage: {e}")
        return None

def get_skills_data():
    """Récupère les compétences depuis SQLite"""
    try:
        with get_db() as conn:
            if conn is None:
                return []
            
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM skills ORDER BY order_index ASC')
            rows = cursor.fetchall()
            return rows_to_list(rows)
    except Exception as e:
        print(f"Erreur lors de la récupération des compétences: {e}")
        return []

def get_partners_data():
    """Récupère les partenaires depuis SQLite"""
    try:
        with get_db() as conn:
            if conn is None:
                return []
            
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM partners ORDER BY order_index ASC')
            rows = cursor.fetchall()
            return rows_to_list(rows)
    except Exception as e:
        print(f"Erreur lors de la récupération des partenaires: {e}")
        return []

@app.route('/')
def index():
    current_year = datetime.now().year
    
    # Récupérer les données dynamiques depuis SQLite
    homepage_data = get_homepage_data()
    skills = get_skills_data()
    partners = get_partners_data()
    
    # Valeurs par défaut si la base de données n'est pas disponible
    if not homepage_data:
        homepage_data = {
            "badge": "Disponible en freelance · Trois-Rivières (Québec)",
            "title_line1": "Du besoin métier",
            "title_line2": "au produit et à la donnée.",
            "description": app.config['PORTFOLIO_DESCRIPTION'],
            "email": app.config['PORTFOLIO_EMAIL'],
            "cta_text": "Discutons d'un mandat",
            "about_title": "Présentation",
            "about_name": app.config['PORTFOLIO_NAME'],
            "about_subtitle": app.config['PORTFOLIO_TITLE'],
            "about_description": "Baccalauréat en informatique (science des données) à l'UQTR.",
        }
    
    return render_template('index.html', 
                         current_year=current_year,
                         homepage_data=homepage_data,
                         skills=skills,
                         partners=partners,
                         key_stats=get_key_stats())

@app.route('/works')
def works():
    """Page des réalisations"""
    current_year = datetime.now().year
    
    # Récupérer les projets depuis SQLite
    projects = []
    try:
        with get_db() as conn:
            if conn is None:
                app.logger.error("Connexion DB impossible dans /works")
                projects = []
            else:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM projects 
                    WHERE status = ? 
                    ORDER BY order_index ASC, created_at DESC
                ''', ('published',))
                rows = cursor.fetchall()
                projects = rows_to_list(rows)
                app.logger.info(f"Récupération de {len(projects)} projets depuis la DB")
                
                # Convertir id en string pour compatibilité et nettoyer les données
                for project in projects:
                    project['_id'] = str(project['id'])
                    project['featured'] = bool(project.get('featured', 0))
                    project['category'] = project.get('category') or 'pro'
                    if project.get('additional_images') is None:
                        project['additional_images'] = ''
                    raw_results = project.get('results') or '[]'
                    try:
                        project['results_list'] = json.loads(raw_results) if isinstance(raw_results, str) else raw_results
                    except (TypeError, ValueError):
                        project['results_list'] = [raw_results] if raw_results else []
    except Exception as e:
        app.logger.error(f"Erreur lors de la récupération des projets: {e}")
        import traceback
        app.logger.error(traceback.format_exc())

    category_order = {'pro': 0, 'data': 1, 'academic': 2}
    projects.sort(key=lambda p: (category_order.get(p.get('category'), 9), p.get('order_index') or 0))
    active_cat = request.args.get('cat', 'all')
    return render_template('works.html', 
                         current_year=current_year,
                         projects=projects,
                         homepage_data=get_homepage_data(),
                         active_cat=active_cat)

@app.route('/services')
def services():
    """Page des services"""
    current_year = datetime.now().year
    
    # Récupérer les services depuis SQLite
    services_list = []
    try:
        with get_db() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM services ORDER BY order_index ASC, created_at DESC')
                rows = cursor.fetchall()
                services_list = rows_to_list(rows)
                # Convertir id en string pour compatibilité
                for service in services_list:
                    service['_id'] = str(service['id'])
    except Exception as e:
        app.logger.error(f"Erreur lors de la récupération des services: {e}")
    
    return render_template('services.html', current_year=current_year, services=services_list, homepage_data=get_homepage_data())

@app.route('/parcours')
def parcours():
    """Page parcours / chronologie"""
    current_year = datetime.now().year
    items = []
    try:
        with get_db() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM career ORDER BY order_index ASC')
                items = rows_to_list(cursor.fetchall())
    except Exception as e:
        app.logger.error(f"Erreur parcours: {e}")
    return render_template('parcours.html', current_year=current_year, career=items, homepage_data=get_homepage_data())

@app.route('/cv')
def download_cv():
    from flask import send_from_directory
    docs = os.path.join(app.root_path, 'static', 'docs')
    filename = 'cv-claude-pricemou.pdf'
    path = os.path.join(docs, filename)
    if not os.path.exists(path):
        flash('CV temporairement indisponible', 'error')
        return redirect(url_for('index'))
    return send_from_directory(docs, filename, as_attachment=True)

@app.route('/sitemap.xml')
def sitemap():
    pages = [
        url_for('index', _external=True),
        url_for('parcours', _external=True),
        url_for('works', _external=True),
        url_for('services', _external=True),
        url_for('contact', _external=True),
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        xml.append(f'<url><loc>{page}</loc></url>')
    xml.append('</urlset>')
    return app.response_class('\n'.join(xml), mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    body = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /admin\n'
        'Disallow: /api/\n'
        f"Sitemap: {app.config['SITE_URL']}/sitemap.xml\n"
    )
    return app.response_class(body, mimetype='text/plain')

@app.route('/contact')
def contact():
    """Page de contact"""
    current_year = datetime.now().year
    homepage_data = get_homepage_data()
    portfolio_email = (homepage_data or {}).get('email') or app.config.get('PORTFOLIO_EMAIL')
    if not session.get('csrf_token'):
        session['csrf_token'] = generate_csrf_token()
    service = request.args.get('service', '')
    subject = ''
    if service:
        subject = f"Devis — {service.replace('-', ' ')}"
    return render_template(
        'contact.html',
        current_year=current_year,
        portfolio_email=portfolio_email,
        homepage_data=homepage_data,
        csrf_token=session.get('csrf_token'),
        preset_subject=subject,
    )

@app.route('/api/contact', methods=['POST'])
@app.route('/contact/submit', methods=['POST'])
@_limit_contact
def contact_submit():
    """Reçoit et stocke un message de contact"""
    try:
        # Honeypot anti-spam
        honeypot = ''
        if request.is_json:
            data = request.get_json() or {}
            honeypot = (data.get('website') or '').strip()
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            subject = data.get('subject', '').strip()
            message = data.get('message', '').strip()
            token = data.get('csrf_token', '')
        else:
            honeypot = (request.form.get('website') or '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
            token = request.form.get('csrf_token', '')

        if honeypot:
            return jsonify({'success': True, 'message': 'Votre message a été envoyé avec succès.'}), 200

        if token != session.get('csrf_token'):
            return jsonify({'success': False, 'error': 'Session expirée. Rechargez la page.'}), 400
        
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
        
        # Nettoyer et valider les données
        cleaned_data = {
            'name': sanitize_input(name, max_length=100),
            'email': sanitize_input(email, max_length=200),
            'subject': sanitize_input(subject, max_length=200),
            'message': sanitize_input(message, max_length=2000),
            'created_at': datetime.now(),
            'read': False,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')[:500]
        }
        
        # Stocker dans SQLite
        try:
            with get_db() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO contacts (name, email, subject, message, ip_address, user_agent)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        cleaned_data['name'],
                        cleaned_data['email'],
                        cleaned_data['subject'],
                        cleaned_data['message'],
                        cleaned_data.get('ip_address', ''),
                        cleaned_data.get('user_agent', '')
                    ))
                    contact_id = cursor.lastrowid
                    conn.commit()
                    app.logger.info(f"Nouveau message de contact reçu de {email} (ID: {contact_id})")
                    
                    # Optionnel: Envoyer un email de notification
                    send_contact_notification_email(cleaned_data)
                    
                    response_data = {
                        'success': True,
                        'message': 'Votre message a été envoyé avec succès. Je vous répondrai dans les plus brefs délais.'
                    }
                    app.logger.info(f"Contact sauvegardé avec succès: {email}")
                    response = jsonify(response_data)
                    response.headers['Content-Type'] = 'application/json; charset=utf-8'
                    return response, 200
                else:
                    app.logger.info(f"Message de contact reçu (SQLite non disponible): {email} - {subject}")
                    response_data = {
                        'success': True,
                        'message': 'Votre message a été reçu. Je vous répondrai dans les plus brefs délais.'
                    }
                    return jsonify(response_data), 200
        except Exception as e:
            app.logger.error(f"Erreur lors du stockage du contact: {e}")
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'enregistrement du message. Veuillez réessayer.'
            }), 500
            
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
        
        # Les routes API doivent toujours renvoyer du JSON (DELETE sans body inclus)
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Non authentifié. Veuillez vous connecter.'}), 401
        return redirect(url_for('admin_login'))
    return decorated_function

def json_serial(obj):
    """Sérialise les objets pour JSON (compatibilité)"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion administrateur"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
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
        
        # Vérifier les identifiants dans SQLite
        try:
            with get_db() as conn:
                if conn is None:
                    flash('Erreur de connexion à la base de données', 'error')
                    return render_template('admin_login.html')
                
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username,))
                admin_user = cursor.fetchone()
                
                if admin_user:
                    admin_user_dict = row_to_dict(admin_user)
                    # Utiliser check_password pour gérer bcrypt et migration depuis SHA256
                    stored_password = admin_user_dict['password']
                    
                    # Vérifier avec bcrypt
                    if check_password(password, stored_password):
                        # Si le mot de passe est en SHA256 (ancien système), le migrer vers bcrypt
                        if len(stored_password) == 64 and re.match(r'^[a-f0-9]{64}$', stored_password):
                            # Migration automatique vers bcrypt
                            new_hash = hash_password(password)
                            cursor.execute('UPDATE admin_users SET password = ? WHERE id = ?', 
                                         (new_hash, admin_user_dict['id']))
                            conn.commit()
                        # Mettre à jour la dernière connexion
                        cursor.execute('''
                            UPDATE admin_users 
                            SET last_login = ? 
                            WHERE username = ?
                        ''', (datetime.now(), username))
                        conn.commit()
                        
                        # Enregistrer dans l'historique
                        cursor.execute('''
                            INSERT INTO login_history (username, success, ip_address, user_agent)
                            VALUES (?, ?, ?, ?)
                        ''', (username, 1, request.remote_addr, request.headers.get('User-Agent', '')[:500]))
                        conn.commit()
                        
                        session['admin_logged_in'] = True
                        session['admin_username'] = username
                        session['admin_id'] = str(admin_user_dict['id'])
                        return redirect(url_for('admin_section', section='dashboard'))
                
                # Si on arrive ici, les identifiants sont incorrects
                # Enregistrer la tentative échouée dans l'historique
                try:
                    cursor.execute('''
                        INSERT INTO login_history (username, success, ip_address, user_agent)
                        VALUES (?, ?, ?, ?)
                    ''', (username, 0, request.remote_addr, request.headers.get('User-Agent', '')[:500]))
                    conn.commit()
                except:
                    pass  # Ignorer les erreurs d'historique
                
                flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
                return render_template('admin_login.html')
        except Exception as e:
            app.logger.error(f"Erreur lors de la connexion: {e}")
            flash('Erreur lors de la connexion. Veuillez réessayer.', 'error')
            return render_template('admin_login.html')
    
    # Si déjà connecté, rediriger vers admin
    if 'admin_logged_in' in session and session.get('admin_logged_in'):
        return redirect(url_for('admin_section', section='dashboard'))
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Déconnexion administrateur"""
    session.clear()
    flash('Vous avez été déconnecté avec succès', 'success')
    return redirect(url_for('admin_login'))

ADMIN_SECTIONS = {
    'dashboard': 'Tableau de bord',
    'homepage': "Page d'accueil",
    'skills': 'Compétences',
    'partners': 'Partenaires',
    'projects': 'Projets',
    'services': 'Services',
    'contacts': 'Contacts',
    'profile': 'Profil',
    'admins': 'Administrateurs',
}

@app.route('/admin')
@login_required
def admin():
    """Redirige vers le tableau de bord admin"""
    return redirect(url_for('admin_section', section='dashboard'))

@app.route('/admin/<section>')
@login_required
def admin_section(section):
    """Page d'administration pour une section donnée"""
    if section not in ADMIN_SECTIONS:
        flash('Section introuvable', 'error')
        return redirect(url_for('admin_section', section='dashboard'))
    return render_template(
        'admin.html',
        admin_username=session.get('admin_username', 'Admin'),
        active_section=section,
        section_title=ADMIN_SECTIONS[section],
    )

# ========== Routes API Analytics (tracking public) ==========
def _client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or ''

@app.route('/api/analytics/track-page', methods=['POST'])
def track_page_api():
    """Enregistre une vue de page + visiteur (public)"""
    try:
        data = request.get_json(silent=True) or {}
        page_path = sanitize_input(data.get('page_path') or request.path or '/', max_length=500)
        # Ne pas tracker l'admin / les assets
        if page_path.startswith('/admin') or page_path.startswith('/static') or page_path.startswith('/api'):
            return jsonify({'success': True, 'skipped': True}), 200

        ip_address = _client_ip()
        user_agent = request.headers.get('User-Agent', '')
        referer = request.headers.get('Referer', '')

        with get_db() as conn:
            if conn is None:
                return jsonify({'success': False, 'error': 'DB unavailable'}), 503
            from utils.analytics import track_page_view, track_visitor
            track_page_view(conn, page_path, ip_address, user_agent, referer)
            track_visitor(conn, ip_address, user_agent, page_path)
        return jsonify({'success': True}), 200
    except Exception as e:
        app.logger.error(f"Erreur track_page_api: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/analytics/track-project-view', methods=['POST'])
def track_project_view_api():
    """Enregistre une vue de projet (public)"""
    try:
        data = request.get_json(silent=True) or {}
        project_id = data.get('project_id')
        if project_id is None or str(project_id).strip() == '':
            return jsonify({'error': 'project_id requis'}), 400
        try:
            int(project_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'project_id invalide'}), 400

        ip_address = _client_ip()
        user_agent = request.headers.get('User-Agent', '')

        with get_db() as conn:
            if conn is None:
                return jsonify({'success': False, 'error': 'DB unavailable'}), 503
            from utils.analytics import track_project_view
            track_project_view(conn, project_id, ip_address, user_agent)
        return jsonify({'success': True}), 200
    except Exception as e:
        app.logger.error(f"Erreur track_project_view_api: {e}")
        return jsonify({'success': False}), 500

# ========== Route API pour les Statistiques ==========
@app.route('/api/analytics/stats', methods=['GET'])
@admin_required
def get_analytics_stats():
    """Récupère les statistiques globales"""
    try:
        days = int(request.args.get('days', 30))
        
        with get_db() as conn:
            if conn is None:
                return jsonify({
                    'error': 'Base de données non disponible',
                    'total_views': 0,
                    'total_visitors': 0,
                    'total_projects': 0,
                    'total_services': 0,
                    'total_contacts': 0,
                    'unread_contacts': 0,
                    'engagement_rate': 0,
                    'views_by_day': [],
                    'visitors_by_day': [],
                    'top_projects': []
                }), 503
            
            # Importer la fonction get_statistics
            from utils.analytics import get_statistics
            stats = get_statistics(conn, days)
            
            # Ajouter les messages non lus
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM contacts WHERE read = 0')
            unread_contacts = cursor.fetchone()[0]
            stats['unread_contacts'] = unread_contacts
            
            # Ajouter les projets par statut
            cursor.execute('SELECT status, COUNT(*) FROM projects GROUP BY status')
            projects_by_status = {}
            for row in cursor.fetchall():
                projects_by_status[row[0]] = row[1]
            stats['projects_by_status'] = projects_by_status
            
            return jsonify(stats), 200
            
    except Exception as e:
        app.logger.error(f"Erreur get_analytics_stats: {e}")
        return jsonify({
            'error': str(e),
            'total_views': 0,
            'total_visitors': 0,
            'total_projects': 0,
            'total_services': 0,
            'total_contacts': 0,
            'unread_contacts': 0,
            'engagement_rate': 0,
            'views_by_day': [],
            'visitors_by_day': [],
            'top_projects': []
        }), 500

# ========== API Routes pour Homepage ==========
@app.route('/api/homepage', methods=['GET'])
def get_homepage_api():
    """Récupère les données de la page d'accueil"""
    try:
        data = get_homepage_data()
        if data:
            # Convertir id en _id pour compatibilité
            if 'id' in data:
                data['_id'] = str(data['id'])
                del data['id']
        else:
            # Retourner des données par défaut si aucune donnée
            data = {
                "badge": "Disponible en freelance · Trois-Rivières (Québec)",
                "title_line1": "Du besoin métier",
                "title_line2": "au produit et à la donnée.",
                "description": app.config['PORTFOLIO_DESCRIPTION'],
                "email": app.config['PORTFOLIO_EMAIL'],
                "cta_text": "Discutons d'un mandat",
                "about_title": "Présentation",
                "about_name": app.config['PORTFOLIO_NAME'],
                "about_subtitle": app.config['PORTFOLIO_TITLE'],
                "about_description": "Baccalauréat en informatique (science des données) à l'UQTR."
            }
        return jsonify(data or {})
    except Exception as e:
        app.logger.error(f"Erreur get_homepage_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/homepage', methods=['PUT'])
@admin_required
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
        
        # Mettre à jour dans SQLite
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            # Vérifier si une entrée existe
            cursor.execute('SELECT id FROM homepage WHERE type = ?', ('header',))
            existing = cursor.fetchone()
            
            cleaned_data['type'] = 'header'
            cleaned_data['updated_at'] = datetime.now()
            
            if existing:
                # Mettre à jour
                cursor.execute('''
                    UPDATE homepage SET 
                        badge = ?, title_line1 = ?, title_line2 = ?, description = ?,
                        email = ?, cta_text = ?, about_title = ?, about_name = ?,
                        about_subtitle = ?, about_description = ?, updated_at = ?
                    WHERE type = ?
                ''', (
                    cleaned_data.get('badge'), cleaned_data.get('title_line1'),
                    cleaned_data.get('title_line2'), cleaned_data.get('description'),
                    cleaned_data.get('email'), cleaned_data.get('cta_text'),
                    cleaned_data.get('about_title'), cleaned_data.get('about_name'),
                    cleaned_data.get('about_subtitle'), cleaned_data.get('about_description'),
                    cleaned_data['updated_at'], 'header'
                ))
            else:
                # Insérer
                cursor.execute('''
                    INSERT INTO homepage (type, badge, title_line1, title_line2, description,
                                         email, cta_text, about_title, about_name,
                                         about_subtitle, about_description, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'header', cleaned_data.get('badge'), cleaned_data.get('title_line1'),
                    cleaned_data.get('title_line2'), cleaned_data.get('description'),
                    cleaned_data.get('email'), cleaned_data.get('cta_text'),
                    cleaned_data.get('about_title'), cleaned_data.get('about_name'),
                    cleaned_data.get('about_subtitle'), cleaned_data.get('about_description'),
                    cleaned_data['updated_at']
                ))
            conn.commit()
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
        skills = get_skills_data()
        if not isinstance(skills, list):
            skills = []
        # Convertir id en _id pour compatibilité
        for skill in skills:
            if 'id' in skill:
                skill['_id'] = str(skill['id'])
                skill['order'] = skill.get('order_index', 0)
                del skill['id']
                if 'order_index' in skill:
                    del skill['order_index']
        return jsonify(skills)
    except Exception as e:
        app.logger.error(f"Erreur get_skills_api: {e}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': f'Erreur lors de la récupération des compétences: {str(e)}',
            'data': []
        }), 500

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
        
        # Insérer dans SQLite
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO skills (title, description, icon, projects_count, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                cleaned_data['title'],
                cleaned_data['description'],
                cleaned_data.get('icon', ''),
                cleaned_data['projects_count'],
                cleaned_data.get('order', 0),
                datetime.now(),
                datetime.now()
            ))
            skill_id = cursor.lastrowid
            conn.commit()
            return jsonify({'success': True, 'id': str(skill_id), 'message': 'Compétence créée'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_skill_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills/<skill_id>', methods=['PUT'])
@admin_required
def update_skill_api(skill_id):
    """Met à jour une compétence"""
    try:
        data = request.get_json()
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            # Construire la requête UPDATE dynamiquement
            updates = []
            values = []
            if 'title' in data:
                updates.append('title = ?')
                values.append(sanitize_input(data['title'], max_length=100))
            if 'description' in data:
                updates.append('description = ?')
                values.append(sanitize_input(data['description'], max_length=500))
            if 'icon' in data:
                updates.append('icon = ?')
                values.append(sanitize_input(data['icon'], max_length=200))
            if 'projects_count' in data:
                updates.append('projects_count = ?')
                values.append(int(data['projects_count']) if str(data['projects_count']).isdigit() else 0)
            if 'order' in data:
                updates.append('order_index = ?')
                values.append(int(data['order']) if str(data['order']).isdigit() else 0)
            
            updates.append('updated_at = ?')
            values.append(datetime.now())
            values.append(int(skill_id))
            
            cursor.execute(f'''
                UPDATE skills SET {', '.join(updates)}
                WHERE id = ?
            ''', values)
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({'success': True, 'message': 'Compétence mise à jour'})
            return jsonify({'error': 'Compétence non trouvée'}), 404
    except Exception as e:
        app.logger.error(f"Erreur update_skill_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills/<skill_id>', methods=['DELETE'])
@admin_required
def delete_skill_api(skill_id):
    """Supprime une compétence"""
    try:
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('DELETE FROM skills WHERE id = ?', (int(skill_id),))
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({'success': True, 'message': 'Compétence supprimée'})
            return jsonify({'error': 'Compétence non trouvée'}), 404
    except Exception as e:
        app.logger.error(f"Erreur delete_skill_api: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Partners ==========
@app.route('/api/partners', methods=['GET'])
def get_partners_api():
    """Récupère tous les partenaires"""
    try:
        partners = get_partners_data()
        if not isinstance(partners, list):
            partners = []
        # Convertir id en _id pour compatibilité
        for partner in partners:
            if 'id' in partner:
                partner['_id'] = str(partner['id'])
                partner['order'] = partner.get('order_index', 0)
                partner['image'] = partner.get('image', '')
                del partner['id']
                if 'order_index' in partner:
                    del partner['order_index']
        return jsonify(partners)
    except Exception as e:
        app.logger.error(f"Erreur get_partners_api: {e}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': f'Erreur lors de la récupération des partenaires: {str(e)}',
            'data': []
        }), 500

@app.route('/api/partners', methods=['POST'])
@admin_required
def create_partner_api():
    """Crée un nouveau partenaire"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Validation des champs requis
        required_fields = ['name']
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
        
        # Insérer dans SQLite
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO partners (name, image, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                cleaned_data['name'],
                cleaned_data.get('logo', '') or cleaned_data.get('image', ''),
                cleaned_data.get('order', 0),
                datetime.now(),
                datetime.now()
            ))
            partner_id = cursor.lastrowid
            conn.commit()
            return jsonify({'success': True, 'id': str(partner_id), 'message': 'Partenaire créé'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_partner_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/partners/<partner_id>', methods=['PUT'])
@admin_required
def update_partner_api(partner_id):
    """Met à jour un partenaire"""
    try:
        data = request.get_json()
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            updates = []
            values = []
            if 'name' in data:
                updates.append('name = ?')
                values.append(sanitize_input(data['name'], max_length=100))
            if 'logo' in data or 'image' in data:
                updates.append('image = ?')
                values.append(sanitize_input(data.get('logo') or data.get('image', ''), max_length=500))
            if 'order' in data:
                updates.append('order_index = ?')
                values.append(int(data['order']) if str(data['order']).isdigit() else 0)
            
            updates.append('updated_at = ?')
            values.append(datetime.now())
            values.append(int(partner_id))
            
            cursor.execute(f'''
                UPDATE partners SET {', '.join(updates)}
                WHERE id = ?
            ''', values)
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({'success': True, 'message': 'Partenaire mis à jour'})
            return jsonify({'error': 'Partenaire non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur update_partner_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/partners/<partner_id>', methods=['DELETE'])
@admin_required
def delete_partner_api(partner_id):
    """Supprime un partenaire"""
    try:
        try:
            pid = int(partner_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'ID partenaire invalide'}), 400

        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM partners WHERE id = ?', (pid,))
            if cursor.fetchone() is None:
                return jsonify({'error': 'Partenaire non trouvé'}), 404

            cursor.execute('DELETE FROM partners WHERE id = ?', (pid,))
            conn.commit()
            return jsonify({'success': True, 'message': 'Partenaire supprimé'})
    except Exception as e:
        app.logger.error(f"Erreur delete_partner_api: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API Routes pour Projects ==========
@app.route('/api/projects', methods=['GET'])
def get_projects_api():
    """Récupère la liste des projets"""
    try:
        with get_db() as conn:
            if conn is None:
                return jsonify({
                    'error': 'Base de données non disponible',
                    'message': 'La connexion à la base de données n\'est pas disponible.',
                    'data': []
                }), 503
            
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
            rows = cursor.fetchall()
            projects = rows_to_list(rows)
            # Convertir id en _id pour compatibilité
            for project in projects:
                project['_id'] = str(project['id'])
                project['order'] = project.get('order_index', 0)
                project['featured'] = bool(project.get('featured', 0))
                if 'additional_images' not in project:
                    project['additional_images'] = ''
                del project['id']
                if 'order_index' in project:
                    del project['order_index']
            
            return jsonify(projects)
    except Exception as e:
        app.logger.error(f"Erreur get_projects_api: {e}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': f'Erreur lors de la récupération des projets: {str(e)}',
            'data': []
        }), 500

@app.route('/api/projects', methods=['POST'])
@admin_required
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
            'additional_images': sanitize_input(data.get('additional_images', ''), max_length=2000),
            'link': sanitize_input(data.get('link', ''), max_length=500),
            'github_link': sanitize_input(data.get('github_link', ''), max_length=500),
            'status': sanitize_input(data.get('status', 'published'), max_length=50),
            'order': int(data.get('order', 0)) if str(data.get('order', 0)).isdigit() else 0,
            'featured': bool(data.get('featured', False))
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
        
        # Insérer dans SQLite
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (title, description, technologies, image, additional_images, link, github_link,
                                     status, order_index, featured, views, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cleaned_data['title'],
                cleaned_data['description'],
                cleaned_data['technologies'],
                cleaned_data.get('image', ''),
                cleaned_data.get('additional_images', ''),
                cleaned_data.get('link', ''),
                cleaned_data.get('github_link', ''),
                cleaned_data['status'],
                cleaned_data.get('order', 0),
                1 if cleaned_data.get('featured', False) else 0,
                0,  # views
                datetime.now(),
                datetime.now()
            ))
            project_id = cursor.lastrowid
            conn.commit()
            return jsonify({'success': True, 'id': str(project_id), 'message': 'Projet créé'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_project_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
@admin_required
def update_project_api(project_id):
    """Met à jour un projet"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            updates = []
            values = []
            
            max_lengths = {
                'title': 200, 'description': 1000, 'technologies': 200,
                'image': 500, 'additional_images': 2000, 'link': 500, 'github_link': 500, 'status': 50
            }
            
            for key, value in data.items():
                if key in max_lengths:
                    if isinstance(value, str):
                        updates.append(f'{key} = ?')
                        values.append(sanitize_input(value, max_length=max_lengths[key]))
                    else:
                        updates.append(f'{key} = ?')
                        values.append(value)
                elif key == 'order':
                    updates.append('order_index = ?')
                    values.append(int(value) if str(value).isdigit() else 0)
                elif key == 'featured':
                    updates.append('featured = ?')
                    values.append(1 if bool(value) else 0)
            
            # Valider les URLs
            if 'link' in data and data['link'] and not validate_url(data['link']):
                return jsonify({'error': 'Format d\'URL de lien invalide'}), 400
            if 'github_link' in data and data['github_link'] and not validate_url(data['github_link']):
                return jsonify({'error': 'Format d\'URL GitHub invalide'}), 400
            if 'status' in data:
                valid_statuses = ['draft', 'published', 'archived']
                if data['status'] not in valid_statuses:
                    updates.append('status = ?')
                    values.append('published')
            
            updates.append('updated_at = ?')
            values.append(datetime.now())
            values.append(int(project_id))
            
            cursor.execute(f'''
                UPDATE projects SET {', '.join(updates)}
                WHERE id = ?
            ''', values)
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({'success': True, 'message': 'Projet mis à jour'})
            return jsonify({'error': 'Projet non trouvé'}), 404
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur update_project_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project_api(project_id):
    """Récupère un projet spécifique"""
    try:
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE id = ?', (int(project_id),))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Projet non trouvé'}), 404
            
            project = row_to_dict(row)
            project['_id'] = str(project['id'])
            project['order'] = project.get('order_index', 0)
            project['featured'] = bool(project.get('featured', 0))
            if 'additional_images' not in project:
                project['additional_images'] = ''
            del project['id']
            if 'order_index' in project:
                del project['order_index']
            
            return jsonify(project), 200
    except Exception as e:
        app.logger.error(f"Erreur get_project_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
@admin_required
def delete_project_api(project_id):
    """Supprime un projet"""
    try:
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('DELETE FROM projects WHERE id = ?', (int(project_id),))
            conn.commit()
            
            if cursor.rowcount > 0:
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
        with get_db() as conn:
            if conn is None:
                return jsonify({
                    'error': 'Base de données non disponible',
                    'message': 'La connexion à la base de données n\'est pas disponible.',
                    'data': []
                }), 503
            
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM services ORDER BY order_index ASC, created_at DESC')
            rows = cursor.fetchall()
            services = rows_to_list(rows)
            # Convertir id en _id pour compatibilité
            for service in services:
                service['_id'] = str(service['id'])
                service['order'] = service.get('order_index', 0)
                del service['id']
                if 'order_index' in service:
                    del service['order_index']
            
            return jsonify(services)
    except Exception as e:
        app.logger.error(f"Erreur get_services_api: {e}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': f'Erreur lors de la récupération des services: {str(e)}',
            'data': []
        }), 500

@app.route('/api/services', methods=['POST'])
@admin_required
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
        
        # Insérer dans SQLite
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO services (title, description, icon, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                cleaned_data['title'],
                cleaned_data['description'],
                cleaned_data.get('icon', ''),
                cleaned_data.get('order', 0),
                datetime.now(),
                datetime.now()
            ))
            service_id = cursor.lastrowid
            conn.commit()
            return jsonify({'success': True, 'id': str(service_id), 'message': 'Service créé'})
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur create_service_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/services/<service_id>', methods=['PUT'])
@admin_required
def update_service_api(service_id):
    """Met à jour un service"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            updates = []
            values = []
            
            max_lengths = {'title': 200, 'description': 1000, 'icon': 500}
            
            for key, value in data.items():
                if key in max_lengths:
                    updates.append(f'{key} = ?')
                    if isinstance(value, str):
                        values.append(sanitize_input(value, max_length=max_lengths[key]))
                    else:
                        values.append(value)
                elif key == 'order':
                    updates.append('order_index = ?')
                    values.append(int(value) if str(value).isdigit() else 0)
            
            # Valider l'URL de l'icône si présente
            if 'icon' in data and data['icon'] and not validate_url(data['icon']) and not data['icon'].startswith('icons/'):
                return jsonify({'error': 'Format d\'URL d\'icône invalide'}), 400
            
            updates.append('updated_at = ?')
            values.append(datetime.now())
            values.append(int(service_id))
            
            cursor.execute(f'''
                UPDATE services SET {', '.join(updates)}
                WHERE id = ?
            ''', values)
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({'success': True, 'message': 'Service mis à jour'})
            return jsonify({'error': 'Service non trouvé'}), 404
    except ValueError as e:
        return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Erreur update_service_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/services/<service_id>', methods=['DELETE'])
@admin_required
def delete_service_api(service_id):
    """Supprime un service"""
    try:
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('DELETE FROM services WHERE id = ?', (int(service_id),))
            conn.commit()
            
            if cursor.rowcount > 0:
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
        with get_db() as conn:
            if conn is None:
                return jsonify({
                    'error': 'Base de données non disponible',
                    'message': 'La connexion à la base de données n\'est pas disponible.',
                    'data': []
                }), 503
            
            cursor = conn.cursor()
            read_filter = request.args.get('read')
            limit = request.args.get('limit', type=int)
            
            if read_filter is not None:
                read_value = 1 if read_filter.lower() == 'true' else 0
                cursor.execute('SELECT * FROM contacts WHERE read = ? ORDER BY created_at DESC', (read_value,))
            else:
                cursor.execute('SELECT * FROM contacts ORDER BY created_at DESC')
            
            rows = cursor.fetchall()
            contacts = rows_to_list(rows)
            
            # Limiter le nombre de résultats si spécifié
            if limit:
                contacts = contacts[:limit]
            
            # Convertir id en _id pour compatibilité
            for contact in contacts:
                contact['_id'] = str(contact['id'])
                contact['read'] = bool(contact.get('read', 0))
                del contact['id']
                if 'created_at' in contact:
                    if isinstance(contact['created_at'], str):
                        pass  # Déjà en string
                    else:
                        contact['created_at'] = contact['created_at'].isoformat() if hasattr(contact['created_at'], 'isoformat') else str(contact['created_at'])
            
            return jsonify(contacts)
    except Exception as e:
        app.logger.error(f"Erreur get_contacts_api: {e}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': f'Erreur lors de la récupération des contacts: {str(e)}',
            'data': []
        }), 500

@app.route('/api/contacts/<contact_id>/read', methods=['PUT'])
@admin_required
def mark_contact_read_api(contact_id):
    """Marque un message comme lu ou non lu"""
    try:
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            data = request.get_json()
            read_status = 1 if data.get('read', True) else 0
            
            cursor = conn.cursor()
            cursor.execute('UPDATE contacts SET read = ? WHERE id = ?', (read_status, int(contact_id)))
            conn.commit()
            
            if cursor.rowcount > 0:
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
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('DELETE FROM contacts WHERE id = ?', (int(contact_id),))
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({'success': True, 'message': 'Message supprimé'})
            return jsonify({'error': 'Message non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur delete_contact_api: {e}")
        return jsonify({'error': str(e)}), 500

# Les fonctions de validation sont importées depuis utils.validators

# ========== Routes API pour la Gestion du Profil Admin ==========
@app.route('/api/admin/profile', methods=['GET'])
@admin_required
def get_admin_profile():
    """Récupère les informations du profil de l'administrateur connecté"""
    try:
        admin_id = session.get('admin_id')
        if not admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, full_name, created_at, last_login FROM admin_users WHERE id = ?', (int(admin_id),))
            admin_user = cursor.fetchone()
            
            if not admin_user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            profile_data = row_to_dict(admin_user)
            # Formater les dates
            if profile_data.get('created_at'):
                profile_data['created_at'] = profile_data['created_at'].isoformat() if hasattr(profile_data['created_at'], 'isoformat') else str(profile_data['created_at'])
            if profile_data.get('last_login'):
                profile_data['last_login'] = profile_data['last_login'].isoformat() if hasattr(profile_data['last_login'], 'isoformat') else str(profile_data['last_login'])
            
            return jsonify(profile_data), 200
    except Exception as e:
        app.logger.error(f"Erreur get_admin_profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/profile', methods=['PUT'])
@admin_required
def update_admin_profile():
    """Met à jour les informations du profil de l'administrateur connecté"""
    try:
        admin_id = session.get('admin_id')
        if not admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            updates = []
            values = []
            
            # Valider et mettre à jour l'email si fourni
            if 'email' in data:
                email = sanitize_input(data['email'], max_length=100)
                if email and not validate_email(email):
                    return jsonify({'error': 'Format d\'email invalide'}), 400
                updates.append('email = ?')
                values.append(email if email else None)
            
            # Mettre à jour le nom complet si fourni
            if 'full_name' in data:
                full_name = sanitize_input(data['full_name'], max_length=100)
                updates.append('full_name = ?')
                values.append(full_name if full_name else None)
            
            if not updates:
                return jsonify({'error': 'Aucune donnée à mettre à jour'}), 400
            
            values.append(int(admin_id))
            
            cursor.execute(f'''
                UPDATE admin_users SET {', '.join(updates)}
                WHERE id = ?
            ''', values)
            conn.commit()
            
            if cursor.rowcount > 0:
                app.logger.info(f"Profil admin mis à jour (ID: {admin_id})")
                return jsonify({'success': True, 'message': 'Profil mis à jour avec succès'}), 200
            return jsonify({'error': 'Aucune modification effectuée'}), 400
    except Exception as e:
        app.logger.error(f"Erreur update_admin_profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/profile/password', methods=['PUT'])
@admin_required
def change_admin_password():
    """Change le mot de passe de l'administrateur connecté"""
    try:
        admin_id = session.get('admin_id')
        if not admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': 'Tous les champs sont requis'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Les nouveaux mots de passe ne correspondent pas'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Le nouveau mot de passe doit contenir au moins 6 caractères'}), 400
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            # Récupérer l'utilisateur et vérifier le mot de passe actuel
            cursor.execute('SELECT password FROM admin_users WHERE id = ?', (int(admin_id),))
            user_row = cursor.fetchone()
            
            if not user_row:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            stored_password = user_row[0]
            
            # Vérifier le mot de passe actuel
            if not check_password(current_password, stored_password):
                return jsonify({'error': 'Mot de passe actuel incorrect'}), 401
            
            # Hasher le nouveau mot de passe
            new_password_hash = hash_password(new_password)
            
            # Mettre à jour le mot de passe
            cursor.execute('UPDATE admin_users SET password = ? WHERE id = ?', (new_password_hash, int(admin_id)))
            conn.commit()
            
            app.logger.info(f"Mot de passe changé pour l'admin (ID: {admin_id})")
            return jsonify({'success': True, 'message': 'Mot de passe changé avec succès'}), 200
    except Exception as e:
        app.logger.error(f"Erreur change_admin_password: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/profile/login-history', methods=['GET'])
@admin_required
def get_login_history():
    """Récupère l'historique des connexions de l'administrateur connecté"""
    try:
        admin_id = session.get('admin_id')
        username = session.get('admin_username')
        if not admin_id or not username:
            return jsonify({'error': 'Non authentifié'}), 401
        
        limit = request.args.get('limit', type=int) or 50
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, success, ip_address, user_agent, login_time
                FROM login_history
                WHERE username = ?
                ORDER BY login_time DESC
                LIMIT ?
            ''', (username, limit))
            
            rows = cursor.fetchall()
            history = rows_to_list(rows)
            
            # Formater les données
            for entry in history:
                entry['success'] = bool(entry.get('success', 0))
                if entry.get('login_time'):
                    entry['login_time'] = entry['login_time'].isoformat() if hasattr(entry['login_time'], 'isoformat') else str(entry['login_time'])
            
            return jsonify(history), 200
    except Exception as e:
        app.logger.error(f"Erreur get_login_history: {e}")
        return jsonify({'error': str(e)}), 500

# ========== Routes API pour la Gestion des Administrateurs ==========
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_admin_users():
    """Récupère la liste de tous les administrateurs"""
    try:
        with get_db() as conn:
            if conn is None:
                return jsonify({
                    'error': 'Base de données non disponible',
                    'message': 'La connexion à la base de données n\'est pas disponible.',
                    'data': []
                }), 503
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, full_name, created_at, last_login 
                FROM admin_users 
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            admins = rows_to_list(rows)
            
            # Formater les données
            for admin in admins:
                admin['_id'] = str(admin['id'])
                del admin['id']
                admin['created_at'] = admin['created_at'].isoformat() if hasattr(admin['created_at'], 'isoformat') else str(admin['created_at'])
                if admin.get('last_login'):
                    admin['last_login'] = admin['last_login'].isoformat() if hasattr(admin['last_login'], 'isoformat') else str(admin['last_login'])
            
            return jsonify(admins), 200
    except Exception as e:
        app.logger.error(f"Erreur get_admin_users: {e}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': f'Erreur lors de la récupération des administrateurs: {str(e)}',
            'data': []
        }), 500

@app.route('/api/admin/users', methods=['POST'])
@admin_required
def create_admin_user():
    """Crée un nouvel administrateur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Validation des champs requis
        username = sanitize_input(data.get('username', ''), max_length=50)
        password = data.get('password', '').strip()
        email = sanitize_input(data.get('email', ''), max_length=100) if data.get('email') else None
        full_name = sanitize_input(data.get('full_name', ''), max_length=100) if data.get('full_name') else None
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({'error': 'Le nom d\'utilisateur doit contenir au moins 3 caractères'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
        
        if email and not validate_email(email):
            return jsonify({'error': 'Format d\'email invalide'}), 400
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            
            # Vérifier si le nom d'utilisateur existe déjà
            cursor.execute('SELECT id FROM admin_users WHERE username = ?', (username,))
            if cursor.fetchone():
                return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
            
            # Hasher le mot de passe
            password_hash = hash_password(password)
            
            # Créer l'administrateur
            cursor.execute('''
                INSERT INTO admin_users (username, password, email, full_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, email, full_name, datetime.now()))
            
            admin_id = cursor.lastrowid
            conn.commit()
            
            app.logger.info(f"Nouvel administrateur créé: {username} (ID: {admin_id})")
            return jsonify({
                'success': True,
                'id': str(admin_id),
                'message': 'Administrateur créé avec succès'
            }), 201
            
    except Exception as e:
        app.logger.error(f"Erreur create_admin_user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<admin_id>', methods=['PUT'])
@admin_required
def update_admin_user(admin_id):
    """Met à jour un administrateur"""
    try:
        current_admin_id = session.get('admin_id')
        if not current_admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        # Empêcher un admin de se modifier lui-même via cette route (utiliser /api/admin/profile)
        if str(current_admin_id) == str(admin_id):
            return jsonify({'error': 'Utilisez la section Profil pour modifier vos propres informations'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            
            # Vérifier que l'admin existe
            cursor.execute('SELECT id FROM admin_users WHERE id = ?', (int(admin_id),))
            if not cursor.fetchone():
                return jsonify({'error': 'Administrateur non trouvé'}), 404
            
            updates = []
            values = []
            
            # Mettre à jour l'email si fourni
            if 'email' in data:
                email = sanitize_input(data['email'], max_length=100) if data['email'] else None
                if email and not validate_email(email):
                    return jsonify({'error': 'Format d\'email invalide'}), 400
                updates.append('email = ?')
                values.append(email)
            
            # Mettre à jour le nom complet si fourni
            if 'full_name' in data:
                full_name = sanitize_input(data['full_name'], max_length=100) if data['full_name'] else None
                updates.append('full_name = ?')
                values.append(full_name)
            
            # Mettre à jour le mot de passe si fourni
            if 'password' in data and data['password']:
                password = data['password'].strip()
                if len(password) < 6:
                    return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
                password_hash = hash_password(password)
                updates.append('password = ?')
                values.append(password_hash)
            
            if not updates:
                return jsonify({'error': 'Aucune donnée à mettre à jour'}), 400
            
            values.append(int(admin_id))
            
            cursor.execute(f'''
                UPDATE admin_users SET {', '.join(updates)}
                WHERE id = ?
            ''', values)
            conn.commit()
            
            if cursor.rowcount > 0:
                app.logger.info(f"Administrateur mis à jour (ID: {admin_id})")
                return jsonify({'success': True, 'message': 'Administrateur mis à jour avec succès'}), 200
            return jsonify({'error': 'Aucune modification effectuée'}), 400
            
    except Exception as e:
        app.logger.error(f"Erreur update_admin_user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<admin_id>', methods=['DELETE'])
@admin_required
def delete_admin_user(admin_id):
    """Supprime un administrateur"""
    try:
        current_admin_id = session.get('admin_id')
        if not current_admin_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        # Empêcher un admin de se supprimer lui-même
        if str(current_admin_id) == str(admin_id):
            return jsonify({'error': 'Vous ne pouvez pas supprimer votre propre compte'}), 400
        
        with get_db() as conn:
            if conn is None:
                return jsonify({'error': 'Base de données non disponible'}), 503
            
            cursor = conn.cursor()
            
            # Vérifier que l'admin existe
            cursor.execute('SELECT username FROM admin_users WHERE id = ?', (int(admin_id),))
            admin_row = cursor.fetchone()
            if not admin_row:
                return jsonify({'error': 'Administrateur non trouvé'}), 404
            
            # Vérifier qu'il reste au moins un administrateur
            cursor.execute('SELECT COUNT(*) FROM admin_users')
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                return jsonify({'error': 'Impossible de supprimer le dernier administrateur'}), 400
            
            # Supprimer l'administrateur
            cursor.execute('DELETE FROM admin_users WHERE id = ?', (int(admin_id),))
            conn.commit()
            
            if cursor.rowcount > 0:
                app.logger.info(f"Administrateur supprimé (ID: {admin_id}, Username: {admin_row[0]})")
                return jsonify({'success': True, 'message': 'Administrateur supprimé avec succès'}), 200
            return jsonify({'error': 'Administrateur non trouvé'}), 404
            
    except Exception as e:
        app.logger.error(f"Erreur delete_admin_user: {e}")
        return jsonify({'error': str(e)}), 500

# ========== Route de diagnostic SQLite ==========
@app.route('/api/admin/mongo-status', methods=['GET'])
@admin_required
def mongo_status_api():
    """Route de diagnostic pour vérifier l'état de la connexion SQLite (compatibilité avec l'ancien nom)"""
    try:
        db_path = os.getenv('SQLITE_DB_PATH', 'portfolio.db')
        
        status = {
            'db_type': 'SQLite',
            'db_path': db_path,
            'connection_status': 'unknown',
            'tables': [],
            'error': None
        }
        
        # Tester la connexion SQLite
        try:
            with get_db() as conn:
                if conn is None:
                    status['connection_status'] = 'disconnected'
                    status['error'] = 'Impossible de se connecter à SQLite'
                    return jsonify(status), 503
                
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                status['tables'] = tables
                status['connection_status'] = 'connected'
                
                # Compter les documents dans chaque table
                counts = {}
                for table_name in tables:
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                        counts[table_name] = cursor.fetchone()[0]
                    except:
                        counts[table_name] = 'error'
                status['document_counts'] = counts
                
        except Exception as e:
            status['connection_status'] = 'error'
            status['error'] = str(e)
            return jsonify(status), 500
        
        return jsonify(status), 200
        
    except Exception as e:
        app.logger.error(f"Erreur mongo_status_api: {e}")
        return jsonify({
            'connection_status': 'error',
            'error': str(e)
        }), 500

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

