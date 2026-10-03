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
    ):
        _add_column(cursor, 'projects', col, definition)

    for col, definition in (
        ('problem', 'TEXT'),
        ('deliverables', 'TEXT'),
        ('stack', 'TEXT'),
        ('duration', 'TEXT'),
        ('quote_anchor', 'TEXT'),
    ):
        _add_column(cursor, 'services', col, definition)


HOMEPAGE_SEED = {
    "type": "header",
    "badge": "Disponible en freelance · Trois-Rivières (Québec)",
    "title_line1": "Du besoin métier",
    "title_line2": "au produit et à la donnée.",
    "description": "Je conçois des applications web et des analyses de données pour des équipes qui doivent livrer vite, sans perdre le contrôle opérationnel. Français (maternelle), anglais (intermédiaire).",
    "email": "pricemoufromon97@gmail.com",
    "cta_text": "Discutons d'un mandat",
    "about_title": "Présentation",
    "about_name": "Claude Pricemou",
    "about_subtitle": "Développeur Full Stack & Science des données, freelance à Trois-Rivières.",
    "about_description": (
        "Baccalauréat en informatique (science des données) à l'UQTR ; baccalauréat et BTS en informatique (HEC).\n\n"
        "Certifications : AWS Cloud Practitioner (2024), Azure AI-900 (2024), Big Data (UC San Diego), Power BI.\n\n"
        "Lauréat « Meilleur programmeur » (2020, Champion des Champions, Institut Cerco).\n\n"
        "J'interviens sur des produits opérationnels (transport, interventions, recyclage) et sur des analyses de données ouvertes."
    ),
    "location": "Trois-Rivières (Québec)",
    "availability": "Disponible en freelance",
    "cv_path": "docs/cv-claude-pricemou.pdf",
    "languages": "Français (maternelle), anglais (intermédiaire)",
}


