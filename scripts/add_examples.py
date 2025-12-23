#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour initialiser la base de données
et insérer les 10 projets réels avec descriptions détaillées
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

from database import get_db, init_database


def add_example_projects():
    """Ajoute 10 projets réels avec descriptions détaillées"""
    projects = [
        {
            "title": "Système de Gestion de Bibliothèque",
            "description": (
                "Application desktop développée en C# avec Windows Forms permettant la gestion complète "
                "des livres, des emprunts et des utilisateurs. "
                "Le système intègre une authentification sécurisée pour les administrateurs et utilisateurs, "
                "la possibilité de suivre les prêts en temps réel, et des fonctionnalités d’ajout, modification "
                "et suppression des livres et des comptes utilisateurs. "
                "Le projet a été modélisé avec UML afin de planifier et documenter la structure des classes et les flux de données."
            ),
            "technologies": "C#, Windows Forms, SQL Server, UML",
            "image": "images/projects/library.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 1,
            "featured": True
        },
        {
            "title": "Plateforme Open Moise",
            "description": (
                "Participation au développement d’une plateforme web collaborative visant à centraliser et gérer "
                "les contenus numériques. Le projet incluait la conception de l’architecture, le développement "
                "des modules côté frontend et backend, ainsi que la mise en place de fonctionnalités de gestion "
                "des utilisateurs, publication de contenu et sécurité des données. "
                "L’objectif était de faciliter la collaboration et l’accès aux contenus pour les utilisateurs."
            ),
            "technologies": "HTML, CSS, JavaScript, PHP",
            "image": "images/projects/openmoise.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 2,
            "featured": True
        },
        {
            "title": "Système de Gestion de Pharmacie (POS)",
            "description": (
                "Application web complète pour la gestion d’une pharmacie incluant le suivi des stocks, "
                "l’enregistrement des produits, la gestion des commandes clients en ligne et le suivi des livraisons. "
                "Le projet a utilisé une architecture REST API pour séparer le frontend et le backend, "
                "assurant ainsi la scalabilité et la sécurité. "
                "Des fonctionnalités supplémentaires comme la gestion des utilisateurs et des rôles ont été intégrées "
                "pour un contrôle précis des accès."
            ),
            "technologies": "Node.js, Express.js, MongoDB, Docker, REST API",
            "image": "images/projects/pharmacy.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 3,
            "featured": True
        },
        {
            "title": "Application de Télémédecine",
            "description": (
                "Développement d’une application permettant aux patients et aux professionnels de santé de réaliser "
                "des consultations médicales à distance. "
                "Le projet comprenait l’analyse des besoins, la conception de la base de données, la gestion des comptes utilisateurs, "
                "la planification des rendez-vous et la sécurisation des échanges de données sensibles. "
                "L’interface utilisateur a été conçue pour être intuitive et adaptée à différents appareils."
            ),
            "technologies": "Node.js, JavaScript, MySQL",
            "image": "images/projects/telemedicine.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 4,
            "featured": False
        },
        {
            "title": "Application de Lutte contre les Violences Basées sur le Genre",
            "description": (
                "Projet à impact social visant à fournir un outil de sensibilisation et de signalement sécurisé "
                "des violences basées sur le genre. "
                "L’application comprend la collecte de données anonymisées, la gestion des utilisateurs et des signalements, "
                "ainsi qu’un tableau de bord pour le suivi statistique. "
                "Elle inclut également une interface simple et sécurisée pour les victimes et les professionnels de soutien."
            ),
            "technologies": "PHP, MySQL, HTML, CSS",
            "image": "images/projects/vbg.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 5,
            "featured": False
        },
        {
            "title": "Jeu de Cartes Pêche | Pioche",
            "description": (
                "Jeu de cartes multijoueur pour 2 à 4 joueurs, développé en C# avec une architecture orientée objet. "
                "Chaque joueur possède une main de cartes et le jeu gère la pioche ainsi que les interactions entre joueurs. "
                "Le projet inclut la conception de la classe TableDeJeu, la gestion des règles, et la distribution aléatoire des cartes. "
                "Le système assure l’intégrité des données et le respect des contraintes du jeu."
            ),
            "technologies": "C#, Programmation Orientée Objet",
            "image": "images/projects/cards.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 6,
            "featured": False
        },
        {
            "title": "Projet de Réseautique – Subnetting et Gestion IP",
            "description": (
                "Travaux pratiques axés sur l’adressage IP, le découpage en sous-réseaux et la planification de réseaux informatiques. "
                "Le projet incluait l’analyse des besoins réseau, la répartition efficace des adresses IP, "
                "et la documentation de chaque sous-réseau pour une maintenance simplifiée."
            ),
            "technologies": "Réseautique, IPv4, Subnetting",
            "image": "images/projects/network.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 7,
            "featured": False
        },
        {
            "title": "Projet d’Analyse et Modélisation (INF1006)",
            "description": (
                "Projet académique de modélisation logicielle comprenant l’analyse des besoins fonctionnels et techniques "
                "et la création de diagrammes UML (classes, séquences, composants). "
                "Le projet a permis de planifier la structure logicielle et d’assurer la cohérence entre les différentes parties du système."
            ),
            "technologies": "UML, PlantUML, StarUML",
            "image": "images/projects/uml.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 8,
            "featured": False
        },
        {
            "title": "Architecture Frontend / Backend Web",
            "description": (
                "Conception d’une architecture web respectant le principe de responsabilité unique (SRP), "
                "avec séparation claire entre frontend et backend. "
                "Le projet inclut la mise en place de composants modulaires, la structuration du code pour une maintenance facile, "
                "et l’optimisation des flux de données entre le client et le serveur."
            ),
            "technologies": "React, TypeScript, Node.js",
            "image": "images/projects/architecture.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 9,
            "featured": False
        },
        {
            "title": "Site Web de Gestion de Paris Sportifs",
            "description": (
                "Application web permettant l’enregistrement des pronostics sportifs, la saisie des résultats, "
                "l’analyse des gains et pertes, et la génération de fichiers Excel pour le suivi des performances. "
                "Le système inclut également des statistiques détaillées pour aider à l’analyse des tendances et des résultats des paris."
            ),
            "technologies": "Node.js, Express.js, MongoDB, MVC",
            "image": "images/projects/betting.png",
            "link": "",
            "github_link": "",
            "status": "published",
            "order": 10,
            "featured": True
        }
    ]

    with get_db() as conn:
        if conn is None:
            print("❌ Connexion DB impossible")
            return

        cursor = conn.cursor()

        for project in projects:
            cursor.execute("SELECT id FROM projects WHERE title = ?", (project["title"],))
            if cursor.fetchone():
                print(f"⚠️ Projet déjà existant : {project['title']}")
                continue

            cursor.execute(
                """
                INSERT INTO projects (
                    title, description, technologies, image,
                    additional_images, link, github_link, status, order_index,
                    featured, views, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project["title"],
                    project["description"],
                    project["technologies"],
                    project["image"],
                    project.get("additional_images", ""),  # Champ additional_images
                    project["link"],
                    project["github_link"],
                    project["status"],
                    project["order"],
                    1 if project["featured"] else 0,
                    0,
                    datetime.now(),
                    datetime.now()
                )
            )
            print(f"✅ Projet ajouté : {project['title']}")

        conn.commit()


def main():
    print("📦 Initialisation de la base de données...")
    init_database()

    print("➕ Insertion des projets...")
    add_example_projects()

    print("🎉 Terminé avec succès")


if __name__ == "__main__":
    main()
