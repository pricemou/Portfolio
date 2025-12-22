"""
Module de gestion de la connexion MongoDB
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def get_mongo_client():
    """
    Crée et retourne un client MongoDB basé sur les variables d'environnement
    
    Returns:
        tuple: (client, database) ou (None, None) en cas d'erreur
    """
    mongo_uri = os.getenv('MONGO_URI')
    mongo_db_name = os.getenv('MONGO_DB_NAME', 'portfolio_db')
    
    # Si MONGO_URI n'est pas défini, retourner None
    if not mongo_uri:
        print("⚠️  MONGO_URI non défini dans .env - MongoDB désactivé")
        return None, None
    
    try:
        # Créer le client MongoDB avec des paramètres optimisés
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,  # Timeout de 10 secondes
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            retryWrites=True,
            w='majority'
        )
        
        # Tester la connexion
        client.admin.command('ping')
        print(f"✅ Connexion MongoDB réussie - Base de données: {mongo_db_name}")
        
        # Sélectionner la base de données
        db = client[mongo_db_name]
        
        return client, db
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = str(e)
        print(f"Erreur de connexion MongoDB: {error_msg[:200]}")
        print("L'application fonctionnera sans base de donnees MongoDB")
        
        # Messages d'aide spécifiques
        if "Connection refused" in error_msg:
            print("Conseil: Verifiez votre connexion internet et que MongoDB Atlas est accessible")
            print("Conseil: Verifiez que votre IP est autorisee dans MongoDB Atlas Network Access")
        elif "timeout" in error_msg.lower():
            print("Conseil: Le serveur MongoDB ne repond pas. Verifiez votre MONGO_URI dans .env")
        elif "authentication" in error_msg.lower():
            print("Conseil: Verifiez vos identifiants MongoDB dans MONGO_URI")
        
        return None, None
    except Exception as e:
        print(f"❌ Erreur inattendue MongoDB: {e}")
        return None, None

def init_database(db):
    """
    Initialise la base de données avec les collections et index nécessaires
    
    Args:
        db: Instance de la base de données MongoDB
    """
    try:
        # Créer les collections si elles n'existent pas
        collections = ['projects', 'services', 'contacts', 'analytics', 'homepage', 'skills', 'partners', 'admin_users']
        
        # Créer un index pour admin_users
        if 'admin_users' in db.list_collection_names():
            db.admin_users.create_index("username", unique=True)
        
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"✅ Collection '{collection_name}' créée")
        
        # Créer des index pour optimiser les requêtes
        if 'projects' in db.list_collection_names():
            db.projects.create_index("title")
            db.projects.create_index("created_at")
        
        if 'contacts' in db.list_collection_names():
            db.contacts.create_index("email")
            db.contacts.create_index("created_at")
        
        # Initialiser les données de la page d'accueil si elles n'existent pas
        init_homepage_data(db)
        
        # Initialiser les compétences si elles n'existent pas
        init_skills_data(db)
        
        # Initialiser les partenaires si elles n'existent pas
        init_partners_data(db)
        
        print("✅ Base de données initialisée avec succès")
        
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation de la base de données: {e}")

def init_homepage_data(db):
    """Initialise les données de la page d'accueil avec des valeurs par défaut"""
    try:
        homepage_collection = db.homepage
        
        # Vérifier si des données existent déjà
        if homepage_collection.count_documents({}) == 0:
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
            homepage_collection.insert_one(default_data)
            print("✅ Données par défaut de la page d'accueil créées")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des données homepage: {e}")

def init_skills_data(db):
    """Initialise les compétences avec des valeurs par défaut"""
    try:
        skills_collection = db.skills
        
        # Vérifier si des compétences existent déjà
        if skills_collection.count_documents({}) == 0:
            default_skills = [
                {
                    "title": "Full-Stack Development",
                    "icon": "icons/code.svg",
                    "description": "Développement d'applications web complètes, du frontend au backend, avec les dernières technologies.",
                    "projects_count": 15,
                    "order": 1
                },
                {
                    "title": "Data Science",
                    "icon": "icons/design.svg",
                    "description": "Analyse de données, machine learning et visualisation pour extraire des insights précieux.",
                    "projects_count": 12,
                    "order": 2
                },
                {
                    "title": "Architecture & DevOps",
                    "icon": "icons/phone.svg",
                    "description": "Conception d'architectures scalables et déploiement avec les meilleures pratiques DevOps.",
                    "projects_count": 8,
                    "order": 3
                }
            ]
            skills_collection.insert_many(default_skills)
            print("✅ Compétences par défaut créées")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des compétences: {e}")

def init_partners_data(db):
    """Initialise les partenaires/clients avec des valeurs par défaut"""
    try:
        partners_collection = db.partners
        
        # Vérifier si des partenaires existent déjà
        if partners_collection.count_documents({}) == 0:
            default_partners = [
                {"name": "wallety", "image": "images/partners/wallety.png", "order": 1},
                {"name": "artisty", "image": "images/partners/artisty.png", "order": 2},
                {"name": "khedma-lik", "image": "images/partners/khedma-lik.png", "order": 3},
                {"name": "directy", "image": "images/partners/directy.png", "order": 4},
                {"name": "telefy", "image": "images/partners/telefy.png", "order": 5}
            ]
            partners_collection.insert_many(default_partners)
            print("✅ Partenaires par défaut créés")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des partenaires: {e}")

