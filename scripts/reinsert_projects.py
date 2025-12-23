#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour réinsérer tous les projets existants avec les bonnes valeurs
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

def reinsert_projects():
    """Réinsère tous les projets avec les valeurs correctes"""
    print("🔄 Réinsertion des projets...")
    
    try:
        with get_db() as conn:
            if conn is None:
                print("❌ Connexion DB impossible")
                return False
            
            cursor = conn.cursor()
            
            # Récupérer tous les projets existants
            cursor.execute('''
                SELECT id, title, description, technologies, image, 
                       link, github_link, status, order_index, featured, 
                       views, created_at, updated_at, additional_images
                FROM projects
            ''')
            projects = cursor.fetchall()
            
            print(f"📊 {len(projects)} projets trouvés")
            
            # Sauvegarder les données
            projects_data = []
            for project in projects:
                projects_data.append({
                    'id': project[0],
                    'title': project[1],
                    'description': project[2] or '',
                    'technologies': project[3] or '',
                    'image': project[4] or '',
                    'link': project[5] or '',
                    'github_link': project[6] or '',
                    'status': project[7] or 'published',
                    'order_index': project[8] if project[8] is not None else 0,
                    'featured': project[9] if project[9] is not None else 0,
                    'views': project[10] if project[10] is not None else 0,
                    'created_at': project[11] or datetime.now(),
                    'updated_at': project[12] or datetime.now(),
                    'additional_images': project[13] if project[13] is not None else ''
                })
            
            # Supprimer tous les projets
            print("🗑️  Suppression des projets existants...")
            cursor.execute('DELETE FROM projects')
            
            # Réinsérer avec les valeurs correctes
            print("➕ Réinsertion des projets...")
            now = datetime.now()
            
            for project_data in projects_data:
                cursor.execute('''
                    INSERT INTO projects (
                        title, description, technologies, image,
                        additional_images, link, github_link, status, order_index,
                        featured, views, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_data['title'],
                    project_data['description'],
                    project_data['technologies'],
                    project_data['image'],
                    project_data['additional_images'],
                    project_data['link'],
                    project_data['github_link'],
                    project_data['status'],
                    project_data['order_index'],
                    project_data['featured'],
                    project_data['views'],
                    project_data['created_at'],
                    now  # Toujours mettre à jour updated_at
                ))
                print(f"  ✅ Réinséré: {project_data['title']}")
            
            conn.commit()
            print(f"\n✅ Réinsertion terminée: {len(projects_data)} projets réinsérés")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la réinsertion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  ATTENTION: Ce script va supprimer et réinsérer tous les projets!")
    response = input("Voulez-vous continuer? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        reinsert_projects()
    else:
        print("❌ Opération annulée")

