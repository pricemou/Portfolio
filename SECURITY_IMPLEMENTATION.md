# Guide d'implémentation de la sécurité

## Modifications apportées

### 1. Rate Limiting avec Flask-Limiter
- Limite par défaut : 200 requêtes/jour, 50/heure
- Routes API spécifiques :
  - `/api/homepage` (PUT) : 10/minute
  - `/api/projects` (POST) : 20/minute
  - `/api/contact` (POST) : 5/minute (public)
  - Routes admin : 30/minute

### 2. CSRF Protection avec Flask-WTF
- CSRF activé pour tous les formulaires
- Routes API exemptées avec `@csrf.exempt` (authentification admin requise)
- Token CSRF généré automatiquement pour les formulaires HTML

### 3. Chiffrement bcrypt
- Remplacement de SHA256 par bcrypt (12 rounds)
- Migration automatique des mots de passe SHA256 vers bcrypt
- Fonction `check_password()` compatible avec les deux formats

### 4. Validation XSS améliorée
- Utilisation de `bleach` pour nettoyer le HTML
- `sanitize_input_advanced()` pour échapper les caractères spéciaux
- Tags HTML autorisés limités
- Attributs HTML autorisés restreints

## Installation

```bash
pip install -r requirements.txt
```

## Migration des mots de passe

Les mots de passe existants en SHA256 seront automatiquement migrés vers bcrypt lors de la prochaine connexion réussie.

## Configuration

Les limites de rate limiting peuvent être ajustées dans `app.py` :

```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Utiliser Redis en production
    strategy="fixed-window"
)
```

Pour la production, utilisez Redis :
```python
storage_uri="redis://localhost:6379"
```


