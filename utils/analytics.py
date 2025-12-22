"""
Module de gestion des analytics et statistiques
"""
from datetime import datetime, timedelta
import hashlib
from database import get_db, row_to_dict, rows_to_list

def track_page_view(conn, page_path, ip_address, user_agent, referer=None):
    """
    Enregistre une vue de page
    
    Args:
        conn: Connexion SQLite
        page_path: Chemin de la page visitée
        ip_address: Adresse IP du visiteur
        user_agent: User-Agent du navigateur
        referer: Page référente (optionnel)
    """
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics (type, page_path, ip_address, user_agent, referer, timestamp, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'page_view',
            page_path,
            ip_address,
            user_agent[:500] if user_agent else '',
            referer[:500] if referer else '',
            datetime.now(),
            datetime.now().date()
        ))
        conn.commit()
    except Exception as e:
        print(f"Erreur lors du tracking de la vue de page: {e}")

def track_project_view(conn, project_id, ip_address, user_agent):
    """
    Enregistre une vue d'un projet spécifique
    
    Args:
        conn: Connexion SQLite
        project_id: ID du projet visualisé
        ip_address: Adresse IP du visiteur
        user_agent: User-Agent du navigateur
    """
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        # Enregistrer dans analytics
        cursor.execute('''
            INSERT INTO analytics (type, project_id, ip_address, user_agent, timestamp, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'project_view',
            int(project_id),
            ip_address,
            user_agent[:500] if user_agent else '',
            datetime.now(),
            datetime.now().date()
        ))
        
        # Incrémenter le compteur de vues du projet
        cursor.execute('''
            UPDATE projects 
            SET views = views + 1 
            WHERE id = ?
        ''', (int(project_id),))
        
        conn.commit()
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

def track_visitor(conn, ip_address, user_agent, page_path):
    """
    Enregistre un visiteur unique
    
    Args:
        conn: Connexion SQLite
        ip_address: Adresse IP du visiteur
        user_agent: User-Agent du navigateur
        page_path: Page visitée
    """
    if conn is None:
        return
    
    try:
        visitor_id = get_visitor_id(ip_address, user_agent)
        today = datetime.now().date()
        
        cursor = conn.cursor()
        
        # Vérifier si ce visiteur a déjà été compté aujourd'hui
        cursor.execute('''
            SELECT * FROM analytics 
            WHERE type = ? AND visitor_id = ? AND date = ?
        ''', ('visitor', visitor_id, today))
        existing_visit = cursor.fetchone()
        
        if not existing_visit:
            # Nouveau visiteur pour aujourd'hui
            cursor.execute('''
                INSERT INTO analytics (type, visitor_id, ip_address, user_agent, timestamp, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'visitor',
                visitor_id,
                ip_address,
                user_agent[:500] if user_agent else '',
                datetime.now(),
                today
            ))
            conn.commit()
    except Exception as e:
        print(f"Erreur lors du tracking du visiteur: {e}")

def get_statistics(conn, days=30):
    """
    Récupère les statistiques pour les N derniers jours
    
    Args:
        conn: Connexion SQLite
        days: Nombre de jours à analyser (défaut: 30)
    
    Returns:
        dict: Statistiques agrégées
    """
    if conn is None:
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
        cursor = conn.cursor()
        
        # Date de début
        start_date = datetime.now() - timedelta(days=days)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Total des vues de pages
        cursor.execute('''
            SELECT COUNT(*) FROM analytics 
            WHERE type = ? AND timestamp >= ?
        ''', ('page_view', start_date))
        total_views = cursor.fetchone()[0]
        
        # Total des visiteurs uniques
        cursor.execute('''
            SELECT COUNT(*) FROM analytics 
            WHERE type = ? AND date >= ?
        ''', ('visitor', start_date.date()))
        total_visitors = cursor.fetchone()[0]
        
        # Total des projets publiés
        cursor.execute('SELECT COUNT(*) FROM projects WHERE status = ?', ('published',))
        total_projects = cursor.fetchone()[0]
        
        # Total des services
        cursor.execute('SELECT COUNT(*) FROM services')
        total_services = cursor.fetchone()[0]
        
        # Total des contacts
        cursor.execute('SELECT COUNT(*) FROM contacts')
        total_contacts = cursor.fetchone()[0]
        
        # Vues par jour (N derniers jours)
        views_by_day = []
        visitors_by_day = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date()
            
            cursor.execute('''
                SELECT COUNT(*) FROM analytics 
                WHERE type = ? AND date = ?
            ''', ('page_view', date))
            views_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM analytics 
                WHERE type = ? AND date = ?
            ''', ('visitor', date))
            visitors_count = cursor.fetchone()[0]
            
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
        cursor.execute('''
            SELECT id, title, views FROM projects 
            WHERE status = ? 
            ORDER BY views DESC 
            LIMIT 5
        ''', ('published',))
        rows = cursor.fetchall()
        top_projects = rows_to_list(rows)
        
        for project in top_projects:
            project['_id'] = str(project['id'])
            project['views'] = project.get('views', 0)
            del project['id']
        
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

def get_project_statistics(conn, project_id):
    """
    Récupère les statistiques d'un projet spécifique
    
    Args:
        conn: Connexion SQLite
        project_id: ID du projet
    
    Returns:
        dict: Statistiques du projet
    """
    if conn is None:
        return {'views': 0, 'views_by_day': []}
    
    try:
        cursor = conn.cursor()
        
        # Récupérer le projet et ses vues
        cursor.execute('SELECT views FROM projects WHERE id = ?', (int(project_id),))
        project_row = cursor.fetchone()
        total_views = project_row[0] if project_row else 0
        
        # Vues par jour (30 derniers jours)
        views_by_day = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).date()
            
            cursor.execute('''
                SELECT COUNT(*) FROM analytics 
                WHERE type = ? AND project_id = ? AND date = ?
            ''', ('project_view', int(project_id), date))
            views_count = cursor.fetchone()[0]
            
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
