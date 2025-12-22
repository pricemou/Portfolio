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

# Fonctions utilitaires pour l'authentification
def hash_password(password):
    """Hash un mot de passe avec SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

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
    app.config['MONGO_CLIENT'] = mongo_client
else:
    app.config['MONGO_DB'] = None
    app.config['MONGO_CLIENT'] = None
    print("⚠️  L'application fonctionnera sans base de données MongoDB")

def ensure_mongo_connection():
    """
    Vérifie et réinitialise la connexion MongoDB si nécessaire
    Retourne la base de données MongoDB ou None
    """
    mongo_db = app.config.get('MONGO_DB')
    mongo_client = app.config.get('MONGO_CLIENT')
    
    # Si on a déjà une connexion, tester si elle fonctionne encore
    if mongo_db is not None and mongo_client is not None:
        try:
            # Tester la connexion
            mongo_client.admin.command('ping')
            return mongo_db
        except Exception as e:
            app.logger.warning(f"Connexion MongoDB perdue, tentative de reconnexion: {e}")
            # La connexion est perdue, essayer de se reconnecter
            pass
    
    # Essayer de se reconnecter
    try:
        new_client, new_db = get_mongo_client()
        if new_db is not None:
            app.config['MONGO_DB'] = new_db
            app.config['MONGO_CLIENT'] = new_client
            app.logger.info("✅ Reconnexion MongoDB réussie")
            return new_db
        else:
            app.logger.error("❌ Impossible de se reconnecter à MongoDB")
            return None
    except Exception as e:
        app.logger.error(f"❌ Erreur lors de la reconnexion MongoDB: {e}")
        return None

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
    
    # Récupérer les projets depuis MongoDB (si disponible)
    projects = []
    mongo_db = app.config.get('MONGO_DB')
    if mongo_db is not None:
        try:
            projects_collection = mongo_db.projects
            # Récupérer uniquement les projets publiés, triés par ordre puis par date
            projects = list(projects_collection.find({"status": "published"}).sort("order", 1).sort("created_at", -1))
            # Convertir ObjectId en string pour le template
            for project in projects:
                if '_id' in project:
                    project['_id'] = str(project['_id'])
        except Exception as e:
            print(f"Erreur lors de la récupération des projets: {e}")
    
    return render_template('works.html', 
                         current_year=current_year,
                         projects=projects)

@app.route('/services')
def services():
    """Page des services"""
    current_year = datetime.now().year
    
    # Récupérer les services depuis MongoDB (si disponible)
    services_list = []
    mongo_db = app.config.get('MONGO_DB')
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
    return render_template('contact.html', current_year=current_year, portfolio_email=portfolio_email)

@app.route('/api/contact', methods=['POST'])
@app.route('/contact/submit', methods=['POST'])
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
        
        # Stocker dans MongoDB
        mongo_db = app.config.get('MONGO_DB')
        if mongo_db is not None:
            try:
                contacts_collection = mongo_db.contacts
                result = contacts_collection.insert_one(cleaned_data)
                app.logger.info(f"Nouveau message de contact reçu de {email} (ID: {result.inserted_id})")
                
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
            except Exception as e:
                app.logger.error(f"Erreur lors du stockage du contact: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Erreur lors de l\'enregistrement du message. Veuillez réessayer.'
                }), 500
        else:
            # Mode sans MongoDB - juste logger
            app.logger.info(f"Message de contact reçu (MongoDB non disponible): {email} - {subject}")
            response_data = {
                'success': True,
                'message': 'Votre message a été reçu. Je vous répondrai dans les plus brefs délais.'
            }
            return jsonify(response_data), 200
            
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
                
                if admin_user and admin_user['password'] == hash_password(password):
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
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            # Retourner des données par défaut si MongoDB n'est pas disponible
            app.logger.warning("MongoDB non disponible pour get_homepage_api")
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
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            # Retourner une erreur explicite si MongoDB n'est pas disponible
            app.logger.warning("MongoDB non disponible pour get_skills_api")
            return jsonify({
                'error': 'MongoDB non disponible',
                'message': 'La connexion à la base de données n\'est pas disponible. Vérifiez la configuration MONGO_URI.',
                'data': []
            }), 503
        
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
    try:
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.error("MongoDB non disponible pour update_skill_api")
            return jsonify({'error': 'MongoDB non disponible'}), 500
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
    try:
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.error("MongoDB non disponible pour delete_skill_api")
            return jsonify({'error': 'MongoDB non disponible'}), 500
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
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            # Retourner une erreur explicite si MongoDB n'est pas disponible
            app.logger.warning("MongoDB non disponible pour get_partners_api")
            return jsonify({
                'error': 'MongoDB non disponible',
                'message': 'La connexion à la base de données n\'est pas disponible. Vérifiez la configuration MONGO_URI.',
                'data': []
            }), 503
        
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
    try:
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.error("MongoDB non disponible pour update_partner_api")
            return jsonify({'error': 'MongoDB non disponible'}), 500
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
    try:
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.error("MongoDB non disponible pour delete_partner_api")
            return jsonify({'error': 'MongoDB non disponible'}), 500
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
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.warning("MongoDB non disponible pour get_projects_api")
            return jsonify({
                'error': 'MongoDB non disponible',
                'message': 'La connexion à la base de données n\'est pas disponible. Vérifiez la configuration MONGO_URI.',
                'data': []
            }), 503
        
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
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.warning("MongoDB non disponible pour get_services_api")
            return jsonify({
                'error': 'MongoDB non disponible',
                'message': 'La connexion à la base de données n\'est pas disponible. Vérifiez la configuration MONGO_URI.',
                'data': []
            }), 503
        
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
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.warning("MongoDB non disponible pour get_contacts_api")
            return jsonify({
                'error': 'MongoDB non disponible',
                'message': 'La connexion à la base de données n\'est pas disponible. Vérifiez la configuration MONGO_URI.',
                'data': []
            }), 503
        
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
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            app.logger.error("MongoDB non disponible pour delete_contact_api")
            return jsonify({'error': 'Base de données non disponible'}), 503
        
        result = mongo_db.contacts.delete_one({"_id": ObjectId(contact_id)})
        
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Message supprimé'})
        return jsonify({'error': 'Message non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur delete_contact_api: {e}")
        return jsonify({'error': str(e)}), 500

# Les fonctions de validation sont importées depuis utils.validators

# ========== Route de diagnostic MongoDB ==========
@app.route('/api/admin/mongo-status', methods=['GET'])
@admin_required
def mongo_status_api():
    """Route de diagnostic pour vérifier l'état de la connexion MongoDB"""
    try:
        mongo_uri = os.getenv('MONGO_URI')
        mongo_db_name = os.getenv('MONGO_DB_NAME', 'portfolio_db')
        
        status = {
            'mongo_uri_configured': bool(mongo_uri),
            'mongo_uri_preview': mongo_uri[:20] + '...' if mongo_uri and len(mongo_uri) > 20 else mongo_uri if mongo_uri else None,
            'mongo_db_name': mongo_db_name,
            'connection_status': 'unknown',
            'collections': [],
            'error': None
        }
        
        mongo_db = ensure_mongo_connection()
        if mongo_db is None:
            status['connection_status'] = 'disconnected'
            status['error'] = 'Impossible de se connecter à MongoDB'
            return jsonify(status), 503
        
        # Tester la connexion
        try:
            mongo_client = app.config.get('MONGO_CLIENT')
            mongo_client.admin.command('ping')
            status['connection_status'] = 'connected'
            
            # Lister les collections disponibles
            status['collections'] = mongo_db.list_collection_names()
            
            # Compter les documents dans chaque collection
            counts = {}
            for collection_name in status['collections']:
                try:
                    counts[collection_name] = mongo_db[collection_name].count_documents({})
                except:
                    counts[collection_name] = 'error'
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

