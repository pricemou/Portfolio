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
                    status TEXT DEFAULT 'published',
                    order_index INTEGER DEFAULT 0,
                    featured INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
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
            
            conn.commit()
            
            # Initialiser les données par défaut
            init_homepage_data(conn)
            init_skills_data(conn)
            init_partners_data(conn)
            
            print("✅ Base de données SQLite initialisée avec succès")
            return True
            
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation de la base de données: {e}")
        return False

def init_homepage_data(conn):
    """Initialise les données de la page d'accueil avec des valeurs par défaut"""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM homepage WHERE type = ?', ('header',))
        count = cursor.fetchone()[0]
        
        if count == 0:
            default_data = {
                "type": "header",
                "badge": "Développeur Full-Stack & Data Science",
                "title_line1": "De l'idée à la donnée.",
                "title_line2": "Du code à l'insight !",
                "description": "Je développe des applications web complètes et transforme les données en décisions stratégiques. Passionné par l'innovation technologique et l'analyse de données.",
                "email": "contact@example.com",
                "cta_text": "Discutons !",
                "about_title": "Présentation",
                "about_name": "Pricemou claude",
                "about_subtitle": "Développeur Full-Stack & Data Science passionné par l'innovation et l'excellence technique.",
                "about_description": "Je suis un développeur Full-Stack et Data Scientist avec une passion pour créer des solutions technologiques complètes et performantes. Mon expertise couvre tout le spectre du développement web, du frontend interactif aux APIs backend robustes, en passant par l'analyse de données et le machine learning.\n\nFort de plusieurs années d'expérience, j'ai développé des applications web modernes, conçu des architectures scalables et transformé des données complexes en insights actionnables. Je maîtrise les technologies modernes comme React, Node.js, Python, SQL, ainsi que les outils de data science comme Pandas, NumPy, Scikit-learn et les visualisations avec Matplotlib et D3.js.\n\nJe suis constamment en veille technologique, curieux des nouvelles tendances et toujours prêt à relever de nouveaux défis. Mon approche combine rigueur technique, créativité et attention aux détails pour livrer des solutions qui font la différence."
            }
            
            cursor.execute('''
                INSERT INTO homepage (type, badge, title_line1, title_line2, description, email, cta_text,
                                     about_title, about_name, about_subtitle, about_description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                default_data['type'], default_data['badge'], default_data['title_line1'],
                default_data['title_line2'], default_data['description'], default_data['email'],
                default_data['cta_text'], default_data['about_title'], default_data['about_name'],
                default_data['about_subtitle'], default_data['about_description']
            ))
            conn.commit()
            print("✅ Données par défaut de la page d'accueil créées")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des données homepage: {e}")

def init_skills_data(conn):
    """Initialise les compétences avec des valeurs par défaut"""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM skills')
        count = cursor.fetchone()[0]
        
        if count == 0:
            default_skills = [
                ("Full-Stack Development", "icons/code.svg", "Développement d'applications web complètes, du frontend au backend, avec les dernières technologies.", 15, 1),
                ("Data Science", "icons/design.svg", "Analyse de données, machine learning et visualisation pour extraire des insights précieux.", 12, 2),
                ("Architecture & DevOps", "icons/phone.svg", "Conception d'architectures scalables et déploiement avec les meilleures pratiques DevOps.", 8, 3)
            ]
            
            cursor.executemany('''
                INSERT INTO skills (title, icon, description, projects_count, order_index)
                VALUES (?, ?, ?, ?, ?)
            ''', default_skills)
            conn.commit()
            print("✅ Compétences par défaut créées")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des compétences: {e}")

def init_partners_data(conn):
    """Initialise les partenaires/clients avec des valeurs par défaut"""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM partners')
        count = cursor.fetchone()[0]
        
        if count == 0:
            default_partners = [
                ("wallety", "images/partners/wallety.png", 1),
                ("artisty", "images/partners/artisty.png", 2),
                ("khedma-lik", "images/partners/khedma-lik.png", 3),
                ("directy", "images/partners/directy.png", 4),
                ("telefy", "images/partners/telefy.png", 5)
            ]
            
            cursor.executemany('''
                INSERT INTO partners (name, image, order_index)
                VALUES (?, ?, ?)
            ''', default_partners)
            conn.commit()
            print("✅ Partenaires par défaut créés")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des partenaires: {e}")

def row_to_dict(row):
    """Convertit une ligne SQLite en dictionnaire"""
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows):
    """Convertit plusieurs lignes SQLite en liste de dictionnaires"""
    return [dict(row) for row in rows]
