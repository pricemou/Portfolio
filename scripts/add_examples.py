#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter des exemples de services et projets dans la base de données
"""

import sys
import os
from datetime import datetime

# Configuration UTF-8 pour Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        pass

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, init_database

def add_example_services():
    """Ajoute 5 exemples de services"""
    services = [
        {
            'title': 'Développement Web',
            'description': 'Création de sites web modernes et responsives avec les dernières technologies (React, Vue.js, Node.js). Développement d\'applications web full-stack performantes et sécurisées.',
            'icon': 'icons/code.svg',
            'order': 1
        },
        {
            'title': 'Applications Mobiles',
            'description': 'Développement d\'applications mobiles natives (iOS/Android) et cross-platform (React Native, Flutter). Interface utilisateur intuitive et expérience optimale.',
            'icon': 'icons/mobile.svg',
            'order': 2
        },
        {
            'title': 'Data Science & Analytics',
            'description': 'Analyse de données, machine learning et intelligence artificielle. Création de modèles prédictifs et visualisations de données pour prendre des décisions éclairées.',
            'icon': 'icons/data.svg',
            'order': 3
        },
        {
            'title': 'Consultation Technique',
            'description': 'Conseil et accompagnement technique pour vos projets. Architecture logicielle, optimisation de performance, code review et bonnes pratiques de développement.',
            'icon': 'icons/consulting.svg',
            'order': 4
        },
        {
            'title': 'Maintenance & Support',
            'description': 'Maintenance continue de vos applications, corrections de bugs, mises à jour de sécurité et support technique. Garantie de disponibilité et performance optimales.',
            'icon': 'icons/support.svg',
            'order': 5
        }
    ]
    
    with get_db() as conn:
        if conn is None:
            print("❌ Erreur: Impossible de se connecter à la base de données")
            return False
        
        cursor = conn.cursor()
        added_count = 0
        
        for service in services:
            try:
                # Vérifier si le service existe déjà
                cursor.execute('SELECT id FROM services WHERE title = ?', (service['title'],))
                if cursor.fetchone():
                    print(f"⚠️  Service '{service['title']}' existe déjà, ignoré")
                    continue
                
                # Insérer le service
                cursor.execute('''
                    INSERT INTO services (title, description, icon, order_index, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    service['title'],
                    service['description'],
                    service['icon'],
                    service['order'],
                    datetime.now(),
                    datetime.now()
                ))
                added_count += 1
                print(f"✅ Service ajouté: {service['title']}")
            except Exception as e:
                print(f"❌ Erreur lors de l'ajout du service '{service['title']}': {e}")
        
        conn.commit()
        print(f"\n📊 {added_count} service(s) ajouté(s) sur {len(services)}")
        return True

def add_example_projects():
    """Ajoute 5 exemples de projets"""
    projects = [
        {
            'title': 'Plateforme E-commerce',
            'description': 'Application e-commerce complète avec gestion de panier, paiement en ligne, système de commandes et interface d\'administration. Technologies: React, Node.js, PostgreSQL.',
            'technologies': 'React, Node.js, PostgreSQL, Stripe',
            'image': 'images/projects/ecommerce.png',
            'link': 'https://example.com/ecommerce',
            'github_link': 'https://github.com/example/ecommerce',
            'status': 'published',
            'order': 1,
            'featured': True
        },
        {
            'title': 'Application de Gestion de Tâches',
            'description': 'Application web de gestion de tâches collaborative avec authentification, tableaux Kanban, notifications en temps réel et synchronisation multi-appareils.',
            'technologies': 'Vue.js, Express.js, MongoDB, Socket.io',
            'image': 'images/projects/taskmanager.png',
            'link': 'https://example.com/tasks',
            'github_link': 'https://github.com/example/task-manager',
            'status': 'published',
            'order': 2,
            'featured': True
        },
        {
            'title': 'Dashboard Analytics',
            'description': 'Tableau de bord analytique avec visualisations interactives, rapports personnalisables et export de données. Analyse en temps réel des métriques business.',
            'technologies': 'React, Python, D3.js, FastAPI',
            'image': 'images/projects/dashboard.png',
            'link': 'https://example.com/dashboard',
            'github_link': 'https://github.com/example/analytics-dashboard',
            'status': 'published',
            'order': 3,
            'featured': False
        },
        {
            'title': 'Application Mobile Fitness',
            'description': 'Application mobile de suivi fitness avec suivi d\'activités, plans d\'entraînement personnalisés, intégration de capteurs et communauté d\'utilisateurs.',
            'technologies': 'React Native, Firebase, Redux',
            'image': 'images/projects/fitness.png',
            'link': 'https://example.com/fitness',
            'github_link': 'https://github.com/example/fitness-app',
            'status': 'published',
            'order': 4,
            'featured': False
        },
        {
            'title': 'Système de Réservation',
            'description': 'Plateforme de réservation en ligne pour hôtels avec calendrier interactif, gestion des disponibilités, paiement sécurisé et notifications automatiques.',
            'technologies': 'Angular, NestJS, MySQL, Redis',
            'image': 'images/projects/booking.png',
            'link': 'https://example.com/booking',
            'github_link': 'https://github.com/example/booking-system',
            'status': 'published',
            'order': 5,
            'featured': False
        }
    ]
    
    with get_db() as conn:
        if conn is None:
            print("❌ Erreur: Impossible de se connecter à la base de données")
            return False
        
        cursor = conn.cursor()
        added_count = 0
        
        for project in projects:
            try:
                # Vérifier si le projet existe déjà
                cursor.execute('SELECT id FROM projects WHERE title = ?', (project['title'],))
                if cursor.fetchone():
                    print(f"⚠️  Projet '{project['title']}' existe déjà, ignoré")
                    continue
                
                # Insérer le projet
                cursor.execute('''
                    INSERT INTO projects (title, description, technologies, image, link, github_link,
                                         status, order_index, featured, views, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project['title'],
                    project['description'],
                    project['technologies'],
                    project['image'],
                    project['link'],
                    project['github_link'],
                    project['status'],
                    project['order'],
                    1 if project['featured'] else 0,
                    0,  # views initial
                    datetime.now(),
                    datetime.now()
                ))
                added_count += 1
                print(f"✅ Projet ajouté: {project['title']}")
            except Exception as e:
                print(f"❌ Erreur lors de l'ajout du projet '{project['title']}': {e}")
        
        conn.commit()
        print(f"\n📊 {added_count} projet(s) ajouté(s) sur {len(projects)}")
        return True

def main():
    """Fonction principale"""
    print("=" * 60)
    print("Ajout d'exemples de services et projets")
    print("=" * 60)
    
    # Initialiser la base de données si nécessaire
    print("\n📦 Initialisation de la base de données...")
    init_database()
    
    # Ajouter les services
    print("\n" + "=" * 60)
    print("Ajout des services...")
    print("=" * 60)
    add_example_services()
    
    # Ajouter les projets
    print("\n" + "=" * 60)
    print("Ajout des projets...")
    print("=" * 60)
    add_example_projects()
    
    print("\n" + "=" * 60)
    print("✅ Terminé!")
    print("=" * 60)

if __name__ == '__main__':
    main()

