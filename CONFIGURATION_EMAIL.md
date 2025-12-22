# Configuration de l'envoi d'emails

Pour recevoir des notifications par email lorsqu'un nouveau message de contact est reçu, vous devez configurer les variables d'environnement suivantes dans votre fichier `.env`.

## ⚠️ Erreur "535 Username and Password not accepted"

Si vous voyez cette erreur dans les logs, c'est que vous utilisez votre **mot de passe Gmail normal** au lieu d'un **mot de passe d'application**. Gmail ne permet plus l'utilisation de mots de passe normaux pour les applications tierces depuis mai 2022.

## Configuration Gmail

### ⚠️ IMPORTANT : Erreur d'authentification

Si vous voyez l'erreur `535-5.7.8 Username and Password not accepted`, cela signifie que vous devez utiliser un **mot de passe d'application** et non votre mot de passe Gmail normal.

### Étape 1 : Activer la validation en 2 étapes (OBLIGATOIRE)

1. Allez sur https://myaccount.google.com/security
2. Dans la section "Connexion à Google", cliquez sur "Validation en deux étapes"
3. Suivez les instructions pour activer la validation en 2 étapes
4. **C'est obligatoire** - Gmail ne permet plus l'utilisation de mots de passe normaux pour les applications tierces

### Étape 2 : Créer un mot de passe d'application

1. Allez sur https://myaccount.google.com/apppasswords
   - Ou : Compte Google > Sécurité > Validation en deux étapes > Mots de passe des applications
2. Sélectionnez "Autre (nom personnalisé)" dans le menu déroulant
3. Entrez un nom (ex: "Portfolio Flask")
4. Cliquez sur "Générer"
5. **Copiez le mot de passe de 16 caractères** (sans espaces) - vous ne pourrez plus le voir après !
6. Utilisez ce mot de passe dans `MAIL_PASSWORD` dans votre `.env`

### Étape 2 : Configurer le fichier .env

Ajoutez ces lignes dans votre fichier `.env` :

```env
# Configuration Email (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-application-16-caracteres
NOTIFICATION_EMAIL=pricemoufromon97@gmail.com
```

**Important :**
- `MAIL_USERNAME` : Votre adresse Gmail complète
- `MAIL_PASSWORD` : Le mot de passe d'application (16 caractères) généré par Google, **PAS** votre mot de passe Gmail normal
- `NOTIFICATION_EMAIL` : L'adresse email où vous voulez recevoir les notifications (par défaut: pricemoufromon97@gmail.com)

## Configuration autres fournisseurs

### Outlook/Hotmail
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@outlook.com
MAIL_PASSWORD=votre-mot-de-passe
```

### Yahoo
```env
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@yahoo.com
MAIL_PASSWORD=votre-mot-de-passe-application
```

## Vérification

Après avoir configuré les variables, redémarrez l'application Flask. Vous devriez voir dans les logs :

```
Flask-Mail configure et pret
```

Lorsqu'un message de contact est reçu, vous verrez dans les logs :

```
Email de notification envoye a pricemoufromon97@gmail.com pour le message de ...
```

## Dépannage

### L'email n'est pas envoyé

1. **Vérifiez les logs** : Regardez les messages dans la console Flask pour voir les erreurs
2. **Vérifiez la configuration** : Assurez-vous que `MAIL_USERNAME` et `MAIL_PASSWORD` sont bien définis
3. **Pour Gmail** : Utilisez un mot de passe d'application, pas votre mot de passe normal
4. **Vérifiez le firewall** : Assurez-vous que le port 587 n'est pas bloqué

### Erreurs courantes

- **"Authentication failed"** : Vérifiez que vous utilisez un mot de passe d'application pour Gmail
- **"Connection refused"** : Vérifiez `MAIL_SERVER` et `MAIL_PORT`
- **"Timeout"** : Vérifiez votre connexion internet et le firewall

## Test

Pour tester l'envoi d'email, envoyez un message depuis le formulaire de contact sur `/contact`. Si tout est configuré correctement, vous recevrez un email à l'adresse `NOTIFICATION_EMAIL`.

