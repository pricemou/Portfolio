#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de diagnostic complet pour vérifier l'état des projets dans la base de données
"""

import sys
import os
import sqlite3
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

from database import get_db, rows_to_list

def diagnose_projects():
    """Diagnostic complet des projets"""
    print("=" * 60)
    print("🔍 DIAGNOSTIC COMPLET DES PROJETS")
    print("=" * 60)
    
    try:
        with get_db() as conn:
            if conn is None:
                print("❌ Connexion DB impossible")
                return False
            
            cursor = conn.cursor()
            
            # 1. Vérifier la structure de la table
            print("\n📋 1. STRUCTURE DE LA TABLE")
            print("-" * 60)
            cursor.execute("PRAGMA table_info(projects)")
            columns = cursor.fetchall()
            print(f"Colonnes trouvées: {len(columns)}")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) - Default: {col[4]}")
            
            # 2. Vérifier le dernier ID et la séquence
            print("\n📊 2. IDENTIFIANTS")
            print("-" * 60)
            cursor.execute("SELECT MAX(id) FROM projects")
            max_id = cursor.fetchone()[0]
            print(f"Dernier ID: {max_id}")
            
            cursor.execute("SELECT COUNT(*) FROM projects")
            total = cursor.fetchone()[0]
            print(f"Nombre total de projets: {total}")
            
            # 3. Vérifier les colonnes obligatoires
            print("\n✅ 3. VÉRIFICATION DES COLONNES OBLIGATOIRES")
            print("-" * 60)
            cursor.execute('''
                SELECT id, title, status, order_index, featured, 
                       created_at, updated_at, additional_images
                FROM projects
            ''')
            projects = cursor.fetchall()
            
            issues = []
            for project in projects:
                project_id, title, status, order_index, featured, created_at, updated_at, additional_images = project
                
                project_issues = []
                
                # Vérifier status
                if status is None or status == '':
                    project_issues.append("status manquant")
                elif status not in ['draft', 'published', 'archived']:
                    project_issues.append(f"status invalide: {status}")
                
                # Vérifier order_index
                if order_index is None:
                    project_issues.append("order_index manquant")
                
                # Vérifier featured
                if featured is None:
                    project_issues.append("featured manquant")
                
                # Vérifier created_at
                if created_at is None:
                    project_issues.append("created_at manquant")
                
                # Vérifier updated_at
                if updated_at is None:
                    project_issues.append("updated_at manquant")
                
                # Vérifier additional_images
                if additional_images is None:
                    project_issues.append("additional_images est None (doit être '')")
                
                if project_issues:
                    issues.append({
                        'id': project_id,
                        'title': title,
                        'issues': project_issues
                    })
            
            if issues:
                print(f"⚠️  {len(issues)} projets avec des problèmes:")
                for issue in issues:
                    print(f"\n  ID {issue['id']}: {issue['title']}")
                    for problem in issue['issues']:
                        print(f"    - {problem}")
            else:
                print("✅ Tous les projets ont les colonnes obligatoires remplies")
            
            # 4. Vérifier les projets publiés
            print("\n📰 4. PROJETS PUBLIÉS")
            print("-" * 60)
            cursor.execute('''
                SELECT id, title, status, order_index 
                FROM projects 
                WHERE status = ?
                ORDER BY order_index ASC, created_at DESC
            ''', ('published',))
            published = cursor.fetchall()
            print(f"Nombre de projets publiés: {len(published)}")
            
            if published:
                print("\nListe des projets publiés:")
                for i, proj in enumerate(published[:10], 1):
                    print(f"  {i}. ID: {proj[0]} - {proj[1]} (order: {proj[3]})")
            
            # 5. Test de récupération avec rows_to_list
            print("\n🔄 5. TEST DE RÉCUPÉRATION")
            print("-" * 60)
            cursor.execute('''
                SELECT * FROM projects 
                WHERE status = ? 
                ORDER BY order_index ASC, created_at DESC
            ''', ('published',))
            rows = cursor.fetchall()
            projects_list = rows_to_list(rows)
            
            print(f"Lignes récupérées: {len(rows)}")
            print(f"Projets convertis: {len(projects_list)}")
            
            if projects_list:
                print("\nExemple de projet converti:")
                sample = projects_list[0]
                print(f"  ID: {sample.get('id')}")
                print(f"  Title: {sample.get('title')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  Order: {sample.get('order_index')}")
                print(f"  Featured: {sample.get('featured')}")
                print(f"  Additional images: {sample.get('additional_images', 'N/A')}")
            
            # 6. Recommandations
            print("\n💡 6. RECOMMANDATIONS")
            print("-" * 60)
            if issues:
                print("⚠️  Des problèmes ont été détectés. Exécutez:")
                print("   python scripts/fix_projects.py")
            else:
                print("✅ Aucun problème détecté dans la structure des données")
                print("💡 Si les projets ne s'affichent toujours pas:")
                print("   1. Videz le cache du navigateur (Ctrl + Shift + R)")
                print("   2. Vérifiez les logs du serveur Flask")
                print("   3. Vérifiez la console du navigateur (F12)")
            
            return len(issues) == 0
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    diagnose_projects()

