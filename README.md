# Claude Pricemou — Portfolio

Site : [https://claude225.pythonanywhere.com/](https://claude225.pythonanywhere.com/)  
Code : [https://github.com/pricemou/Portfolio](https://github.com/pricemou/Portfolio)

Portfolio de **Claude Pricemou**, développeur Full Stack & science des données, freelance à Trois-Rivières (Québec).

## Stack

- Backend : Python / Flask / Jinja2
- Base : SQLite
- Frontend : HTML, CSS, JS (thème clair / sombre, FR / EN)

## Lancer en local (Windows)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install Flask==3.0.0 Werkzeug==3.0.1 python-dotenv==1.0.0 Flask-WTF==1.2.1 WTForms==3.1.1 Flask-Mail==0.10.0 Flask-Limiter==3.5.0 bcrypt==4.1.2 bleach==6.1.0
copy .env.example .env
python app.py
```

Ouvrir `http://127.0.0.1:5000`.

`uwsgi` n’est pas requis sous Windows. En production Linux, Gunicorn ou le WSGI de l’hébergeur suffit.

## Pages

| Route | Contenu |
|--------|---------|
| `/` | Accueil, à propos, chiffres, références |
| `/parcours` | Chronologie |
| `/works` | Projets (filtres Pro / Data / Académique) |
| `/services` | Offres et devis |
| `/contact` | Formulaire (anti-spam) |
| `/cv` | Téléchargement du CV |
| `/admin` | Administration (non listée dans le menu public) |

## Captures

Remplacer ces fichiers par de vraies captures après déploiement :

- Accueil : `static/images/claude-pricemou.svg` (placeholder tant qu’une photo pro n’est pas fournie)
- Projets et services : pages `/works` et `/services`

## Sécurité

Ne commitez jamais `.env` ni `portfolio.db`. Copiez `.env.example` et changez `SECRET_KEY` et `ADMIN_PASSWORD`.

## Licence

MIT — contenu et marque : Claude Pricemou.
