# Guide de dépannage pour l'envoi d'emails en hébergement

Lorsque vous hébergez votre application Flask, l'envoi d'emails peut échouer pour plusieurs raisons. Ce guide vous aide à identifier et résoudre les problèmes courants.

## 🚀 Diagnostic rapide

Avant de commencer, exécutez le script de diagnostic :

```bash
python test_email.py
```

Ce script vérifie :
- ✅ Installation de Flask-Mail
- ✅ Configuration des variables d'environnement
- ✅ Connexion réseau au serveur SMTP
- ✅ Authentification SMTP
- ✅ Configuration Flask-Mail

Pour tester l'envoi réel d'email :
```bash
TEST_SEND_EMAIL=True python test_email.py
```

## 🔍 Vérifications de base

### 1. Variables d'environnement configurées

Sur votre serveur d'hébergement, assurez-vous que toutes les variables d'environnement sont configurées :

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-application
NOTIFICATION_EMAIL=email-de-destination@gmail.com
```

**Important :** Les variables d'environnement doivent être définies sur le serveur, pas seulement dans un fichier `.env` local.

### 2. Vérifier les logs

Les logs de l'application contiennent des informations détaillées sur les erreurs d'envoi d'email. Recherchez dans les logs :

- `ERREUR AUTHENTIFICATION EMAIL` : Problème d'authentification
- `ERREUR CONNEXION EMAIL` : Problème de connexion réseau
- `ERREUR TIMEOUT EMAIL` : Le serveur SMTP ne répond pas à temps

## 🚨 Problèmes courants et solutions

### Problème 1 : "Authentication failed" ou "535 Username and Password not accepted"

**Cause :** Vous utilisez votre mot de passe Gmail normal au lieu d'un mot de passe d'application.

**Solution :**
1. Activez la validation en 2 étapes sur votre compte Google : https://myaccount.google.com/security
2. Créez un mot de passe d'application : https://myaccount.google.com/apppasswords
3. Utilisez ce mot de passe de 16 caractères dans `MAIL_PASSWORD`

### Problème 2 : "Connection refused" ou "Connection timeout"

**Cause :** Le serveur d'hébergement ne peut pas se connecter au serveur SMTP.

**Solutions possibles :**

1. **Firewall bloquant le port SMTP**
   - Vérifiez que le port 587 (ou 465 pour SSL) n'est pas bloqué
   - Contactez votre hébergeur pour ouvrir les ports SMTP sortants

2. **Réseau restreint**
   - Certains hébergeurs bloquent les connexions SMTP sortantes
   - Vérifiez avec votre hébergeur si les connexions SMTP sont autorisées

3. **IP bloquée par Gmail**
   - Gmail peut bloquer les connexions depuis certaines IPs
   - Vérifiez les logs Gmail pour voir si votre IP est bloquée
   - Utilisez un service SMTP alternatif (SendGrid, Mailgun, etc.)

### Problème 3 : "Timeout" lors de l'envoi

**Cause :** Le serveur SMTP ne répond pas assez rapidement.

**Solution :** Augmentez le timeout dans vos variables d'environnement :

```bash
MAIL_TIMEOUT=60  # 60 secondes au lieu de 30
```

### Problème 4 : Les emails sont envoyés en local mais pas en production

**Cause :** Configuration différente entre l'environnement local et le serveur.

**Solutions :**

1. **Vérifiez les variables d'environnement sur le serveur**
   ```bash
   # Sur votre serveur
   echo $MAIL_USERNAME
   echo $MAIL_PASSWORD
   ```

2. **Vérifiez que Flask-Mail est installé**
   ```bash
   pip list | grep Flask-Mail
   ```

3. **Vérifiez les logs de l'application au démarrage**
   - Vous devriez voir : `Flask-Mail configure et pret (serveur: smtp.gmail.com:587)`
   - Si vous voyez : `Flask-Mail configure mais MAIL_USERNAME ou MAIL_PASSWORD manquants`, les variables ne sont pas définies

## 🔧 Solutions alternatives

### Option 1 : Utiliser un service SMTP tiers

Si Gmail ne fonctionne pas, utilisez un service dédié :

#### SendGrid
```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=votre-api-key-sendgrid
```

#### Mailgun
```bash
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=votre-username-mailgun
MAIL_PASSWORD=votre-password-mailgun
```

#### Amazon SES
```bash
MAIL_SERVER=email-smtp.region.amazonaws.com
MAIL_PORT=587
MAIL_USERNAME=votre-access-key
MAIL_PASSWORD=votre-secret-key
```

### Option 2 : Utiliser une API d'email

Au lieu de SMTP, vous pouvez utiliser une API REST :

- **SendGrid API**
- **Mailgun API**
- **Postmark**
- **Resend**

Ces services sont généralement plus fiables en hébergement car ils utilisent HTTPS au lieu de SMTP.

## 📋 Checklist de dépannage

- [ ] Variables d'environnement définies sur le serveur
- [ ] Mot de passe d'application Gmail utilisé (pas le mot de passe normal)
- [ ] Port SMTP (587 ou 465) accessible depuis le serveur
- [ ] Firewall n'bloque pas les connexions SMTP sortantes
- [ ] Flask-Mail installé sur le serveur
- [ ] Logs vérifiés pour identifier l'erreur exacte
- [ ] Test d'envoi effectué depuis le serveur

## 🧪 Tester l'envoi d'email

Pour tester si l'envoi fonctionne sur votre serveur :

1. Envoyez un message depuis le formulaire de contact
2. Vérifiez les logs de l'application
3. Vérifiez votre boîte email de destination

Si l'email n'arrive pas, vérifiez :
- Les spams/courrier indésirable
- Les logs de l'application pour les erreurs
- La configuration des variables d'environnement

## 📞 Support

Si le problème persiste :
1. Vérifiez les logs détaillés de l'application
2. Testez la connexion SMTP depuis le serveur avec `telnet` ou `openssl`
3. Contactez votre hébergeur pour vérifier les restrictions réseau
4. Considérez l'utilisation d'un service SMTP tiers plus fiable

