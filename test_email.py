"""
Script de test pour diagnostiquer les problèmes d'envoi d'email en hébergement
"""
import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print("=" * 60)
print("DIAGNOSTIC DE CONFIGURATION EMAIL")
print("=" * 60)
print()

# 1. Vérifier Flask-Mail
print("1. Vérification de Flask-Mail...")
try:
    from flask_mail import Mail, Message
    print("   ✓ Flask-Mail est installé")
except ImportError:
    print("   ✗ Flask-Mail n'est PAS installé")
    print("   Solution: pip install Flask-Mail")
    sys.exit(1)

# 2. Vérifier les variables d'environnement
print("\n2. Vérification des variables d'environnement...")
mail_server = os.getenv('MAIL_SERVER', '')
mail_port = os.getenv('MAIL_PORT', '')
mail_username = os.getenv('MAIL_USERNAME', '')
mail_password = os.getenv('MAIL_PASSWORD', '')
mail_use_tls = os.getenv('MAIL_USE_TLS', '')
notification_email = os.getenv('NOTIFICATION_EMAIL', '')

config_ok = True

if not mail_server:
    print("   ✗ MAIL_SERVER non défini")
    config_ok = False
else:
    print(f"   ✓ MAIL_SERVER = {mail_server}")

if not mail_port:
    print("   ✗ MAIL_PORT non défini")
    config_ok = False
else:
    print(f"   ✓ MAIL_PORT = {mail_port}")

if not mail_username:
    print("   ✗ MAIL_USERNAME non défini")
    config_ok = False
else:
    print(f"   ✓ MAIL_USERNAME = {mail_username}")

if not mail_password:
    print("   ✗ MAIL_PASSWORD non défini")
    config_ok = False
else:
    print(f"   ✓ MAIL_PASSWORD = {'*' * len(mail_password)} (défini)")

if not mail_use_tls:
    print("   ⚠ MAIL_USE_TLS non défini (utilisera True par défaut)")
else:
    print(f"   ✓ MAIL_USE_TLS = {mail_use_tls}")

if not notification_email:
    print("   ⚠ NOTIFICATION_EMAIL non défini (utilisera pricemoufromon97@gmail.com)")
else:
    print(f"   ✓ NOTIFICATION_EMAIL = {notification_email}")

if not config_ok:
    print("\n   ❌ Configuration incomplète - Les emails ne fonctionneront pas")
    print("   Solution: Définissez toutes les variables d'environnement requises")
    sys.exit(1)

# 3. Tester la connexion SMTP
print("\n3. Test de connexion SMTP...")
try:
    import smtplib
    import socket
    
    port = int(mail_port) if mail_port else 587
    server = mail_server if mail_server else 'smtp.gmail.com'
    
    print(f"   Tentative de connexion à {server}:{port}...")
    
    # Test de connexion réseau
    try:
        sock = socket.create_connection((server, port), timeout=10)
        sock.close()
        print(f"   ✓ Connexion réseau réussie à {server}:{port}")
    except socket.timeout:
        print(f"   ✗ TIMEOUT: Impossible de se connecter à {server}:{port}")
        print("   Solution: Vérifiez votre connexion internet et que le port n'est pas bloqué")
        sys.exit(1)
    except socket.gaierror as e:
        print(f"   ✗ ERREUR DNS: Impossible de résoudre {server}")
        print(f"   Détails: {e}")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"   ✗ CONNEXION REFUSÉE: Le serveur {server}:{port} refuse la connexion")
        print("   Solution: Vérifiez que le port SMTP est ouvert et accessible")
        sys.exit(1)
    except Exception as e:
        print(f"   ✗ ERREUR DE CONNEXION: {e}")
        sys.exit(1)
    
    # Test d'authentification SMTP
    print("   Test d'authentification SMTP...")
    try:
        if port == 465:
            # SSL
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            # TLS
            smtp = smtplib.SMTP(server, port, timeout=10)
            smtp.starttls()
        
        smtp.login(mail_username, mail_password)
        smtp.quit()
        print("   ✓ Authentification SMTP réussie")
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ✗ ERREUR D'AUTHENTIFICATION: {e}")
        print("   Solution: Vérifiez vos identifiants")
        print("   Pour Gmail: Utilisez un mot de passe d'application (pas votre mot de passe normal)")
        print("   Voir: https://myaccount.google.com/apppasswords")
        sys.exit(1)
    except Exception as e:
        print(f"   ✗ ERREUR SMTP: {e}")
        sys.exit(1)
        
except ImportError:
    print("   ⚠ smtplib non disponible (normal sur certains systèmes)")
except Exception as e:
    print(f"   ⚠ Erreur lors du test SMTP: {e}")

# 4. Test avec Flask-Mail
print("\n4. Test avec Flask-Mail...")
try:
    from flask import Flask
    
    app = Flask(__name__)
    app.config['MAIL_SERVER'] = mail_server
    app.config['MAIL_PORT'] = int(mail_port) if mail_port else 587
    app.config['MAIL_USE_TLS'] = mail_use_tls.lower() == 'true' if mail_use_tls else True
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = mail_username
    app.config['MAIL_PASSWORD'] = mail_password
    app.config['MAIL_DEFAULT_SENDER'] = mail_username
    app.config['MAIL_TIMEOUT'] = int(os.getenv('MAIL_TIMEOUT', '30'))
    
    mail = Mail(app)
    print("   ✓ Flask-Mail initialisé avec succès")
    
    # Test d'envoi (optionnel, commenté par défaut)
    test_send = os.getenv('TEST_SEND_EMAIL', 'False').lower() == 'true'
    if test_send:
        print("   Test d'envoi d'email...")
        recipient = notification_email if notification_email else 'pricemoufromon97@gmail.com'
        msg = Message(
            subject="Test d'envoi d'email",
            recipients=[recipient],
            body="Ceci est un email de test depuis votre application Flask."
        )
        mail.send(msg)
        print(f"   ✓ Email de test envoyé à {recipient}")
    else:
        print("   ⚠ Test d'envoi désactivé (définissez TEST_SEND_EMAIL=True pour tester)")
        
except Exception as e:
    print(f"   ✗ ERREUR Flask-Mail: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ DIAGNOSTIC TERMINÉ - Configuration semble correcte")
print("=" * 60)
print("\nSi les emails ne fonctionnent toujours pas en production:")
print("1. Vérifiez que les variables d'environnement sont définies sur le serveur")
print("2. Vérifiez les logs de l'application pour les erreurs détaillées")
print("3. Consultez DEPLOIEMENT_EMAIL.md pour plus d'aide")
print()

