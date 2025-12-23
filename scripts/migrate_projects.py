#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour migrer les projets existants et s'assurer qu'ils ont tous les champs nécessaires
"""

import sys
import os

# Configuration UTF-8 (Windows)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ajout du dossier parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def migrate_projects():
    """Met à jour les projets existants pour s'assurer qu'ils ont tous les champs nécessaires"""
    print("🔄 Migration des projets existants...")
    
    try:
        with get_db() as conn:
            if conn is None:
                print("❌ Connexion DB impossible")
                return False
            
            cursor = conn.cursor()
            
            # Vérifier tous les projets
            cursor.execute('SELECT id, title, status, additional_images FROM projects')
            projects = cursor.fetchall()
            
            print(f"📊 {len(projects)} projets trouvés")
            
            updated = 0
            for project in projects:
                project_id, title, status, additional_images = project
                
                # Mettre à jour additional_images si None ou vide
                if additional_images is None:
                    cursor.execute(
                        'UPDATE projects SET additional_images = ? WHERE id = ?',
                        ('', project_id)
                    )
                    print(f"  ✅ Mis à jour: {title} (ID: {project_id}) - additional_images ajouté")
                    updated += 1
                elif additional_images == '':
                    # Déjà correct
                    pass
                else:
                    # Déjà défini
                    pass
            
            conn.commit()
            print(f"\n✅ Migration terminée: {updated} projets mis à jour")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_projects()

