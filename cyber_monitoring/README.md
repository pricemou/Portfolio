# Monitoring cybersécurité

Tableau de bord interactif (données **simulées**) pour le portfolio.

## Sur le site (recommandé)

Tout est intégré dans l’admin Flask : `/admin/cyber`

1. Installer les dépendances : `pip install -r requirements.txt`
2. Générer le CSV (si absent) :
   ```bash
   python -m cyber_monitoring.generate_events
   ```
3. Lancer le portfolio :
   ```bash
   python app.py
   ```
4. Ouvrir `/admin/cyber`

## Streamlit (même moteur de données)

```bash
pip install -r requirements.txt
python -m cyber_monitoring.generate_events
streamlit run cyber_monitoring/streamlit_app.py
```

Les IP utilisées sont des plages de documentation (RFC 5737) : `203.0.113.x`, `198.51.100.x`, `192.0.2.x`.
