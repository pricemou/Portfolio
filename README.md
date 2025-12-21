# Developer Portfolio

![licence](https://img.shields.io/badge/licence-MIT-blue)

Developer Portfolio is a web template made for developers to present themselves based on Flask.

![Developer Protfolio](https://user-images.githubusercontent.com/32510139/196662875-44970df4-d748-4a76-8a5f-ec2f4f0eb0e9.png)

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

## Run Locally

Pour exécuter l'application localement, assurez-vous que l'environnement virtuel est activé, puis exécutez :

```bash
  python app.py
```

L'application sera disponible sur `http://localhost:5000`

**Note:** Pour désactiver l'environnement virtuel, tapez simplement `deactivate` dans le terminal.

## Deployment

For production deployment, use a WSGI server like Gunicorn:

```bash
  pip install gunicorn
  gunicorn app:app
```

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
