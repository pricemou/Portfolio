# Diagnostic MongoDB - Problème de récupération des données en hébergement

## Problème

L'espace admin n'arrive pas à récupérer les informations de la base de données en hébergement.

## Solutions implémentées

### 1. Reconnexion automatique MongoDB

Une fonction `ensure_mongo_connection()` a été ajoutée qui :
- Vérifie si la connexion MongoDB est toujours active
- Réessaie de se reconnecter automatiquement si la connexion est perdue
- Log les erreurs pour faciliter le diagnostic

### 2. Route de diagnostic

Une nouvelle route `/api/admin/mongo-status` permet de vérifier l'état de MongoDB :
- Statut de la connexion
- Collections disponibles
- Nombre de documents par collection
- Erreurs éventuelles

## Vérifications à faire en hébergement

### 1. Vérifier les variables d'environnement

Assurez-vous que les variables suivantes sont bien définies dans votre configuration d'hébergement :

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=portfolio_db
```

**Important :**
- Sur PythonAnywhere : Ajoutez ces variables dans l'onglet **Web** > **Environment variables**
- Sur Heroku : Utilisez `heroku config:set MONGO_URI=...`
- Sur un VPS : Vérifiez que le fichier `.env` est bien chargé

### 2. Vérifier la connexion MongoDB

#### Option A : Via la route de diagnostic (recommandé)

1. Connectez-vous à l'espace admin
2. Ouvrez la console du navigateur (F12)
3. Exécutez :
```javascript
fetch('/api/admin/mongo-status')
  .then(r => r.json())
  .then(data => console.log(data));
```

Vous devriez voir :
- `connection_status: "connected"` si tout fonctionne
- `connection_status: "disconnected"` ou `"error"` si problème

#### Option B : Via les logs du serveur

Vérifiez les logs de votre application pour voir les messages :
- `✅ Connexion MongoDB réussie` = OK
- `⚠️ MONGO_URI non défini` = Variable d'environnement manquante
- `❌ Erreur de connexion MongoDB` = Problème de connexion

### 3. Vérifier MongoDB Atlas (si utilisé)

Si vous utilisez MongoDB Atlas :

1. **Vérifiez que votre IP est autorisée** :
   - Allez dans **Network Access** sur MongoDB Atlas
   - Ajoutez `0.0.0.0/0` pour autoriser toutes les IPs (ou votre IP spécifique)

2. **Vérifiez vos identifiants** :
   - Le `MONGO_URI` doit contenir le bon username/password
   - Format : `mongodb+srv://username:password@cluster.mongodb.net/`

3. **Vérifiez que le cluster est actif** :
   - Le cluster ne doit pas être en pause (clusters gratuits se mettent en pause après inactivité)

### 4. Vérifier les permissions de la base de données

Assurez-vous que l'utilisateur MongoDB a les permissions nécessaires :
- `readWrite` sur la base de données `portfolio_db`
- Ou `readWriteAnyDatabase` si vous utilisez plusieurs bases

## Problèmes courants et solutions

### Problème : `MONGO_URI non défini`

**Solution :**
- Vérifiez que la variable d'environnement `MONGO_URI` est bien définie
- Sur PythonAnywhere : Redémarrez l'application après avoir ajouté la variable
- Vérifiez que le fichier `.env` est bien lu (sur VPS)

### Problème : `Connection refused` ou `Timeout`

**Solutions :**
1. Vérifiez votre connexion internet
2. Vérifiez que MongoDB Atlas autorise votre IP
3. Vérifiez que le cluster MongoDB n'est pas en pause
4. Augmentez les timeouts dans `database.py` si nécessaire

### Problème : `Authentication failed`

**Solutions :**
1. Vérifiez que le username/password dans `MONGO_URI` est correct
2. Vérifiez que l'utilisateur existe dans MongoDB Atlas
3. Vérifiez que l'utilisateur a les bonnes permissions

### Problème : Les données ne se chargent pas mais la connexion fonctionne

**Solutions :**
1. Vérifiez que les collections existent dans MongoDB
2. Utilisez la route `/api/admin/mongo-status` pour voir les collections disponibles
3. Vérifiez que les données existent dans les collections
4. Vérifiez les logs du serveur pour voir les erreurs spécifiques

## Test de connexion manuel

Pour tester la connexion MongoDB depuis Python :

```python
from pymongo import MongoClient
import os

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['portfolio_db']

# Tester la connexion
client.admin.command('ping')
print("✅ Connexion réussie")

# Lister les collections
print("Collections:", db.list_collection_names())

# Compter les documents
for collection_name in db.list_collection_names():
    count = db[collection_name].count_documents({})
    print(f"{collection_name}: {count} documents")
```

## Logs à surveiller

Surveillez ces messages dans les logs :

- `✅ Connexion MongoDB réussie` = Tout fonctionne
- `⚠️ MONGO_URI non défini` = Variable manquante
- `❌ Erreur de connexion MongoDB` = Problème de connexion
- `✅ Reconnexion MongoDB réussie` = Reconnexion automatique réussie
- `MongoDB non disponible pour [route]` = La route ne peut pas accéder à MongoDB

## Support

Si le problème persiste après avoir vérifié tous ces points :

1. Vérifiez les logs complets de l'application
2. Testez la connexion MongoDB manuellement (voir ci-dessus)
3. Vérifiez que toutes les variables d'environnement sont correctes
4. Contactez le support de votre hébergeur si nécessaire

