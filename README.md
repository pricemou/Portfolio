# Developer Portfolio

![licence](https://img.shields.io/badge/licence-MIT-blue)

Developer Portfolio is a web template made for developers to present themselves based on Flask.


## Table of Contents

- [Demo](#demo)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Run Locally](#run-locally)
- [Deployment](#deployment)
- [File Structure](#file-structure)
- [Author](#author)
- [License](#license)

## Demo

[Developer Portfolio demo link](https://developer-portfolio-gules.vercel.app/)

## Tech Stack

**Backend:** Python / Flask  
**Frontend:** HTML5 / CSS3 / Jinja2 Templates  
**Base de données:** SQLite  
**Validation:** Utils personnalisés  
**Tests:** unittest (Python)

## Quick start

Clone the repo

```bash
  git clone https://github.com/blaiti/Developer-Portfolio.git
```

### Créer et activer l'environnement virtuel

**Sur Windows (PowerShell):**
```bash
  cd Developer-Portfolio
  python -m venv venv
  .\venv\Scripts\Activate.ps1
```

**Sur Windows (CMD):**
```bash
  cd Developer-Portfolio
  python -m venv venv
  venv\Scripts\activate.bat
```

**Sur Linux/Mac:**
```bash
  cd Developer-Portfolio
  python3 -m venv venv
  source venv/bin/activate
```

**Sur Git Bash (Windows):**
```bash
  cd Developer-Portfolio
  python -m venv venv
  source venv/Scripts/activate
```

### Installer les dépendances

Une fois l'environnement virtuel activé, installez les dépendances :

```bash
  pip install -r requirements.txt
```

### Configurer les variables d'environnement

Le projet utilise des variables d'environnement pour la configuration. Créez un fichier `.env` à partir du modèle :

**Sur Windows (PowerShell):**
```bash
  Copy-Item .env.example .env
```

**Sur Linux/Mac/Git Bash:**
```bash
  cp .env.example .env
```

Puis éditez le fichier `.env` avec vos propres valeurs :
- `PORTFOLIO_NAME` : Votre nom
- `PORTFOLIO_EMAIL` : Votre email de contact
- `SECRET_KEY` : Clé secrète pour Flask (changez-la en production)
- `DEBUG` : `True` pour le développement, `False` pour la production

## Run Locally

Pour exécuter l'application localement, assurez-vous que l'environnement virtuel est activé, puis exécutez :

```bash
  python app.py
```

L'application sera disponible sur `http://localhost:5000` (ou l'adresse configurée dans `.env`)

**Note:** Pour désactiver l'environnement virtuel, tapez simplement `deactivate` dans le terminal.

## Configuration des Variables d'Environnement

Le projet utilise un fichier `.env` pour la configuration. Les variables principales sont :

### Configuration Flask
- `FLASK_ENV` : Environnement Flask (development/production)
- `DEBUG` : Mode debug (True/False)
- `SECRET_KEY` : Clé secrète Flask (à changer en production)
- `HOST` : Adresse IP du serveur (défaut: 127.0.0.1)
- `PORT` : Port du serveur (défaut: 5000)

### Informations Portfolio
- `PORTFOLIO_NAME` : Nom affiché dans le portfolio
- `PORTFOLIO_TITLE` : Titre professionnel
- `PORTFOLIO_EMAIL` : Email de contact
- `PORTFOLIO_DESCRIPTION` : Description du portfolio

### Configuration Base de données
- `SQLITE_DB_PATH` : Chemin vers le fichier SQLite (défaut: `portfolio.db`)

### Configuration Admin
- `ADMIN_USERNAME` : Nom d'utilisateur pour se connecter à l'interface admin (défaut: admin)
- `ADMIN_PASSWORD` : Mot de passe pour se connecter à l'interface admin (défaut: admin123)
- `ADMIN_KEY` : Clé secrète pour l'API (optionnel, pour compatibilité avec l'ancien système)

**Important :** Changez le mot de passe par défaut en production !

### Configuration Email (optionnel)
Pour recevoir des notifications par email lors de nouveaux messages de contact :
- `MAIL_SERVER` : Serveur SMTP (défaut: smtp.gmail.com)
- `MAIL_PORT` : Port SMTP (défaut: 587)
- `MAIL_USE_TLS` : Utiliser TLS (défaut: True)
- `MAIL_USERNAME` : Votre adresse email
- `MAIL_PASSWORD` : Mot de passe d'application (pour Gmail, utilisez un mot de passe d'application)
- `NOTIFICATION_EMAIL` : Email de destination pour les notifications (défaut: pricemoufromon97@gmail.com)

**Note :** Pour Gmail, vous devez créer un [mot de passe d'application](https://myaccount.google.com/apppasswords). Voir [CONFIGURATION_EMAIL.md](CONFIGURATION_EMAIL.md) pour plus de détails.

**Important :** Le fichier `.env` est ignoré par Git pour des raisons de sécurité. Ne commitez jamais vos clés secrètes !

### Base de données SQLite

L'application utilise **SQLite** comme base de données, qui est intégrée à Python. Aucune installation supplémentaire n'est nécessaire !

**Configuration (optionnelle) :**
- `SQLITE_DB_PATH` : Chemin vers le fichier de base de données (défaut: `portfolio.db`)

**Note :** La base de données SQLite sera créée automatiquement au premier démarrage de l'application dans le fichier `portfolio.db` à la racine du projet.

## Deployment

Pour le déploiement en production :

1. Configurez les variables d'environnement sur votre serveur
2. Définissez `DEBUG=False` et `FLASK_ENV=production`
3. Changez `SECRET_KEY` par une clé sécurisée
4. Utilisez un serveur WSGI comme Gunicorn :

```bash
  pip install gunicorn
  gunicorn app:app
```

Ou avec des variables d'environnement :
```bash
  gunicorn --bind 0.0.0.0:8000 app:app
```

## Tests

Pour exécuter les tests unitaires :

```bash
python -m pytest tests/
```

Ou avec unittest :

```bash
python -m unittest tests/test_basic.py
```

## Documentation API

La documentation complète de l'API est disponible dans [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Gestion des erreurs

L'application inclut :
- Pages d'erreur personnalisées (404, 500)
- Handlers d'erreur pour toutes les routes
- Validation des données côté serveur
- Messages d'erreur clairs pour l'utilisateur

## File Structure

Within the download you'll find the following directories and files:

```bash
Developer-Portfolio
.
├── app.py
├── requirements.txt
├── .gitignore
├── templates
│   ├── base.html
│   ├── index.html
│   └── components
│       ├── navbar.html
│       ├── header.html
│       ├── about.html
│       ├── about_card.html
│       └── footer.html
├── static
│   ├── favicon.ico
│   ├── css
│   │   └── globals.css
│   ├── icons
│   │   ├── code.svg
│   │   ├── design.svg
│   │   ├── facebook.svg
│   │   ├── github.svg
│   │   ├── instagram.svg
│   │   ├── linkedin.svg
│   │   ├── phone.svg
│   │   └── youtube.svg
│   └── images
│       ├── blaiti.png
│       └── partners
│           ├── artisty.png
│           ├── directy.png
│           ├── khedma-lik.png
│           ├── wallety.png
│           └── telefy.png
└── README.md
```

## Author

[@blaiti](https://github.com/)

## License>
