"""
Point d'entrée WSGI pour le déploiement en production
Utilisé par uWSGI, Gunicorn, et autres serveurs WSGI
"""
import os
import sys

# Ajouter le répertoire du projet au path Python
sys.path.insert(0, os.path.dirname(__file__))

# Importer l'application Flask
from app import app

# L'application Flask est maintenant disponible pour uWSGI
application = app

if __name__ == "__main__":
    # Pour les tests locaux uniquement
    app.run(host='0.0.0.0', port=5000)

