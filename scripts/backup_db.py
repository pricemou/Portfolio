#!/usr/bin/env python3
"""
Script de backup automatique de la base de données SQLite
Usage: python scripts/backup_db.py
"""
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def backup_database():
    """Crée une sauvegarde de la base de données SQLite"""
    # Chemin de la base de données
    db_path = os.getenv('SQLITE_DB_PATH', 'portfolio.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Erreur: La base de données {db_path} n'existe pas")
        return False
    
    # Créer le dossier backups s'il n'existe pas
    backups_dir = Path('backups')
    backups_dir.mkdir(exist_ok=True)
    
    # Nom du fichier de backup avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"portfolio_backup_{timestamp}.db"
    backup_path = backups_dir / backup_filename
    
    try:
        # Copier la base de données
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup créé: {backup_path}")
        
        # Nettoyer les anciens backups (garder les 30 derniers jours)
        cleanup_old_backups(backups_dir, days=30)
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du backup: {e}")
        return False

def cleanup_old_backups(backups_dir, days=30):
    """Supprime les backups plus anciens que X jours"""
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for backup_file in backups_dir.glob('portfolio_backup_*.db'):
        try:
            # Extraire la date du nom de fichier
            filename = backup_file.stem
            date_str = filename.replace('portfolio_backup_', '')
            file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            
            if file_date < cutoff_date:
                backup_file.unlink()
                print(f"🗑️  Backup supprimé (trop ancien): {backup_file.name}")
        except Exception as e:
            print(f"⚠️  Erreur lors de la suppression de {backup_file}: {e}")

if __name__ == '__main__':
    success = backup_database()
    sys.exit(0 if success else 1)