def init_homepage_data(conn):
    """Crée ou met à jour l'identité de la page d'accueil."""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM homepage WHERE type = ? LIMIT 1', ('header',))
        row = cursor.fetchone()
        values = (
            HOMEPAGE_SEED['badge'], HOMEPAGE_SEED['title_line1'], HOMEPAGE_SEED['title_line2'],
            HOMEPAGE_SEED['description'], HOMEPAGE_SEED['email'], HOMEPAGE_SEED['cta_text'],
            HOMEPAGE_SEED['about_title'], HOMEPAGE_SEED['about_name'], HOMEPAGE_SEED['about_subtitle'],
            HOMEPAGE_SEED['about_description'], HOMEPAGE_SEED['location'], HOMEPAGE_SEED['availability'],
            HOMEPAGE_SEED['cv_path'], HOMEPAGE_SEED['languages'],
        )
        if row:
            cursor.execute('''
                UPDATE homepage SET badge=?, title_line1=?, title_line2=?, description=?, email=?, cta_text=?,
                    about_title=?, about_name=?, about_subtitle=?, about_description=?,
                    location=?, availability=?, cv_path=?, languages=?, updated_at=CURRENT_TIMESTAMP
                WHERE type='header'
            ''', values)
        else:
            cursor.execute('''
                INSERT INTO homepage (type, badge, title_line1, title_line2, description, email, cta_text,
                    about_title, about_name, about_subtitle, about_description,
                    location, availability, cv_path, languages)
                VALUES ('header', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
        conn.commit()
    except Exception as e:
        print(f"⚠️  Erreur homepage: {e}")


def init_skills_data(conn):
    """Compétences par catégorie (sans compteurs fictifs)."""
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM skills')
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
    """Références réelles (plus de logos template)."""
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM partners')
        refs = [
            ("Marc Worldwide Transport", "", "depuis mai 2026", 1),
            ("Network Pro Service", "", "2026", 2),
            ("RabbyTech (Abidjan)", "", "2025", 3),
            ("Groupe Cerco", "", "2019–2022", 4),
            ("Clean International", "", "chef d'équipe", 5),
            ("AÉI UQTR", "", "bénévole", 6),
        ]
        cursor.executemany('''
            INSERT INTO partners (name, image, period, order_index)
            VALUES (?, ?, ?, ?)
        ''', refs)
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


def init_projects_data(conn):
    try:
        cursor = conn.cursor()
        for title in TEMPLATE_PROJECT_TITLES:
            cursor.execute("UPDATE projects SET status='archived' WHERE title = ?", (title,))

        cursor.execute("SELECT COUNT(*) FROM projects WHERE title = ?", ("Système de gestion de transport",))
        if cursor.fetchone()[0] > 0:
            conn.commit()
            return

        projects = [
            ("Système de gestion de transport", "Flask, React, PostgreSQL",
             "Outil interne adopté par les équipes d'exploitation pour planifier et suivre les transports.",
             "pro", "Développeur Full Stack",
             "Marc Worldwide Transport devait réduire les erreurs de saisie et les retards de tournée.",
             json.dumps([
                 "Adoption par plus de 90 % des équipes",
                 "−60 % d'erreurs de saisie",
                 "+40 % de rapidité de traitement",
                 "−35 % de retards",
             ], ensure_ascii=False),
             "Comparaison avant/après sur 90 jours : journaux d'exploitation et tickets internes.",
             "depuis 2026", 1, 1),
            ("Gestion d'interventions — Network Pro Service", "React, Node.js, Python, PostgreSQL",
             "Application de suivi des interventions terrain, de la collecte à la clôture.",
             "pro", "Stagiaire développeur",
             "Les données d'intervention étaient collectées à la main, avec peu de visibilité temps réel.",
             json.dumps([
                 "−80 % de temps de collecte manuelle",
                 "+75 % de visibilité opérationnelle",
                 "95 % de satisfaction opérateurs",
             ], ensure_ascii=False),
             "Temps de saisie chronométré avant/après ; sondage opérateurs en fin de stage.",
             "2026", 2, 1),
            ("Plateforme de recyclage — RabbyTech", "Angular, NestJS, PostgreSQL, Scrum",
             "Plateforme de mise en relation et de suivi du recyclage.",
             "pro", "Analyse fonctionnelle et UX/UI",
             "Les intégrations API généraient des écarts de contrat et des bugs bloquants en recette.",
             json.dumps([
                 "−70 % d'erreurs d'intégration API",
                 "−45 % de bugs critiques",
             ], ensure_ascii=False),
             "Tickets Jira comparés entre deux sprints de recette, avant et après les maquettes et contrats.",
             "2025", 3, 1),
            ("OpenMoise — Groupe Cerco", "Python, APIs, OpenMedicine, OpenPay, OpenCar",
             "Suite de services (santé, paiement, mobilité) exposés par API.",
             "pro", "Développeur full stack puis chef d'équipe",
             "Migrations et disponibilité des API à maintenir pour plusieurs produits.",
             json.dumps([
                 "99,5 % de disponibilité des API",
                 "−60 % d'erreurs de migration",
             ], ensure_ascii=False),
             "Uptime monitoring interne et logs de migration sur les fenêtres de bascule.",
             "2019–2022", 4, 1),
            ("Reconnaissance vocale en langues locales", "Rasa, Python, NLU",
             "Assistant vocal pour des langues peu couvertes par les moteurs généraux.",
             "data", "Développeur NLU",
             "Les assistants du marché comprenaient mal les langues locales du terrain.",
             json.dumps([
                 "Intentions métier couvertes pour les langues cibles",
             ], ensure_ascii=False),
             "Évaluation manuelle d'un jeu de phrases annotées (taux d'intent correct).",
             "Cerco", 5, 0),
            ("Prédiction de la dépression étudiante", "Python, scikit-learn, données universitaires",
             "Modèle exploratoire pour identifier des facteurs de risque chez les étudiants.",
             "academic", "Analyste / data scientist",
             "Projet académique : mieux lire les signaux dans des données d'enquête.",
             json.dumps([
                 "Modèle validé en validation croisée",
             ], ensure_ascii=False),
             "Métrique F1 / AUC sur jeu de test tenu à l'écart de l'entraînement.",
             "UQTR", 6, 0),
            ("Série LinkedIn — données ouvertes canadiennes", "Python, données ouvertes, visualisation",
             "Analyses publiées à partir de jeux de données ouvertes canadiennes.",
             "data", "Auteur / analyste",
             "Rendre lisibles des jeux publics pour un public non spécialiste.",
             json.dumps([
                 "Publications régulières à partir de sources officielles",
             ], ensure_ascii=False),
             "Chaque figure cite la source ouverte et la date d'extraction.",
             "2024–2026", 7, 0),
        ]
        cursor.executemany('''
            INSERT INTO projects (title, technologies, description, category, role, context, results,
                measurement, period, order_index, featured, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published')
        ''', projects)
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
