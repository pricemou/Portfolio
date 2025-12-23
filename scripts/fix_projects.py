#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour corriger tous les projets existants et s'assurer qu'ils sont correctement formatés
"""

import sys
import os
from datetime import datetime

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

def fix_projects():
    """Corrige tous les projets pour s'assurer qu'ils ont tous les champs nécessaires"""
    print("🔧 Correction des projets existants...")
    
    try:
        with get_db() as conn:
            if conn is None:
                print("❌ Connexion DB impossible")
                return False
            
            cursor = conn.cursor()
            
            # Récupérer tous les projets
            cursor.execute('SELECT id, title, status, order_index, featured, created_at, updated_at, additional_images FROM projects')
            projects = cursor.fetchall()
            
            print(f"📊 {len(projects)} projets trouvés")
            
            fixed = 0
            now = datetime.now()
            
            for project in projects:
                project_id, title, status, order_index, featured, created_at, updated_at, additional_images = project
                
                updates = []
                params = []
                
                # Corriger status
                if status is None or status == '':
                    updates.append("status = ?")
                    params.append('published')
                elif status not in ['draft', 'published', 'archived']:
                    updates.append("status = ?")
                    params.append('published')
                
                # Corriger order_index
                if order_index is None:
                    updates.append("order_index = ?")
                    params.append(0)
                
                # Corriger featured
                if featured is None:
                    updates.append("featured = ?")
                    params.append(0)
                
                # Corriger created_at
                if created_at is None:
                    updates.append("created_at = ?")
                    params.append(now)
                
                # Corriger updated_at
                if updated_at is None:
                    updates.append("updated_at = ?")
                    params.append(now)
                else:
                    # Toujours mettre à jour updated_at
                    updates.append("updated_at = ?")
                    params.append(now)
                
                # Corriger additional_images
                if additional_images is None:
                    updates.append("additional_images = ?")
                    params.append('')
                
                if updates:
                    params.append(project_id)
                    query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(query, params)
                    print(f"  ✅ Corrigé: {title} (ID: {project_id})")
                    fixed += 1
            
            conn.commit()
            print(f"\n✅ Correction terminée: {fixed} projets mis à jour")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_projects()

