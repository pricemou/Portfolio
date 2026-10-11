# Monitoring cybersécurité (portfolio)

Tableau de bord interactif **Streamlit + Plotly**, aussi servi sur le site Flask à l’URL **`/dashboard`**.

Les données sont **entièrement simulées** (IP de documentation RFC 5737). Aucune donnée personnelle réelle.

## Contenu

| Fichier | Rôle |
|---------|------|
| `generate_events.py` | Génère `events.csv` (50 000 lignes / 30 jours) |
| `events.csv` | Jeu de données (ou reprise de `../cyber-monitoring/events.csv`) |
| `engine.py` | Chargement, filtres, agrégats (partagé Flask + Streamlit) |
| `app.py` | Application Streamlit |
| `requirements.txt` | Dépendances Streamlit |

## Générer les données

```bash
cd dashboard
python generate_events.py
```

Optionnel : `python generate_events.py -n 50000 -o events.csv`

## Lancer Streamlit

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Puis ouvrir l’URL affichée (souvent http://localhost:8501).

## Voir sur le site portfolio

1. Installer aussi côté Flask : `pandas` et `numpy` (déjà utilisés par le moteur).
2. Lancer le site : `python app.py` (ou le launcher habituel).
3. Ouvrir **`/dashboard`** dans le menu « Dashboard ».

Téléversement CSV : bouton dans la barre latérale (mêmes colonnes que `events.csv`).

## Colonnes CSV attendues

`horodatage`, `adresse_ip`, `pays`, `ville`, `latitude`, `longitude`, `service_cible`, `compte_vise`, `type_utilisateur`, `type_activite`, `gravite`
