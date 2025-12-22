# Guide de déploiement en production

## Déploiement avec uWSGI

### Prérequis

1. Python 3.8+
2. uWSGI installé
3. Nginx (recommandé comme reverse proxy)
4. MongoDB (local ou Atlas)

### Installation

```bash
# Installer uWSGI
pip install uwsgi

# Ou via apt (Ubuntu/Debian)
sudo apt-get install uwsgi uwsgi-plugin-python3
```

### Configuration uWSGI

1. **Modifier `uwsgi.ini`** avec vos chemins :
   - `pythonpath` : Chemin vers votre projet
   - `virtualenv` : Chemin vers votre environnement virtuel
   - `socket` : Chemin du socket Unix (ou IP:PORT)

2. **Variables d'environnement** :
   Créez un fichier `.env` avec :
   ```env
   FLASK_ENV=production
   DEBUG=False
   SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
   MONGO_URI=mongodb+srv://...
   # ... autres variables
   ```

3. **Démarrer uWSGI** :
   ```bash
   uwsgi --ini uwsgi.ini
   ```

### Configuration Nginx (reverse proxy)

Créez `/etc/nginx/sites-available/portfolio` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    # Redirection HTTPS (recommandé)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Logs
    access_log /var/log/nginx/portfolio_access.log;
    error_log /var/log/nginx/portfolio_error.log;

    # Taille maximale des uploads
    client_max_body_size 10M;

    # Proxy vers uWSGI
    location / {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/portfolio.sock;
        uwsgi_read_timeout 300;
    }

    # Fichiers statiques
    location /static {
        alias /path/to/your/project/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Activez le site :
```bash
sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Service systemd pour uWSGI

Créez `/etc/systemd/system/portfolio.service` :

```ini
[Unit]
Description=uWSGI instance pour Portfolio
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/venv/bin"
ExecStart=/path/to/your/venv/bin/uwsgi --ini /path/to/your/project/uwsgi.ini

[Install]
WantedBy=multi-user.target
```

Activez et démarrez :
```bash
sudo systemctl enable portfolio
sudo systemctl start portfolio
sudo systemctl status portfolio
```

### Configuration Redis pour Rate Limiting (optionnel mais recommandé)

Si vous utilisez Redis pour Flask-Limiter :

1. Installer Redis :
   ```bash
   sudo apt-get install redis-server
   ```

2. Modifier `app.py` :
   ```python
   limiter = Limiter(
       app=app,
       key_func=get_remote_address,
       default_limits=["200 per day", "50 per hour"],
       storage_uri="redis://localhost:6379",  # Redis au lieu de memory
       strategy="fixed-window"
   )
   ```

3. Installer redis-py :
   ```bash
   pip install redis
   ```

### Vérifications

1. **Vérifier que uWSGI fonctionne** :
   ```bash
   curl http://localhost:8000
   ```

2. **Vérifier les logs** :
   ```bash
   tail -f /var/log/uwsgi/portfolio.log
   ```

3. **Vérifier les stats uWSGI** :
   ```bash
   uwsgi --connect-and-read /tmp/portfolio-stats.sock
   ```

### Sécurité en production

1. ✅ **Changer SECRET_KEY** : Utilisez une clé longue et aléatoire
2. ✅ **DEBUG=False** : Désactivez le mode debug
3. ✅ **HTTPS** : Configurez SSL/TLS avec Let's Encrypt
4. ✅ **Firewall** : Limitez l'accès aux ports nécessaires
5. ✅ **Mots de passe** : Changez tous les mots de passe par défaut
6. ✅ **Permissions** : Utilisez un utilisateur non-root pour uWSGI
7. ✅ **Logs** : Surveillez les logs régulièrement

### Monitoring

- **uWSGI Stats** : Accédez à `/stats` pour les statistiques
- **Logs** : Surveillez `/var/log/uwsgi/portfolio.log`
- **Nginx Logs** : Surveillez `/var/log/nginx/portfolio_*.log`

### Redémarrage

```bash
# Redémarrer uWSGI
sudo systemctl restart portfolio

# Recharger la configuration
sudo systemctl reload portfolio

# Redémarrer Nginx
sudo systemctl restart nginx
```

### Dépannage

**Erreur "ModuleNotFoundError"** :
- Vérifiez que `pythonpath` et `virtualenv` sont corrects dans `uwsgi.ini`

**Erreur "Permission denied"** :
- Vérifiez les permissions du socket Unix
- Vérifiez que l'utilisateur uWSGI peut accéder aux fichiers

**Erreur "Address already in use"** :
- Changez le port ou le socket dans `uwsgi.ini`
- Arrêtez les autres instances

**Application ne répond pas** :
- Vérifiez les logs : `tail -f /var/log/uwsgi/portfolio.log`
- Vérifiez que MongoDB est accessible
- Vérifiez les variables d'environnement


