#!/usr/bin/env python3
"""
Script de health check pour l'application
Usage: python scripts/health_check.py
"""
import os
import sys
import sqlite3
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_database():
    """Vérifie l'état de la base de données"""
    db_path = os.getenv('SQLITE_DB_PATH', 'portfolio.db')
    
    if not os.path.exists(db_path):
        print("❌ Base de données: NON DISPONIBLE (fichier introuvable)")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier les tables essentielles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['admin_users', 'homepage', 'skills', 'projects', 'services', 'contacts']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"⚠️  Base de données: TABLES MANQUANTES: {', '.join(missing_tables)}")
            conn.close()
            return False
        
        # Vérifier la connexion
        cursor.execute("SELECT 1")
        conn.close()
        
        print("✅ Base de données: OK")
        return True
    except Exception as e:
        print(f"❌ Base de données: ERREUR - {e}")
        return False

def check_disk_space():
    """Vérifie l'espace disque disponible"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage('.')
        free_gb = free / (1024**3)
        
        if free_gb < 1:
            print(f"⚠️  Espace disque: CRITIQUE - {free_gb:.2f} GB disponibles")
            return False
        elif free_gb < 5:
            print(f"⚠️  Espace disque: FAIBLE - {free_gb:.2f} GB disponibles")
            return True
        else:
            print(f"✅ Espace disque: OK - {free_gb:.2f} GB disponibles")
            return True
    except Exception as e:
        print(f"❌ Espace disque: ERREUR - {e}")
        return False

def check_environment():
    """Vérifie les variables d'environnement essentielles"""
    required_vars = ['SECRET_KEY', 'FLASK_ENV']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Variables d'environnement: MANQUANTES - {', '.join(missing_vars)}")
        return False
    
    # Vérifier que SECRET_KEY n'est pas la valeur par défaut
    secret_key = os.getenv('SECRET_KEY', '')
    if secret_key == 'changez-moi-en-production' or len(secret_key) < 20:
        print("⚠️  SECRET_KEY: VALEUR PAR DÉFAUT (changez-la en production)")
        return False
    
    print("✅ Variables d'environnement: OK")
    return True

def main():
    """Exécute tous les checks"""
    print("🔍 Health Check de l'application\n")
    
    results = []
    results.append(("Base de données", check_database()))
    results.append(("Espace disque", check_disk_space()))
    results.append(("Variables d'environnement", check_environment()))
    
    print("\n" + "="*50)
    all_ok = all(result[1] for result in results)
    
    if all_ok:
        print("✅ Tous les checks sont OK")
        return 0
    else:
        print("❌ Certains checks ont échoué")
        return 1

if __name__ == '__main__':
    sys.exit(main())

