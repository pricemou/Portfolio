# Installation sur PythonAnywhere

## Problème courant : Modules manquants

Si vous voyez des erreurs comme `ModuleNotFoundError: No module named 'flask_limiter'`, vous devez installer les dépendances.

## Solution 1 : Installer via le Bash Console (recommandé)

1. Ouvrez un **Bash Console** sur PythonAnywhere
2. Activez votre environnement virtuel (si vous en avez un) :
   ```bash
   source /home/Claude225/.virtualenvs/portfolio/bin/activate
   ```
   Ou si vous utilisez un venv dans votre projet :
   ```bash
   source /home/Claude225/Portfolio/venv/bin/activate
   ```

3. Installez les dépendances :
   ```bash
   pip install --user Flask-Limiter Flask-WTF bcrypt bleach
   ```

   Ou installez toutes les dépendances depuis requirements.txt :
   ```bash
   pip install --user -r requirements.txt
   ```

## Solution 2 : Utiliser le Web Interface de PythonAnywhere

1. Allez dans l'onglet **Web** de votre dashboard
2. Cliquez sur **"Open a bash console here"**
3. Exécutez les commandes d'installation ci-dessus

## Solution 3 : Fallback automatique (déjà implémenté)

L'application a été modifiée pour fonctionner **sans** Flask-Limiter et Flask-WTF si ces modules ne sont pas installés. Cependant, certaines fonctionnalités seront désactivées :

- **Sans Flask-Limiter** : Le rate limiting sera désactivé (moins sécurisé)
- **Sans Flask-WTF** : La protection CSRF sera désactivée (moins sécurisé)

## Vérification de l'installation

Pour vérifier que les modules sont installés :

```bash
python3.10 -m pip list | grep -i flask
```

Vous devriez voir :
- Flask
- Flask-Limiter
- Flask-WTF
- Flask-Mail

## Installation complète des dépendances

```bash
pip install --user Flask==3.0.0 Werkzeug==3.0.1 python-dotenv==1.0.0 pymongo==4.6.1 Flask-WTF==1.2.1 WTForms==3.1.1 Flask-Mail==0.10.0 Flask-Limiter==3.5.0 bcrypt==4.1.2 bleach==6.1.0
```

## Après l'installation

1. **Redémarrez votre application Web** dans l'onglet Web de PythonAnywhere
2. Vérifiez les logs pour confirmer que tout fonctionne
3. Les messages d'avertissement devraient disparaître

## Note importante

Sur PythonAnywhere, utilisez `pip install --user` pour installer les packages dans votre répertoire utilisateur, car vous n'avez pas les droits root.

