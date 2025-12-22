# Correction des erreurs en hébergement

## Erreurs corrigées

### 1. ✅ Erreurs d'indentation (lignes 799, 882, 903)

Les erreurs d'indentation dans les fonctions suivantes ont été corrigées :
- `delete_skill_api()` - ligne 799
- `update_partner_api()` - ligne 882  
- `delete_partner_api()` - ligne 903

**Statut :** ✅ Corrigé dans le code local

### 2. ⚠️ ModuleNotFoundError: No module named 'flask_limiter'

**Problème :** Le fichier `app.py` sur le serveur contient un import direct de `flask_limiter` qui n'existe pas dans le fichier local.

**Solution :** Vous devez soit :

#### Option A : Installer Flask-Limiter (recommandé)

Sur PythonAnywhere, ouvrez un **Bash Console** et exécutez :

```bash
pip3.10 install --user Flask-Limiter==3.5.0
```

Ou installez toutes les dépendances :

```bash
pip3.10 install --user -r requirements.txt
```

#### Option B : Rendre l'import conditionnel (si vous ne voulez pas utiliser Flask-Limiter)

Si le fichier `app.py` sur le serveur contient un import comme :
```python
from flask_limiter import Limiter
```

Remplacez-le par un import conditionnel :
```python
# Flask-Limiter (optionnel)
FLASK_LIMITER_AVAILABLE = False
Limiter = None
try:
    from flask_limiter import Limiter
    FLASK_LIMITER_AVAILABLE = True
except ImportError:
    print("Flask-Limiter non installé - le rate limiting sera désactivé")
```

### 3. ⚠️ MONGO_URI non défini

**Problème :** La variable d'environnement `MONGO_URI` n'est pas définie sur le serveur.

**Solution :** Sur PythonAnywhere :

1. Allez dans l'onglet **Web**
2. Cliquez sur votre application
3. Dans la section **Environment variables**, ajoutez :
   - `MONGO_URI` = votre URI MongoDB (ex: `mongodb+srv://username:password@cluster.mongodb.net/`)
   - `MONGO_DB_NAME` = `portfolio_db` (ou le nom de votre choix)

4. **Redémarrez l'application** après avoir ajouté les variables

### 4. ⚠️ The CSRF token is missing

**Problème :** Les requêtes API échouent car le token CSRF est manquant.

**Solution :** Si vous utilisez Flask-WTF, assurez-vous que :
1. Flask-WTF est installé : `pip3.10 install --user Flask-WTF`
2. Les requêtes API incluent le token CSRF (généré automatiquement par Flask-WTF)

Si vous ne voulez pas utiliser CSRF pour les API (déjà protégées par authentification admin), vous pouvez désactiver CSRF pour certaines routes.

## Actions à faire sur le serveur

1. **Télécharger le fichier `app.py` corrigé** depuis votre dépôt local
2. **Vérifier les imports** - Assurez-vous qu'il n'y a pas d'import direct de `flask_limiter` sans gestion d'erreur
3. **Ajouter les variables d'environnement** `MONGO_URI` et `MONGO_DB_NAME`
4. **Installer les dépendances manquantes** :
   ```bash
   pip3.10 install --user Flask-Limiter Flask-WTF bcrypt bleach
   ```
5. **Redémarrer l'application** dans l'onglet Web de PythonAnywhere

## Vérification

Après avoir fait ces corrections, vérifiez que :
- ✅ L'application démarre sans erreur
- ✅ MongoDB se connecte (vérifiez les logs : `✅ Connexion MongoDB réussie`)
- ✅ Les routes API fonctionnent
- ✅ L'espace admin peut récupérer les données

## Logs à surveiller

Messages positifs :
- `✅ Connexion MongoDB réussie`
- `Flask-Mail configure et pret`
- `WSGI app 0 (mountpoint='') ready`

Messages d'erreur à corriger :
- `ModuleNotFoundError: No module named 'flask_limiter'` → Installer Flask-Limiter
- `MONGO_URI non défini` → Ajouter la variable d'environnement
- `IndentationError` → Vérifier le fichier app.py
- `The CSRF token is missing` → Vérifier Flask-WTF

