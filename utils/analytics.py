"""
Module de gestion des analytics et statistiques
"""
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import hashlib

def track_page_view(db, page_path, ip_address, user_agent, referer=None):
    """
    Enregistre une vue de page
    
    Args:
        db: Instance de la base de données MongoDB
        page_path: Chemin de la page visitée
        ip_address: Adresse IP du visiteur
        user_agent: User-Agent du navigateur
        referer: Page référente (optionnel)
    """
    if db is None:
        return
    
    try:
        analytics_collection = db.analytics
        analytics_collection.insert_one({
            'type': 'page_view',
            'page_path': page_path,
            'ip_address': ip_address,
            'user_agent': user_agent[:500] if user_agent else '',
            'referer': referer[:500] if referer else '',
            'timestamp': datetime.now(),
            'date': datetime.now().date()
        })
    except Exception as e:
        print(f"Erreur lors du tracking de la vue de page: {e}")

def track_project_view(db, project_id, ip_address, user_agent):
    """
    Enregistre une vue d'un projet spécifique
    
    Args:
        db: Instance de la base de données MongoDB
        project_id: ID du projet visualisé
        ip_address: Adresse IP du visiteur
        user_agent: User-Agent du navigateur
    """
    if db is None:
        return
    
    try:
        # Enregistrer dans analytics
        analytics_collection = db.analytics
        analytics_collection.insert_one({
            'type': 'project_view',
            'project_id': project_id,
            'ip_address': ip_address,
            'user_agent': user_agent[:500] if user_agent else '',
            'timestamp': datetime.now(),
            'date': datetime.now().date()
        })
        
        # Incrémenter le compteur de vues du projet
        projects_collection = db.projects
        projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$inc": {"views": 1}}
        )
    except Exception as e:
        print(f"Erreur lors du tracking de la vue de projet: {e}")

def get_visitor_id(ip_address, user_agent):
    """
    Génère un ID de visiteur unique basé sur IP et User-Agent
    
    Args:
        ip_address: Adresse IP
        user_agent: User-Agent du navigateur
    
    Returns:
        str: Hash unique du visiteur
    """
    combined = f"{ip_address}_{user_agent}"
    return hashlib.md5(combined.encode()).hexdigest()

def track_visitor(db, ip_address, user_agent, page_path):
    """
    Enregistre un visiteur unique
    
    Args:
        db: Instance de la base de données MongoDB
        ip_address: Adresse IP du visiteur
        user_agent: User-Agent du navigateur
        page_path: Page visitée
    """
    if db is None:
        return
    
    try:
        visitor_id = get_visitor_id(ip_address, user_agent)
        today = datetime.now().date()
        
        analytics_collection = db.analytics
        
        # Vérifier si ce visiteur a déjà été compté aujourd'hui
        existing_visit = analytics_collection.find_one({
            'type': 'visitor',
            'visitor_id': visitor_id,
            'date': today
        })
        
        if not existing_visit:
            # Nouveau visiteur pour aujourd'hui
            analytics_collection.insert_one({
                'type': 'visitor',
                'visitor_id': visitor_id,
                'ip_address': ip_address,
                'user_agent': user_agent[:500] if user_agent else '',
                'first_visit': datetime.now(),
                'date': today
            })
    except Exception as e:
        print(f"Erreur lors du tracking du visiteur: {e}")

def get_statistics(db, days=30):
    """
    Récupère les statistiques pour les N derniers jours
    
    Args:
        db: Instance de la base de données MongoDB
        days: Nombre de jours à analyser (défaut: 30)
    
    Returns:
        dict: Statistiques agrégées
    """
    if db is None:
        return {
            'total_views': 0,
            'total_visitors': 0,
            'total_projects': 0,
            'total_services': 0,
            'total_contacts': 0,
            'engagement_rate': 0,
            'views_by_day': [],
            'visitors_by_day': [],
            'top_projects': []
        }
    
    try:
        analytics_collection = db.analytics
        projects_collection = db.projects
        services_collection = db.services
        contacts_collection = db.contacts
        
        # Date de début
        start_date = datetime.now() - timedelta(days=days)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Total des vues de pages
        total_views = analytics_collection.count_documents({
            'type': 'page_view',
            'timestamp': {'$gte': start_date}
        })
        
        # Total des visiteurs uniques
        total_visitors = analytics_collection.count_documents({
            'type': 'visitor',
            'date': {'$gte': start_date.date()}
        })
        
        # Total des projets publiés
        total_projects = projects_collection.count_documents({'status': 'published'})
        
        # Total des services
        total_services = services_collection.count_documents({})
        
        # Total des contacts
        total_contacts = contacts_collection.count_documents({})
        
        # Vues par jour (30 derniers jours)
        views_by_day = []
        visitors_by_day = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date()
            views_count = analytics_collection.count_documents({
                'type': 'page_view',
                'date': date
            })
            visitors_count = analytics_collection.count_documents({
                'type': 'visitor',
                'date': date
            })
            views_by_day.append({
                'date': date.isoformat(),
                'views': views_count
            })
            visitors_by_day.append({
                'date': date.isoformat(),
                'visitors': visitors_count
            })
        
        # Inverser pour avoir les dates du plus ancien au plus récent
        views_by_day.reverse()
        visitors_by_day.reverse()
        
        # Top projets par vues
        top_projects = list(projects_collection.find(
            {'status': 'published'},
            {'title': 1, 'views': 1, '_id': 1}
        ).sort('views', -1).limit(5))
        
        for project in top_projects:
            project['_id'] = str(project['_id'])
            project['views'] = project.get('views', 0)
        
        # Calcul du taux d'engagement
        # Engagement = (visiteurs qui ont visité plusieurs pages) / (total visiteurs) * 100
        # Pour simplifier, on utilise: (vues / visiteurs) * 100 avec un max de 100%
        if total_visitors > 0:
            engagement_rate = min(100, int((total_views / total_visitors) * 100))
        else:
            engagement_rate = 0
        
        return {
            'total_views': total_views,
            'total_visitors': total_visitors,
            'total_projects': total_projects,
            'total_services': total_services,
            'total_contacts': total_contacts,
            'engagement_rate': engagement_rate,
            'views_by_day': views_by_day,
            'visitors_by_day': visitors_by_day,
            'top_projects': top_projects,
            'period_days': days
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {e}")
        return {
            'total_views': 0,
            'total_visitors': 0,
            'total_projects': 0,
            'total_services': 0,
            'total_contacts': 0,
            'engagement_rate': 0,
            'views_by_day': [],
            'visitors_by_day': [],
            'top_projects': []
        }

def get_project_statistics(db, project_id):
    """
    Récupère les statistiques d'un projet spécifique
    
    Args:
        db: Instance de la base de données MongoDB
        project_id: ID du projet
    
    Returns:
        dict: Statistiques du projet
    """
    if db is None:
        return {'views': 0, 'views_by_day': []}
    
    try:
        analytics_collection = db.analytics
        projects_collection = db.projects
        
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        total_views = project.get('views', 0) if project else 0
        
        # Vues par jour (30 derniers jours)
        views_by_day = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).date()
            views_count = analytics_collection.count_documents({
                'type': 'project_view',
                'project_id': project_id,
                'date': date
            })
            views_by_day.append({
                'date': date.isoformat(),
                'views': views_count
            })
        
        views_by_day.reverse()
        
        return {
            'views': total_views,
            'views_by_day': views_by_day
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques du projet: {e}")
        return {'views': 0, 'views_by_day': []}


