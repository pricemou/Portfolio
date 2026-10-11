"""
Module de gestion de la connexion SQLite
"""
import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import json

# Chemin de la base de données SQLite
DB_PATH = os.getenv('SQLITE_DB_PATH', 'portfolio.db')

def get_db_connection():
    """
    Crée et retourne une connexion SQLite
    
    Returns:
        sqlite3.Connection: Connexion à la base de données SQLite
    """
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        return conn
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à SQLite: {e}")
        return None

@contextmanager
def get_db():
    """
    Contexte manager pour gérer les connexions SQLite
    """
    conn = get_db_connection()
    if conn is None:
        yield None
        return
    
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur SQLite: {e}")
        raise
    finally:
        conn.close()

def init_database():
    """
    Initialise la base de données SQLite avec les tables nécessaires
    """
    try:
        with get_db() as conn:
            if conn is None:
                print("❌ Impossible de créer la connexion SQLite")
                return False
            
            cursor = conn.cursor()
            
            # Table homepage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS homepage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL DEFAULT 'header',
                    badge TEXT,
                    title_line1 TEXT,
                    title_line2 TEXT,
                    description TEXT,
                    email TEXT,
                    cta_text TEXT,
                    about_title TEXT,
                    about_name TEXT,
                    about_subtitle TEXT,
                    about_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table skills
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    icon TEXT,
                    description TEXT,
                    projects_count INTEGER DEFAULT 0,
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table partners
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image TEXT,
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table projects
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    technologies TEXT,
                    description TEXT,
                    link TEXT,
                    github_link TEXT,
                    image TEXT,
                    additional_images TEXT,
                    status TEXT DEFAULT 'published',
                    order_index INTEGER DEFAULT 0,
                    featured INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Ajouter la colonne additional_images si elle n'existe pas (migration)
            try:
                cursor.execute('ALTER TABLE projects ADD COLUMN additional_images TEXT')
            except sqlite3.OperationalError:
                pass  # La colonne existe déjà
            
            # Table services
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    icon TEXT,
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table contacts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    subject TEXT,
                    message TEXT NOT NULL,
                    read INTEGER DEFAULT 0,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table admin_users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Table login_history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    success INTEGER DEFAULT 1,
                    ip_address TEXT,
                    user_agent TEXT,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    page_path TEXT,
                    project_id INTEGER,
                    visitor_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    referer TEXT,
                    date DATE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Créer les index
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_read ON contacts(read)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS career (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    org TEXT,
                    location TEXT,
                    start TEXT,
                    end TEXT,
                    kind TEXT DEFAULT 'emploi',
                    bullets TEXT,
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            migrate_schema(cursor)
            conn.commit()
            
            init_homepage_data(conn)
            init_skills_data(conn)
            init_partners_data(conn)
            init_career_data(conn)
            init_services_data(conn)
            init_projects_data(conn)
            init_certifications_data(conn)
            init_site_pages_data(conn)
            
            print("Base de donnees SQLite initialisee")
            return True
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de donnees: {e}")
        return False

def _add_column(cursor, table, column, definition):
    try:
        cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
    except sqlite3.OperationalError:
        pass


def migrate_schema(cursor):
    """Ajoute les colonnes manquantes sur une base existante."""
    for col, definition in (
        ('location', 'TEXT'),
        ('availability', 'TEXT'),
        ('cv_path', 'TEXT'),
        ('languages', 'TEXT'),
    ):
        _add_column(cursor, 'homepage', col, definition)

    _add_column(cursor, 'partners', 'period', 'TEXT')
    _add_column(cursor, 'skills', 'label', 'TEXT')

    for col, definition in (
        ('category', "TEXT DEFAULT 'pro'"),
        ('role', 'TEXT'),
        ('context', 'TEXT'),
        ('results', 'TEXT'),
        ('measurement', 'TEXT'),
        ('period', 'TEXT'),
        ('long_description', 'TEXT'),
    ):
        _add_column(cursor, 'projects', col, definition)

    for col, definition in (
        ('problem', 'TEXT'),
        ('deliverables', 'TEXT'),
        ('stack', 'TEXT'),
        ('duration', 'TEXT'),
        ('quote_anchor', 'TEXT'),
        ('status', "TEXT DEFAULT 'archived'"),
    ):
        _add_column(cursor, 'services', col, definition)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            type TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            path TEXT,
            ip_hash TEXT,
            details TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_created ON security_events(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(type)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source TEXT,
            level TEXT,
            message TEXT,
            stack TEXT,
            path TEXT,
            user_agent TEXT,
            resolved INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_logs_created ON error_logs(created_at)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            title TEXT NOT NULL,
            code TEXT UNIQUE,
            url TEXT,
            skill_fr TEXT,
            skill_en TEXT,
            featured INTEGER DEFAULT 0,
            order_index INTEGER DEFAULT 0,
            status TEXT DEFAULT 'published',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_pages (
            slug TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    _add_column(cursor, 'career', 'status', "TEXT DEFAULT 'published'")

    for table in ('projects', 'career', 'certifications', 'skills', 'partners', 'contacts'):
        _add_column(cursor, table, 'deleted_at', 'TEXT')

    for col, definition in (
        ('totp_secret', 'TEXT'),
        ('totp_enabled', 'INTEGER DEFAULT 0'),
        ('backup_codes', 'TEXT'),
    ):
        _add_column(cursor, 'admin_users', col, definition)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            admin_id TEXT,
            action TEXT NOT NULL,
            entity TEXT,
            entity_id TEXT,
            diff TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT,
            path TEXT NOT NULL,
            mime_hint TEXT,
            size INTEGER DEFAULT 0,
            alt_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT
        )
    ''')


def init_certifications_data(conn):
    """Importe les certifications depuis data/certifications.json si la table est vide."""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM certifications')
        if cursor.fetchone()[0] > 0:
            return
        path = os.path.join(os.path.dirname(__file__), 'data', 'certifications.json')
        if not os.path.isfile(path):
            return
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('items') or []
        rows = []
        for i, item in enumerate(items):
            skill = item.get('skill') or {}
            code = item.get('code') or ''
            rows.append((
                item.get('domain'),
                item.get('title'),
                code,
                item.get('url') or f"https://www.coursera.org/account/accomplishments/certificate/{code}",
                skill.get('fr') or '',
                skill.get('en') or '',
                1 if item.get('featured') else 0,
                i + 1,
                'published',
            ))
        cursor.executemany('''
            INSERT INTO certifications
            (domain, title, code, url, skill_fr, skill_en, featured, order_index, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', rows)
        conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur certifications: {e}")


def init_site_pages_data(conn):
    """Pages légales de base (contenu factuel minimal, éditable ensuite)."""
    try:
        cursor = conn.cursor()
        pages = [
            (
                'confidentialite',
                'Politique de confidentialité',
                (
                    "Ce site portfolio collecte des données techniques minimales pour son fonctionnement : "
                    "messages du formulaire de contact (nom, courriel, message) et statistiques d'audience "
                    "basées sur des identifiants dérivés (adresses IP hachées, jamais stockées en clair).\n\n"
                    "Les données de contact servent uniquement à répondre aux messages. "
                    "Les journaux techniques et de sécurité sont conservés pour une durée limitée "
                    "afin d'assurer la disponibilité et la protection du site.\n\n"
                    "Pour toute demande d'accès ou de suppression liée à un message de contact, "
                    "écrivez via le formulaire de contact en précisant votre courriel.\n\n"
                    "Ce texte est une information technique, pas un avis juridique."
                ),
            ),
            (
                'mentions',
                'Mentions légales',
                (
                    "Site personnel de présentation professionnelle de Claude Pricemou, "
                    "développeur Full Stack et science des données, basé à Trois-Rivières (Québec).\n\n"
                    "Contact : via le formulaire du site.\n\n"
                    "Les contenus (textes, projets, image) appartiennent à leur auteur, sauf mention contraire."
                ),
            ),
        ]
        for slug, title, body in pages:
            cursor.execute('SELECT slug FROM site_pages WHERE slug = ?', (slug,))
            if cursor.fetchone():
                continue
            cursor.execute(
                'INSERT INTO site_pages (slug, title, body) VALUES (?, ?, ?)',
                (slug, title, body),
            )
        conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur pages légales: {e}")


HOMEPAGE_SEED = {
                "type": "header",
    "badge": "Ouvert aux opportunités · Trois-Rivières (Québec)",
    "title_line1": "Développeur Full Stack",
    "title_line2": "& science des données.",
    "description": (
        "Je construis des applications web et des modèles de données utiles en production. "
        "Parcours entre produits opérationnels et projets data, à Trois-Rivières. "
        "Français (maternelle), anglais (intermédiaire)."
    ),
    "email": "pricemoufromon97@gmail.com",
    "cta_text": "Me contacter",
                "about_title": "Présentation",
    "about_name": "Claude Pricemou",
    "about_subtitle": "Développeur Full Stack & Science des données, basé à Trois-Rivières.",
    "about_description": (
        "Baccalauréat en informatique (science des données) à l'UQTR ; baccalauréat et BTS en informatique (HEC).\n\n"
        "Certifications : AWS Cloud Practitioner (2024), Azure AI-900 (2024), Big Data (UC San Diego), Power BI.\n\n"
        "Lauréat « Meilleur programmeur » (2020, Champion des Champions, Institut Cerco).\n\n"
        "J'ai contribué à des produits opérationnels (transport, interventions, recyclage, télémédecine, paiement) "
        "et à des analyses de données ouvertes."
    ),
    "location": "Trois-Rivières (Québec)",
    "availability": "Ouvert aux opportunités",
    "cv_path": "docs/cv-claude-pricemou.pdf",
    "languages": "Français (maternelle), anglais (intermédiaire)",
}


def init_homepage_data(conn):
    """Insère l'identité d'accueil si absente ; applique le repositionnement perso si l'ancien ton freelance est encore en base."""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, badge, cta_text, availability, about_subtitle FROM homepage WHERE type = ? LIMIT 1', ('header',))
        row = cursor.fetchone()
        values = (
            HOMEPAGE_SEED['badge'], HOMEPAGE_SEED['title_line1'], HOMEPAGE_SEED['title_line2'],
            HOMEPAGE_SEED['description'], HOMEPAGE_SEED['email'], HOMEPAGE_SEED['cta_text'],
            HOMEPAGE_SEED['about_title'], HOMEPAGE_SEED['about_name'], HOMEPAGE_SEED['about_subtitle'],
            HOMEPAGE_SEED['about_description'], HOMEPAGE_SEED['location'], HOMEPAGE_SEED['availability'],
            HOMEPAGE_SEED['cv_path'], HOMEPAGE_SEED['languages'],
        )
        if not row:
            cursor.execute('''
                INSERT INTO homepage (type, badge, title_line1, title_line2, description, email, cta_text,
                    about_title, about_name, about_subtitle, about_description,
                    location, availability, cv_path, languages)
                VALUES ('header', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
            conn.commit()
            return

        badge = (row['badge'] if isinstance(row, sqlite3.Row) else row[1]) or ''
        cta = (row['cta_text'] if isinstance(row, sqlite3.Row) else row[2]) or ''
        availability = (row['availability'] if isinstance(row, sqlite3.Row) else row[3]) or ''
        about_subtitle = (row['about_subtitle'] if isinstance(row, sqlite3.Row) else row[4]) or ''
        looks_freelance = any(
            'freelance' in (text or '').lower() or 'mandat' in (text or '').lower()
            for text in (badge, cta, availability, about_subtitle)
        )
        if looks_freelance:
            cursor.execute('''
                UPDATE homepage SET badge=?, title_line1=?, title_line2=?, description=?, email=?, cta_text=?,
                    about_title=?, about_name=?, about_subtitle=?, about_description=?,
                    location=?, availability=?, cv_path=?, languages=?, updated_at=CURRENT_TIMESTAMP
                WHERE type='header'
            ''', values)
            conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur homepage: {e}")


def init_skills_data(conn):
    """Compétences par catégorie (sans compteurs fictifs). N'écrase pas une base déjà remplie."""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM skills')
        if cursor.fetchone()[0] > 0:
            return
            default_skills = [
            ("Langages", "icons/code.svg", "Python, JavaScript / TypeScript, SQL.", None, "Cœur du métier", 1),
            ("Frontend", "icons/design.svg", "React, Angular, HTML/CSS accessibles.", None, "Interfaces", 2),
            ("Backend", "icons/code.svg", "Flask, Node.js, NestJS, API REST.", None, "Serveur", 3),
            ("Data", "icons/design.svg", "Power BI, machine learning, données ouvertes canadiennes.", None, "Analyse", 4),
            ("Cloud", "icons/phone.svg", "AWS Cloud Practitioner, Azure AI-900.", None, "Infra", 5),
        ]
            cursor.executemany('''
            INSERT INTO skills (title, icon, description, projects_count, label, order_index)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', default_skills)
            conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur compétences: {e}")


def init_partners_data(conn):
    """Références réelles. N'écrase pas une base déjà remplie."""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM partners')
        if cursor.fetchone()[0] == 0:
            refs = [
                (name, PARTNER_COVERS.get(name, ""), period, idx)
                for idx, (name, period) in enumerate(
                    [
                        ("Marc Worldwide Transport", "depuis mai 2026"),
                        ("Network Pro Service", "2026"),
                        ("RabbyTech (Abidjan)", "2025"),
                        ("Groupe Cerco", "2019–2022"),
                        ("Clean International", "chef d'équipe"),
                        ("AÉI UQTR", "bénévole"),
                    ],
                    start=1,
                )
            ]
            cursor.executemany(
                '''
                INSERT INTO partners (name, image, period, order_index)
                VALUES (?, ?, ?, ?)
                ''',
                refs,
            )
        # Synchroniser les visuels thématiques (Unsplash)
        for name, image in PARTNER_COVERS.items():
            cursor.execute(
                "UPDATE partners SET image = ? WHERE name = ?",
                (image, name),
            )
        conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur références: {e}")


def init_career_data(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM career')
        if cursor.fetchone()[0] > 0:
            return
        items = [
            ("Développeur Full Stack freelance", "Marc Worldwide Transport", "Québec", "2026-05", "", "emploi",
             "Conception et évolution d'un système de gestion de transport (Flask + React).", 1),
            ("Stagiaire développeur", "Network Pro Service", "Québec", "2026-01", "2026-04", "stage",
             "Application de gestion d'interventions : collecte, visibilité opérationnelle, satisfaction terrain.", 2),
            ("Stagiaire analyste / développeur", "RabbyTech", "Abidjan", "2025-01", "2025-12", "stage",
             "Plateforme de recyclage : analyse fonctionnelle, maquettes UX/UI, APIs Angular / NestJS.", 3),
            ("Développeur puis chef d'équipe", "Groupe Cerco", "Afrique de l'Ouest", "2019", "2022", "emploi",
             "Front-end, back-end Python, full stack, puis encadrement. Suite OpenMoise (OpenMedicine, OpenPay, OpenCar).", 4),
            ("Chef d'équipe", "Clean International", "", "", "", "emploi",
             "Coordination d'équipe et livraison des livrables techniques.", 5),
            ("Bénévole", "Association des étudiants en informatique de l'UQTR", "Trois-Rivières", "2024", "", "benevolat",
             "Soutien aux activités étudiantes et partage de pratiques.", 6),
        ]
        cursor.executemany('''
            INSERT INTO career (title, org, location, start, end, kind, bullets, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', items)
        conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur parcours: {e}")


def init_services_data(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM services')
        if cursor.fetchone()[0] > 0:
            cursor.execute('SELECT problem FROM services LIMIT 1')
            row = cursor.fetchone()
            if row and row[0]:
                return
            cursor.execute('DELETE FROM services')
        services = [
            ("Application web sur mesure",
             "Remplacer tableurs et processus cassés par un outil métier fiable.",
             "Cahier des charges, interface, application déployée, documentation.",
             "Flask + React ou NestJS + Angular, PostgreSQL.",
             "4 à 12 semaines",
             "application-web",
             "icons/code.svg",
             "Je conçois une application adaptée à votre opération, du besoin jusqu'au déploiement."),
            ("Automatisation et extraction de données",
             "Éliminer la saisie manuelle répétitive et les exports fragiles.",
             "Scripts, jobs planifiés, exports contrôlés, journal d'exécution.",
             "Python, APIs REST, planificateurs.",
             "1 à 4 semaines",
             "automatisation",
             "icons/phone.svg",
             "J'automatise la collecte et le traitement pour libérer du temps opérationnel."),
            ("Tableaux de bord et analyse",
             "Décider sans visibilité consolidée sur l'activité.",
             "Modèle de données, indicateurs, tableau Power BI ou dashboard web.",
             "SQL, Power BI, Python.",
             "2 à 6 semaines",
             "tableaux-de-bord",
             "icons/design.svg",
             "Je transforme vos données en indicateurs actionnables, avec une méthode de calcul explicite."),
            ("Machine learning",
             "Scorer, prédire ou classer là où une règle fixe ne suffit plus.",
             "Notebook reproductible, modèle, API d'inférence, note de limites.",
             "Python, scikit-learn, Flask.",
             "4 à 10 semaines",
             "machine-learning",
             "icons/design.svg",
             "Je livre un modèle utile en production, avec la méthode de validation."),
            ("API et intégration",
             "Faire communiquer des outils en silo sans casser les contrats.",
             "Contrats API, authentification, documentation, tests d'intégration.",
             "Flask / NestJS, PostgreSQL.",
             "2 à 6 semaines",
             "api-integration",
             "icons/code.svg",
             "J'intègre vos systèmes avec des APIs stables et documentées."),
        ]
        cursor.executemany('''
            INSERT INTO services (title, problem, deliverables, stack, duration, quote_anchor, icon, description, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], i + 1) for i, s in enumerate(services)])
        conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur services: {e}")


TEMPLATE_PROJECT_TITLES = (
    'Plateforme E-commerce',
    'Application de Gestion de Tâches',
    'Dashboard Analytics',
    'Application Mobile Fitness',
    'Système de Réservation',
)

# Couvertures Unsplash (licence Unsplash — https://unsplash.com/license)
COVER_TRANSPORT = "images/projects/marc-transport.jpg"
COVER_INTERVENTIONS = "https://images.unsplash.com/photo-1621905252507-b35492cc74b4?auto=format&fit=crop&w=1400&q=80"
COVER_RECYCLAGE = "https://images.unsplash.com/photo-1642631171488-23d631eba638?auto=format&fit=crop&w=1400&q=80"
COVER_MEDECINE = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=1400&q=80"
COVER_PAIEMENT = "https://images.unsplash.com/photo-1563013544-824ae1b704d3?auto=format&fit=crop&w=1400&q=80"
COVER_VOCAL = "https://images.unsplash.com/photo-1589254065878-42c9da997008?auto=format&fit=crop&w=1400&q=80"
COVER_IMMOBILIER = "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1400&q=80"
COVER_DATA = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1400&q=80"

PARTNER_COVERS = {
    "Marc Worldwide Transport": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=800&q=80",
    "Network Pro Service": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=800&q=80",
    "RabbyTech (Abidjan)": "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
    "Groupe Cerco": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=800&q=80",
    "Clean International": "https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=800&q=80",
    "AÉI UQTR": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=800&q=80",
}

MARC_TRANSPORT_TITLE = "Système de gestion de transport"

MARC_TRANSPORT_PROJECT = {
    "title": MARC_TRANSPORT_TITLE,
    "image": COVER_TRANSPORT,
    "additional_images": "images/projects/marc-transport-gallery-1.jpg, images/projects/marc-transport-gallery-2.jpg, images/projects/marc-transport-gallery-3.jpg",
    "technologies": "Flask, React, MySQL",
    # Carte : aperçu court uniquement
    "description": (
        "J'ai participé au développement d'une solution numérique pour Marc Worldwide Transport. "
        "Cette entreprise propose des services liés à la vente de véhicules et au transport international "
        "entre le Canada et la Côte d'Ivoire. "
        "J'ai contribué à faire passer des opérations manuelles vers un outil qui centralise les informations "
        "et facilite le suivi quotidien des équipes."
    ),
    # Modal « Voir détails » : contenu complet
    "long_description": (
        "J'ai participé au développement d'une solution numérique pour Marc Worldwide Transport. "
        "Cette entreprise propose notamment des services liés à la vente de véhicules et au transport "
        "international entre le Canada et la Côte d'Ivoire. "
        "Le slogan de l'entreprise est « Un étudiant, un véhicule à moindre coût ». "
        "Le site public est accessible sur https://www.marctransport.ca/.\n\n"
        "Le projet visait à faire évoluer une organisation dont les opérations étaient gérées manuellement "
        "vers un environnement numérique. L'objectif était de centraliser les informations, "
        "de mieux suivre les opérations et de faciliter le travail quotidien des équipes.\n\n"
        "Les modules couverts comprenaient : la gestion des véhicules et des commandes ; "
        "le suivi des transports et des livraisons ; la gestion des employés et des livreurs ; "
        "les candidatures ; la paie ; les notifications ; ainsi que des éléments de tableaux de bord et d'historique. "
        "Ma contribution a porté sur les modules du périmètre, y compris les candidatures, la paie et les notifications.\n\n"
        "Ma démarche a suivi ces étapes : comprendre les processus existants et les besoins opérationnels ; "
        "définir les modules à couvrir ; développer les traitements côté serveur avec Flask "
        "(Flask est un cadre Python pour créer des applications web) ; "
        "construire les interfaces avec React (React sert à créer l'interface utilisateur) ; "
        "connecter l'application à MySQL en production (MySQL est la base de données qui stocke les informations) ; "
        "vérifier le fonctionnement des modules ; déployer la solution et accompagner son utilisation.\n\n"
        "Compétences mobilisées : développement d'une application serveur avec Python et Flask ; "
        "développement d'interfaces avec React ; intégration avec une base de données MySQL ; "
        "structuration de modules métier ; participation à la numérisation de processus opérationnels ; "
        "collaboration au sein d'une équipe ; prise en compte de besoins concrets d'une entreprise."
    ),
    "category": "pro",
    "role": "Développeur Full Stack — mandat freelance, travail en équipe",
    "context": (
        "Avant la solution, les processus reposaient surtout sur des opérations manuelles. "
        "Cela rendait plus difficile la centralisation des données, le suivi des dossiers et la coordination des activités."
    ),
    "results": json.dumps([
        "Adoption par les équipes opérationnelles : plus de 90 %",
        "Réduction des erreurs de saisie : 60 %",
        "Amélioration de la vitesse de traitement : 40 %",
        "Réduction des retards : 35 %",
    ], ensure_ascii=False),
    "measurement": (
        "Comparaison avant/après sur 90 jours, à partir des journaux opérationnels et des tickets internes."
    ),
    "period": "depuis 2026",
    "link": "https://www.marctransport.ca/",
    "order_index": 1,
    "featured": 1,
}


NETWORK_PRO_TITLE = "Gestion d'interventions — Network Pro Service"

NETWORK_PRO_PROJECT = {
    "title": NETWORK_PRO_TITLE,
    "image": COVER_INTERVENTIONS,
    "technologies": "React, Node.js, Python, PostgreSQL",
    "description": (
        "Application de suivi des interventions terrain, de la collecte à la clôture. "
        "J'ai contribué à digitaliser la saisie, la visibilité opérationnelle et le suivi "
        "des équipes chez Network Pro Service."
    ),
    "long_description": (
        "Chez Network Pro Service (stage 2026), j'ai contribué à une application de gestion "
        "d'interventions terrain : collecte des données, suivi des dossiers, clôture et "
        "visibilité opérationnelle pour les équipes.\n\n"
        "L'objectif était de remplacer une collecte encore largement manuelle par un outil "
        "qui accélère la saisie, améliore le suivi en temps réel et renforce la satisfaction "
        "des opérateurs sur le terrain."
    ),
    "category": "pro",
    "role": "Stagiaire développeur",
    "context": (
        "Les données d'intervention étaient collectées à la main, avec peu de visibilité temps réel."
    ),
    "results": json.dumps([
        "−80 % de temps de collecte manuelle",
        "+75 % de visibilité opérationnelle",
        "95 % de satisfaction opérateurs",
    ], ensure_ascii=False),
    "measurement": "Temps de saisie chronométré avant/après ; sondage opérateurs en fin de stage.",
    "period": "2026",
    "link": "",
    "order_index": 2,
    "featured": 1,
}


RABBYTECH_TITLE = "Plateforme de recyclage — RabbyTech"

RABBYTECH_PROJECT = {
    "title": RABBYTECH_TITLE,
    "image": COVER_RECYCLAGE,
    "technologies": "React, NestJS, PostgreSQL, Scrum",
    "description": (
        "J'ai participé, au sein de l'équipe de RabbyTech, au développement web d'une plateforme "
        "de recyclage et de redistribution solidaire. Les citoyens déposent des objets recyclables "
        "dans des points agréés, accumulent des points, puis les échangent contre des avantages. "
        "J'ai réalisé 15 fonctionnalités clés et connecté les interfaces React aux API du backend."
    ),
    "long_description": (
        "J'ai participé, au sein de l'équipe de RabbyTech (stage, été 2025), au développement web "
        "d'une plateforme destinée à soutenir le recyclage et la redistribution solidaire. "
        "Le principe était de permettre aux citoyens de déposer des objets recyclables dans des points agréés, "
        "d'accumuler des points, puis d'utiliser ces points pour obtenir des avantages chez des partenaires.\n\n"
        "L'organisation partenaire recevait des dons et souhaitait les redistribuer de façon structurée. "
        "La plateforme devait relier les actions de recyclage aux avantages, tout en contrôlant "
        "l'utilisation des produits et des réductions dans les commerces agréés.\n\n"
        "J'ai réalisé 15 fonctionnalités : géolocalisation des points de dépôt ; "
        "scan automatique des objets recyclés (QR, code-barres, IA photo) ; "
        "catalogue des récompenses ; gestion des stocks partenaires ; "
        "rôles et permissions ; tableau de bord analytique ; campagnes de recyclage ; "
        "historique des dépôts et transactions ; notifications ; messagerie interne ; "
        "gamification (badges, niveaux, défis) ; carte thermique des dépôts ; "
        "vérification anti-fraude ; certificats écologiques ; mode hors-ligne pour les agents de collecte. "
        "J'ai aussi intégré les interfaces de gestion des utilisateurs et d'administration, "
        "ainsi que les écrans de suivi des points et de redistribution des avantages.\n\n"
        "Ma démarche : prendre connaissance du cahier des charges ; comprendre les maquettes web ; "
        "intégrer les interfaces avec React (React sert à construire l'interface utilisateur) ; "
        "connecter les écrans aux API du backend NestJS "
        "(une API permet à l'interface et au serveur d'échanger des données) ; "
        "participer à la recette et aux corrections, notamment sur la cohérence entre les interfaces "
        "et les contrats d'API. Le travail s'est fait en équipe selon Scrum "
        "(méthode organisée en cycles courts appelés sprints), avec suivi dans Jira.\n\n"
        "Architecture : interface web en React, backend en NestJS, données en PostgreSQL. "
        "Ma contribution décrite ici concerne la partie web ; le projet comportait aussi une partie mobile prise en charge par l'équipe.\n\n"
        "Compétences mobilisées : développement d'interfaces avec React ; intégration d'API ; "
        "compréhension d'une architecture frontend/backend ; intégration de modules métier ; "
        "sécurité et fiabilité (rôles, anti-fraude, hors-ligne) ; vérification en recette ; "
        "travail agile en équipe ; compréhension d'un besoin métier de recyclage et de redistribution."
    ),
    "category": "pro",
    "role": "Stagiaire en développement web — travail en équipe",
    "context": (
        "L'organisation partenaire devait structurer la redistribution de dons via un système de points "
        "lié au recyclage. Les intégrations API généraient aussi des écarts de contrat et des bugs bloquants en recette."
    ),
    "results": json.dumps([
        "Réduction des erreurs d'intégration API : 70 %",
        "Réduction des bugs critiques : 45 %",
    ], ensure_ascii=False),
    "measurement": (
        "Tickets Jira comparés sur deux sprints de recette, avant et après la mise en place "
        "des maquettes et des contrats d'API."
    ),
    "period": "été 2025",
    "link": "",
    "order_index": 3,
    "featured": 1,
}


def _upsert_featured_project(cursor, project):
    """Met à jour une entrée projet existante (pas de doublon)."""
    cursor.execute("SELECT id FROM projects WHERE title = ?", (project["title"],))
    row = cursor.fetchone()
    if not row:
        return False
    cursor.execute(
        '''
        UPDATE projects
        SET technologies=?, description=?, long_description=?, category=?, role=?, context=?, results=?,
            measurement=?, period=?, link=?, image=?, additional_images=?, featured=?, order_index=?,
            status='published', updated_at=CURRENT_TIMESTAMP
        WHERE title=?
        ''',
        (
            project["technologies"],
            project["description"],
            project["long_description"],
            project["category"],
            project["role"],
            project["context"],
            project["results"],
            project["measurement"],
            project["period"],
            project.get("link") or None,
            project.get("image") or None,
            project.get("additional_images") or "",
            project["featured"],
            project["order_index"],
            project["title"],
        ),
    )
    return True


OPENMEDICINE_OLD_TITLE = "OpenMoise — Groupe Cerco"

OPENMEDICINE_PROJECT = {
    "title": "OpenMedicine — Groupe Cerco",
    "image": COVER_MEDECINE,
    "technologies": "Python, React, API",
    "description": (
        "J'ai contribué au développement web d'OpenMedicine, une plateforme de télémédecine "
        "et de coordination des soins au Groupe Cerco, pendant la période de la COVID-19. "
        "J'ai intégré les maquettes avec React, connecté les interfaces aux API du backend "
        "et participé à certains travaux liés à l'authentification et à la conception des API."
    ),
    "long_description": (
        "OpenMedicine est une solution médicale destinée à faciliter les consultations à distance "
        "et en présentiel, le suivi des patients et la coordination des soins. "
        "Le projet s'inscrivait dans le contexte de la pandémie de COVID-19. "
        "J'ai travaillé au Groupe Cerco (2019–2022) au sein d'une équipe répartie entre "
        "une application mobile, une application web et un backend partagé.\n\n"
        "Les objectifs étaient de faciliter l'organisation des consultations à distance et en présentiel, "
        "de centraliser les dossiers des patients, de soutenir le suivi des patients atteints de la COVID-19, "
        "et de permettre aux professionnels de consulter les informations nécessaires au suivi. "
        "Les fonctionnalités couvertes comprenaient la gestion des dossiers patients, "
        "les rendez-vous à distance et en présentiel, les consultations vidéo, "
        "le suivi lié à la COVID-19, la gestion des contacts entre patients, les ordonnances, "
        "ainsi que l'authentification et les échanges avec le backend.\n\n"
        "Ma démarche : comprendre les besoins et les maquettes ; intégrer les interfaces avec React "
        "(React sert à construire l'interface utilisateur) ; connecter les écrans aux API "
        "(une API définit comment l'interface communique avec le serveur) ; "
        "participer à certains travaux backend en Python autour de la conception des API et de l'authentification "
        "(l'authentification vérifie l'identité d'un utilisateur avant l'accès aux fonctionnalités) ; "
        "vérifier la conformité visuelle et fonctionnelle, puis participer au suivi des bugs.\n\n"
        "Ma contribution concernait principalement l'application web. "
        "Je n'ai pas développé seul l'ensemble de la plateforme mobile, web et backend. "
        "Pour une partie de la période, des responsabilités de coordination d'équipe m'ont aussi été confiées.\n\n"
        "Compétences mobilisées : développement frontend avec React ; intégration d'API ; "
        "participation au backend Python ; authentification ; vérification fonctionnelle ; "
        "intégration UX/UI ; travail en équipe sur une application à plusieurs composantes ; "
        "compréhension des besoins liés aux consultations et au suivi des patients."
    ),
    "category": "pro",
    "role": "Développeur Full Stack — coordination d'équipe pour une partie de la période",
    "context": (
        "Pendant la COVID-19, les équipes de soins avaient besoin d'organiser des consultations "
        "à distance ou en présentiel, tout en centralisant le suivi des patients."
    ),
    "results": json.dumps([
        "Interfaces web intégrées à partir des maquettes",
        "Connexion des écrans aux API du backend",
        "Participation à l'authentification et à la conception des API",
    ], ensure_ascii=False),
    "measurement": (
        "Résultat fonctionnel : contribution à l'intégration web et aux échanges avec le backend, "
        "sans indicateurs chiffrés non vérifiés."
    ),
    "period": "2019–2022",
    "link": "",
    "order_index": 4,
    "featured": 1,
}


OPENPAY_PROJECT = {
    "title": "OpenPay — Groupe Cerco",
    "image": COVER_PAIEMENT,
    "technologies": "Python, React, API REST",
    "description": (
        "J'ai participé au développement full stack d'OpenPay, une plateforme de paiement numérique "
        "au Groupe Cerco (2019–2022). J'ai développé des interfaces React, des services backend en Python, "
        "intégré les maquettes, conçu des API et contribué aux fonctionnalités de transfert "
        "et de suivi des transactions."
    ),
    "long_description": (
        "OpenPay est une plateforme de paiement numérique développée au Groupe Cerco entre 2019 et 2022, "
        "conçue pour faciliter les transferts d'argent, les opérations de paiement et la gestion "
        "des transactions numériques. Le projet combinait une interface web moderne avec des services "
        "backend pour gérer les utilisateurs, les opérations financières et le suivi des transactions.\n\n"
        "Mon rôle était développeur Full Stack : j'ai intervenu sur le frontend et le backend, "
        "de la conception de l'architecture jusqu'à l'intégration des interfaces et au développement "
        "des fonctionnalités métier.\n\n"
        "Fonctionnalités principales : transfert d'argent (identification du destinataire, initiation, "
        "validation, suivi et historique) ; paiement numérique via un portefeuille utilisateur "
        "(opérations, solde, frais, confirmation) ; paiement par QR code pour simplifier le parcours ; "
        "intégration prévue avec des services Mobile Money pour dépôt et retrait "
        "(opérateurs exacts à confirmer dans le code source) ; retrait et dépôt de proximité "
        "(recherche d'un intervenant, localisation, demande, confirmation et suivi).\n\n"
        "Architecture simplifiée : utilisateur → React (frontend) → API / HTTP → Python (backend) → "
        "logique métier, transactions et gestion des données.\n\n"
        "Ma démarche : intégrer les maquettes en composants React réutilisables "
        "(React sert à construire l'interface utilisateur) ; connecter les écrans aux API REST "
        "(une API REST permet à l'interface et au serveur d'échanger des données via HTTP) ; "
        "développer la logique métier et les services backend en Python ; gérer les données "
        "utilisateurs et transactions, valider les opérations et traiter les erreurs ; "
        "participer aux tests, au débogage et à la correction des anomalies.\n\n"
        "Compétences mobilisées : développement full stack React / Python ; architecture applicative ; "
        "conception et intégration d'API ; intégration UI à partir de maquettes ; "
        "logique métier liée aux paiements et transactions ; débogage et maintenance."
    ),
    "category": "pro",
    "role": "Développeur Full Stack",
    "context": (
        "Le projet visait à faciliter les transferts d'argent et les paiements numériques "
        "via une interface web reliée à des services backend."
    ),
    "results": json.dumps([
        "Fonctionnalités frontend React et backend Python développées",
        "Maquettes intégrées et connectées aux API",
        "Participation à l'architecture et aux parcours de transfert / transactions",
    ], ensure_ascii=False),
    "measurement": (
        "Résultat fonctionnel : contribution full stack de bout en bout "
        "(maquettes → React → API → Python → logique métier), sans indicateurs chiffrés non vérifiés."
    ),
    "period": "2019–2022",
    "link": "",
    "order_index": 5,
    "featured": 1,
}


VOCAL_ASSISTANT_LEGACY_TITLES = (
    "Reconnaissance vocale en langues locales",
    "Assistant vocal IA — Langues locales",
    "Assistant vocal IA — langues locales",
)

VOCAL_ASSISTANT_PROJECT = {
    "title": "Assistant vocal IA — langues locales (Groupe Cerco)",
    "image": COVER_VOCAL,
    "technologies": "Python, Rasa, NLU, NLP",
    "description": (
        "Chez Groupe Cerco, j'ai participé au développement d'un assistant vocal pour une marketplace "
        "en Côte d'Ivoire, destiné aux personnes qui ne savent ni lire ni écrire. "
        "Avec Python et Rasa, j'ai travaillé sur la compréhension du langage naturel (NLU) "
        "afin qu'elles puissent commander et acheter uniquement par la voix, dans leur langue locale."
    ),
    "long_description": (
        "Dans le cadre d'un projet d'intelligence artificielle mené chez Groupe Cerco (2019–2022), "
        "j'ai participé au développement d'un assistant vocal intégré à une marketplace, "
        "destiné en priorité aux personnes qui ne savent ni lire ni écrire. "
        "L'objectif était de leur permettre d'interagir par la voix dans leur langue locale : "
        "l'utilisateur parle, des modèles de machine learning convertissent sa parole en langage naturel "
        "(français ou anglais, selon l'option choisie), puis l'assistant comprend sa demande "
        "pour l'aider à naviguer, commander et valider ses achats sans aucune saisie écrite.\n\n"
        "Mon rôle était développeur IA / NLU (Python & Rasa). "
        "Je n'ai pas développé l'ensemble de la marketplace : mon travail portait sur le module "
        "de chatbot vocal et de compréhension du langage naturel — "
        "définition des intentions, extraction des informations importantes, préparation des données "
        "d'entraînement, mise en place du modèle adapté aux langues locales, intégration dans "
        "l'application, tests et amélioration des réponses.\n\n"
        "Parcours : l'utilisateur active le bouton vocal et parle dans sa langue locale ; "
        "la voix est convertie en langage naturel (français ou anglais) par les modèles "
        "de machine learning ; le module NLU (Python + Rasa) identifie l'intention et extrait "
        "les entités ; la demande est ensuite traitée par la marketplace "
        "(recherche, commande, validation de l'achat). "
        "(NLU signifie compréhension du langage naturel : le système détermine ce que l'utilisateur "
        "veut faire et quelles informations sont présentes dans sa phrase.)\n\n"
        "Exemples d'intentions (après conversion en français) : "
        "« Je veux acheter du riz » → acheter_produit (produit = riz) ; "
        "« Trouve-moi un vendeur de maïs » → recherche_produit ; "
        "« Combien coûte le transport ? » → demande_information. "
        "Exemple d'entités : « Je veux acheter 5 sacs de riz à Abidjan » → "
        "quantité = 5, produit = riz, lieu = Abidjan.\n\n"
        "Le projet a pris en charge une quinzaine de langues locales de Côte d'Ivoire, "
        "avec variations de formulation et expressions locales. "
        "Le cycle de travail allait de l'annotation des données à l'entraînement, "
        "aux tests, à la correction des erreurs et au réentraînement.\n\n"
        "Architecture : utilisateur (voix, langue locale) → interface vocale marketplace → "
        "conversion en français/anglais (modèles de machine learning) → Rasa NLU "
        "(détection d'intention et reconnaissance d'entités) → logique métier Python → "
        "actions / services de la marketplace.\n\n"
        "Compétences mobilisées : machine learning, NLP / NLU, classification d'intentions, "
        "reconnaissance d'entités, préparation de données linguistiques, Python, Rasa, "
        "intégration d'un service intelligent dans une application existante."
    ),
    "category": "data",
    "role": "Développeur IA / NLU — Python & Rasa",
    "context": (
        "En Côte d'Ivoire, une partie de la population ne sait ni lire ni écrire, "
        "ou maîtrise mal le français. Les assistants généralistes comprenaient mal "
        "les langues locales, et ces personnes étaient exclues de la marketplace. "
        "Elles avaient besoin d'interagir uniquement par la voix, dans leur propre langue, "
        "pour comprendre la marketplace, commander et faire leurs achats."
    ),
    "results": json.dumps([
        "Chatbot vocal intégré à une marketplace, rendant les achats accessibles "
        "aux personnes qui ne savent ni lire ni écrire",
        "Modèle adapté à une quinzaine de langues locales de Côte d'Ivoire",
        "Intentions et entités métier définies, entraînées et testées, "
        "avec un bon fonctionnement constaté à l'évaluation manuelle",
    ], ensure_ascii=False),
    "measurement": (
        "Évaluation manuelle des intentions et des entités sur des formulations variées ; "
        "cycles d'amélioration à partir des erreurs observées. "
        "Pas de métriques accuracy / F1 publiées sans résultats d'évaluation vérifiés."
    ),
    "period": "2019–2022",
    "link": "",
    "order_index": 6,
    "featured": 1,
}


IMMOBILIER_QC_PROJECT = {
    "title": "Analyse & modélisation prédictive du marché immobilier québécois",
    "image": COVER_IMMOBILIER,
    "technologies": "Data Science, Machine Learning, Séries temporelles, Random Forest",
    "description": (
        "J'ai développé un projet de Data Science sur les données foncières officielles du Québec "
        "afin de prédire le volume mensuel de transactions immobilières. "
        "Le travail couvre le nettoyage des données, la création de 35 variables explicatives, "
        "l'entraînement d'une forêt aléatoire (Random Forest) et l'évaluation chronologique "
        "sans fuite temporelle."
    ),
    "long_description": (
        "J'ai développé un projet complet de Data Science exploitant les données foncières officielles "
        "du Ministère des Ressources naturelles et des Forêts : les Statistiques du Registre foncier "
        "du Québec (Données Québec, licence CC-BY 4.0). Mon travail couvre toute la chaîne : "
        "nettoyage et validation des données, création des variables, modélisation et évaluation.\n\n"
        "Parcours : les données brutes sont nettoyées et validées "
        "(récolement exact avec la source officielle : 12 266 ventes pour août 2026) ; "
        "35 variables explicatives sont créées (retards de 1 à 12 mois, moyennes mobiles, "
        "transformations trigonométriques du mois) pour capter l'inertie et la saisonnalité "
        "sans fuite temporelle ; le modèle est entraîné avec un découpage chronologique strict "
        "(TimeSeriesSplit) ; la forêt aléatoire (Random Forest) est comparée à la méthode de persistance.\n\n"
        "Chiffres clés : 1,05 million de transactions analysées sur 68 mois ; "
        "16 régions administratives et 3 tranches de prix ; "
        "38 % du volume global dans la tranche 250 k$ – 500 k$ ; "
        "top 3 des régions en volume : Montérégie, Montréal et Laurentides.\n\n"
        "Perspectives : l'ajout de variables exogènes (comme le taux directeur, "
        "utilisé avec des valeurs retardées) pourrait permettre d'étendre les prédictions "
        "à un horizon de 3 à 6 mois.\n\n"
        "Architecture : Registre foncier du Québec (données ouvertes) → nettoyage et validation → "
        "feature engineering (35 variables) → découpage chronologique (TimeSeriesSplit) → "
        "Random Forest → prédiction du volume mensuel à 1 mois, par région et par catégorie de prix.\n\n"
        "Compétences mobilisées : analyse de données, nettoyage et validation de données, "
        "feature engineering, séries temporelles, validation chronologique, Random Forest, "
        "évaluation de modèles (MAE, R²), communication de résultats."
    ),
    "category": "data",
    "role": "Data Scientist — analyse de données et modélisation prédictive",
    "context": (
        "Comment anticiper l'évolution des transactions immobilières au Québec ? "
        "Le marché varie selon les régions, les tranches de prix et les saisons, "
        "et il est difficile de prévoir le volume de ventes à court terme. "
        "Le projet visait à construire un modèle capable de prédire le volume mensuel "
        "de transactions à partir des données foncières officielles."
    ),
    "results": json.dumps([
        "Modèle prédictif du volume mensuel de ventes à 1 mois d'échéance, "
        "par région et par catégorie de prix",
        "Réduction de l'erreur de 55,8 % par rapport à la persistance "
        "(MAE de 40,5 contre 91,6)",
        "Coefficient de détermination R² = 0,951 sur le jeu de test",
    ], ensure_ascii=False),
    "measurement": (
        "Évaluation sur un jeu de test chronologique (TimeSeriesSplit, sans fuite temporelle) ; "
        "comparaison à la méthode de persistance avec la MAE et le R². "
        "Récolement exact des totaux avec la source officielle."
    ),
    "period": "données 2021–2026 (janvier 2021 à août 2026)",
    "link": "",
    "order_index": 7,
    "featured": 1,
}


DEPRESSION_PROJECT = {
    "title": "Prédiction de la dépression étudiante",
    "image": COVER_DATA,
    "technologies": "Python, scikit-learn, Machine Learning, analyse de données",
    "description": (
        "Projet académique à l'UQTR : j'ai exploré et modélisé un jeu de données d'enquête "
        "auprès d'étudiants (Kaggle) pour identifier les facteurs de risque associés "
        "à la dépression en milieu scolaire, avec scikit-learn et validation croisée."
    ),
    "long_description": (
        "J'ai réalisé un projet complet d'analyse et de modélisation sur un jeu de données "
        "d'enquête auprès d'étudiants, récupéré sur Kaggle. Mon travail a consisté à explorer "
        "et préparer les données, puis à construire un modèle exploratoire pour identifier "
        "les facteurs de risque associés à la dépression en milieu scolaire, "
        "et à interpréter les résultats pour dégager les facteurs les plus liés.\n\n"
        "Parcours : les données d'enquête sont explorées et nettoyées ; "
        "les variables liées au milieu scolaire et au profil des étudiants sont analysées ; "
        "un modèle de classification est entraîné avec scikit-learn ; "
        "il est validé par validation croisée, puis évalué sur un jeu de test tenu à l'écart "
        "de l'entraînement ; les facteurs les plus associés à la dépression sont ensuite "
        "identifiés et interprétés.\n\n"
        "Architecture : données Kaggle (enquête auprès d'étudiants) → exploration et nettoyage → "
        "préparation des variables → modèle scikit-learn → validation croisée → "
        "évaluation sur jeu de test (F1 / AUC) → identification des facteurs de risque.\n\n"
        "Compétences mobilisées : analyse exploratoire de données, nettoyage et préparation "
        "de données, classification, validation croisée, évaluation de modèles (F1, AUC), "
        "interprétation des variables, Python, scikit-learn."
    ),
    "category": "academic",
    "role": "Analyste / data scientist",
    "context": (
        "Projet académique réalisé à l'UQTR. La dépression en milieu scolaire est un enjeu "
        "important, et les données d'enquête contiennent des signaux qu'il faut apprendre à lire. "
        "L'objectif était de déterminer quels facteurs sont liés au taux de dépression chez "
        "les étudiants, afin de mieux comprendre ce qui l'explique en milieu scolaire."
    ),
    "results": json.dumps([
        "Modèle exploratoire identifiant les facteurs de risque associés "
        "à la dépression chez les étudiants",
        "Modèle validé en validation croisée",
        "Facteurs liés à la dépression en milieu scolaire dégagés et interprétés",
    ], ensure_ascii=False),
    "measurement": (
        "Métrique F1 / AUC sur jeu de test tenu à l'écart de l'entraînement, "
        "en complément de la validation croisée."
    ),
    "period": "projet académique, UQTR",
    "link": "",
    "order_index": 8,
    "featured": 0,
}


def _upsert_marc_transport_project(cursor):
    return _upsert_featured_project(cursor, MARC_TRANSPORT_PROJECT)


def _upsert_rabbytech_project(cursor):
    return _upsert_featured_project(cursor, RABBYTECH_PROJECT)


def _upsert_openmedicine_project(cursor):
    """Met à jour OpenMedicine (anciennement OpenMoise) sans créer de doublon."""
    p = OPENMEDICINE_PROJECT
    cursor.execute(
        "SELECT id FROM projects WHERE title = ? OR title = ?",
        (p["title"], OPENMEDICINE_OLD_TITLE),
    )
    row = cursor.fetchone()
    if not row:
        return False
    project_id = row[0]
    cursor.execute(
        '''
        UPDATE projects
        SET title=?, technologies=?, description=?, long_description=?, category=?, role=?, context=?,
            results=?, measurement=?, period=?, link=?, image=?, featured=?, order_index=?,
            status='published', updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        ''',
        (
            p["title"],
            p["technologies"],
            p["description"],
            p["long_description"],
            p["category"],
            p["role"],
            p["context"],
            p["results"],
            p["measurement"],
            p["period"],
            p.get("link") or None,
            p.get("image") or None,
            p["featured"],
            p["order_index"],
            project_id,
        ),
    )
    return True


def _ensure_featured_project(cursor, project):
    """Met à jour un projet enrichi, ou l'insère s'il n'existe pas encore."""
    if _upsert_featured_project(cursor, project):
        return True
    cursor.execute(
        '''
        INSERT INTO projects (
            title, technologies, description, long_description, category, role, context,
            results, measurement, period, link, image, additional_images, order_index, featured, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published')
        ''',
        (
            project["title"],
            project["technologies"],
            project["description"],
            project["long_description"],
            project["category"],
            project["role"],
            project["context"],
            project["results"],
            project["measurement"],
            project["period"],
            project.get("link") or None,
            project.get("image") or None,
            project.get("additional_images") or "",
            project["order_index"],
            project["featured"],
        ),
    )
    return True


def _upsert_network_pro_project(cursor):
    return _ensure_featured_project(cursor, NETWORK_PRO_PROJECT)


def _upsert_openpay_project(cursor):
    return _ensure_featured_project(cursor, OPENPAY_PROJECT)


def _upsert_vocal_assistant_project(cursor):
    """Met à jour l'assistant vocal (anciens titres inclus) sans doublon."""
    p = VOCAL_ASSISTANT_PROJECT
    titles = (p["title"],) + VOCAL_ASSISTANT_LEGACY_TITLES
    placeholders = ",".join("?" for _ in titles)
    cursor.execute(
        f"SELECT id FROM projects WHERE title IN ({placeholders}) ORDER BY id ASC",
        titles,
    )
    rows = cursor.fetchall()
    if not rows:
        return _ensure_featured_project(cursor, p)
    project_id = rows[0][0]
    # Archiver d'éventuels doublons créés par un ancien upsert
    for extra in rows[1:]:
        cursor.execute(
            "UPDATE projects SET status='archived', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (extra[0],),
        )
    cursor.execute(
        '''
        UPDATE projects
        SET title=?, technologies=?, description=?, long_description=?, category=?, role=?, context=?,
            results=?, measurement=?, period=?, link=?, image=?, featured=?, order_index=?,
            status='published', updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        ''',
        (
            p["title"],
            p["technologies"],
            p["description"],
            p["long_description"],
            p["category"],
            p["role"],
            p["context"],
            p["results"],
            p["measurement"],
            p["period"],
            p.get("link") or None,
            p.get("image") or None,
            p["featured"],
            p["order_index"],
            project_id,
        ),
    )
    return True


def _upsert_immobilier_qc_project(cursor):
    return _ensure_featured_project(cursor, IMMOBILIER_QC_PROJECT)


def _upsert_depression_project(cursor):
    return _ensure_featured_project(cursor, DEPRESSION_PROJECT)


def _refresh_enriched_projects(cursor):
    """Met à jour tous les projets enrichis (textes + couvertures)."""
    _upsert_marc_transport_project(cursor)
    _upsert_network_pro_project(cursor)
    _upsert_rabbytech_project(cursor)
    _upsert_openmedicine_project(cursor)
    _upsert_openpay_project(cursor)
    _upsert_vocal_assistant_project(cursor)
    _upsert_immobilier_qc_project(cursor)
    _upsert_depression_project(cursor)


def init_projects_data(conn):
    try:
        cursor = conn.cursor()
        for title in TEMPLATE_PROJECT_TITLES:
            cursor.execute(
                "UPDATE projects SET status='archived', deleted_at=COALESCE(deleted_at, CURRENT_TIMESTAMP) WHERE title = ?",
                (title,),
            )

        # Rafraîchir les projets enrichis s'ils existent déjà
        marc_ok = _upsert_marc_transport_project(cursor)
        _refresh_enriched_projects(cursor)
        if marc_ok:
            conn.commit()
            return

        projects = [
            (MARC_TRANSPORT_PROJECT["title"], MARC_TRANSPORT_PROJECT["technologies"],
             MARC_TRANSPORT_PROJECT["description"],
             MARC_TRANSPORT_PROJECT["category"], MARC_TRANSPORT_PROJECT["role"],
             MARC_TRANSPORT_PROJECT["context"],
             MARC_TRANSPORT_PROJECT["results"],
             MARC_TRANSPORT_PROJECT["measurement"],
             MARC_TRANSPORT_PROJECT["period"], MARC_TRANSPORT_PROJECT["order_index"],
             MARC_TRANSPORT_PROJECT["featured"]),
            (NETWORK_PRO_PROJECT["title"], NETWORK_PRO_PROJECT["technologies"],
             NETWORK_PRO_PROJECT["description"],
             NETWORK_PRO_PROJECT["category"], NETWORK_PRO_PROJECT["role"],
             NETWORK_PRO_PROJECT["context"],
             NETWORK_PRO_PROJECT["results"],
             NETWORK_PRO_PROJECT["measurement"],
             NETWORK_PRO_PROJECT["period"], NETWORK_PRO_PROJECT["order_index"],
             NETWORK_PRO_PROJECT["featured"]),
            (RABBYTECH_PROJECT["title"], RABBYTECH_PROJECT["technologies"],
             RABBYTECH_PROJECT["description"],
             RABBYTECH_PROJECT["category"], RABBYTECH_PROJECT["role"],
             RABBYTECH_PROJECT["context"],
             RABBYTECH_PROJECT["results"],
             RABBYTECH_PROJECT["measurement"],
             RABBYTECH_PROJECT["period"], RABBYTECH_PROJECT["order_index"],
             RABBYTECH_PROJECT["featured"]),
            (OPENMEDICINE_PROJECT["title"], OPENMEDICINE_PROJECT["technologies"],
             OPENMEDICINE_PROJECT["description"],
             OPENMEDICINE_PROJECT["category"], OPENMEDICINE_PROJECT["role"],
             OPENMEDICINE_PROJECT["context"],
             OPENMEDICINE_PROJECT["results"],
             OPENMEDICINE_PROJECT["measurement"],
             OPENMEDICINE_PROJECT["period"], OPENMEDICINE_PROJECT["order_index"],
             OPENMEDICINE_PROJECT["featured"]),
            (OPENPAY_PROJECT["title"], OPENPAY_PROJECT["technologies"],
             OPENPAY_PROJECT["description"],
             OPENPAY_PROJECT["category"], OPENPAY_PROJECT["role"],
             OPENPAY_PROJECT["context"],
             OPENPAY_PROJECT["results"],
             OPENPAY_PROJECT["measurement"],
             OPENPAY_PROJECT["period"], OPENPAY_PROJECT["order_index"],
             OPENPAY_PROJECT["featured"]),
            (VOCAL_ASSISTANT_PROJECT["title"], VOCAL_ASSISTANT_PROJECT["technologies"],
             VOCAL_ASSISTANT_PROJECT["description"],
             VOCAL_ASSISTANT_PROJECT["category"], VOCAL_ASSISTANT_PROJECT["role"],
             VOCAL_ASSISTANT_PROJECT["context"],
             VOCAL_ASSISTANT_PROJECT["results"],
             VOCAL_ASSISTANT_PROJECT["measurement"],
             VOCAL_ASSISTANT_PROJECT["period"], VOCAL_ASSISTANT_PROJECT["order_index"],
             VOCAL_ASSISTANT_PROJECT["featured"]),
            (IMMOBILIER_QC_PROJECT["title"], IMMOBILIER_QC_PROJECT["technologies"],
             IMMOBILIER_QC_PROJECT["description"],
             IMMOBILIER_QC_PROJECT["category"], IMMOBILIER_QC_PROJECT["role"],
             IMMOBILIER_QC_PROJECT["context"],
             IMMOBILIER_QC_PROJECT["results"],
             IMMOBILIER_QC_PROJECT["measurement"],
             IMMOBILIER_QC_PROJECT["period"], IMMOBILIER_QC_PROJECT["order_index"],
             IMMOBILIER_QC_PROJECT["featured"]),
            (DEPRESSION_PROJECT["title"], DEPRESSION_PROJECT["technologies"],
             DEPRESSION_PROJECT["description"],
             DEPRESSION_PROJECT["category"], DEPRESSION_PROJECT["role"],
             DEPRESSION_PROJECT["context"],
             DEPRESSION_PROJECT["results"],
             DEPRESSION_PROJECT["measurement"],
             DEPRESSION_PROJECT["period"], DEPRESSION_PROJECT["order_index"],
             DEPRESSION_PROJECT["featured"]),
            ("Série LinkedIn — données ouvertes canadiennes", "Python, données ouvertes, visualisation",
             "Analyses publiées à partir de jeux de données ouvertes canadiennes.",
             "data", "Auteur / analyste",
             "Rendre lisibles des jeux publics pour un public non spécialiste.",
             json.dumps([
                 "Publications régulières à partir de sources officielles",
             ], ensure_ascii=False),
             "Chaque figure cite la source ouverte et la date d'extraction.",
             "2024–2026", 9, 0),
        ]
        cursor.executemany('''
            INSERT INTO projects (title, technologies, description, category, role, context, results,
                measurement, period, order_index, featured, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published')
        ''', projects)
        _refresh_enriched_projects(cursor)
        conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur projets: {e}")

def row_to_dict(row):
    """Convertit une ligne SQLite en dictionnaire"""
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows):
    """Convertit plusieurs lignes SQLite en liste de dictionnaires"""
    return [dict(row) for row in rows]
