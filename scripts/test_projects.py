#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour tester la récupération des projets
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

from database import get_db, rows_to_list

def test_projects():
    """Test la récupération des projets"""
    print("🔍 Test de récupération des projets...")
    
    try:
        with get_db() as conn:
            if conn is None:
                print("❌ Connexion DB impossible")
                return
            
            cursor = conn.cursor()
            
            # Test 1: Compter tous les projets
            cursor.execute('SELECT COUNT(*) FROM projects')
            total = cursor.fetchone()[0]
            print(f"📊 Total de projets dans la DB: {total}")
            
            # Test 2: Compter les projets publiés
            cursor.execute('SELECT COUNT(*) FROM projects WHERE status = ?', ('published',))
            published = cursor.fetchone()[0]
            print(f"📊 Projets publiés: {published}")
            
            # Test 3: Récupérer les projets publiés
            cursor.execute('''
                SELECT * FROM projects 
                WHERE status = ? 
                ORDER BY order_index ASC, created_at DESC
            ''', ('published',))
            rows = cursor.fetchall()
            print(f"📊 Lignes récupérées: {len(rows)}")
            
            # Test 4: Convertir avec rows_to_list
            projects = rows_to_list(rows)
            print(f"📊 Projets convertis: {len(projects)}")
            
            # Test 5: Afficher les détails
            if projects:
                print("\n📋 Détails des projets:")
                for i, project in enumerate(projects[:5], 1):
                    print(f"\n  {i}. ID: {project.get('id')}")
                    print(f"     Title: {project.get('title', 'N/A')}")
                    print(f"     Status: {project.get('status', 'N/A')}")
                    print(f"     Order: {project.get('order_index', 'N/A')}")
                    print(f"     Featured: {project.get('featured', 'N/A')}")
                    print(f"     Image: {project.get('image', 'N/A')}")
                    print(f"     Additional images: {project.get('additional_images', 'N/A')}")
            else:
                print("⚠️ Aucun projet trouvé!")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_projects()

