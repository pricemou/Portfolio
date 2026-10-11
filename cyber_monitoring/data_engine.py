"""
Moteur de données pour le tableau de bord cybersécurité.
Génère, charge, filtre et agrège les événements (CSV simulé).
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Colonnes obligatoires du CSV
REQUIRED_COLUMNS = [
    'horodatage',
    'adresse_ip',
    'pays',
    'ville',
    'latitude',
    'longitude',
    'service_cible',
    'compte_vise',
    'type_utilisateur',
    'type_activite',
    'gravite',
]

GRAVITE_SCORE = {'faible': 1, 'moyenne': 2, 'elevee': 3, 'élevée': 3, 'critique': 4}
GRAVITE_LABELS = ['faible', 'moyenne', 'élevée', 'critique']
SERVICES = ['SSH', 'RDP', 'HTTP', 'MySQL']
COMPTES = ['root', 'admin', 'administrator', 'user']
TYPES_USER = ['légitime', 'robot', 'suspect']
ACTIVITES = [
    'connexion réussie',
    'échec de connexion',
    'scan de ports',
    'force brute',
    'injection SQL',
]

# Lieux fictifs (IP documentation RFC 5737) — aucune donnée personnelle réelle
LOCATIONS = [
    {'pays': 'France', 'ville': 'Paris', 'lat': 48.8566, 'lon': 2.3522, 'net': '203.0.113'},
    {'pays': 'France', 'ville': 'Lyon', 'lat': 45.7640, 'lon': 4.8357, 'net': '203.0.113'},
    {'pays': 'Allemagne', 'ville': 'Berlin', 'lat': 52.5200, 'lon': 13.4050, 'net': '198.51.100'},
    {'pays': 'Allemagne', 'ville': 'Munich', 'lat': 48.1351, 'lon': 11.5820, 'net': '198.51.100'},
    {'pays': 'États-Unis', 'ville': 'New York', 'lat': 40.7128, 'lon': -74.0060, 'net': '192.0.2'},
    {'pays': 'États-Unis', 'ville': 'San Francisco', 'lat': 37.7749, 'lon': -122.4194, 'net': '192.0.2'},
    {'pays': 'Royaume-Uni', 'ville': 'Londres', 'lat': 51.5074, 'lon': -0.1278, 'net': '203.0.113'},
    {'pays': 'Brésil', 'ville': 'São Paulo', 'lat': -23.5505, 'lon': -46.6333, 'net': '198.51.100'},
    {'pays': 'Japon', 'ville': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503, 'net': '192.0.2'},
    {'pays': 'Inde', 'ville': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777, 'net': '203.0.113'},
    {'pays': 'Canada', 'ville': 'Montréal', 'lat': 45.5017, 'lon': -73.5673, 'net': '198.51.100'},
    {'pays': 'Australie', 'ville': 'Sydney', 'lat': -33.8688, 'lon': 151.2093, 'net': '192.0.2'},
]

# IP récurrentes pour simuler des campagnes de force brute nocturnes
BRUTE_FORCE_IPS = [
    '203.0.113.44',
    '203.0.113.91',
    '198.51.100.17',
    '198.51.100.220',
    '192.0.2.66',
    '192.0.2.199',
]


def default_events_path() -> Path:
    """Chemin par défaut du CSV simulé dans le projet."""
    return Path(__file__).resolve().parent / 'events.csv'


def generate_events_dataframe(n_events: int = 50_000, days: int = 30, seed: int = 42) -> pd.DataFrame:
    """
    Génère un jeu d'événements simulés.
    Inclut un pic de force brute la nuit avec des IP récurrentes.
    """
    rng = np.random.default_rng(seed)
    end = datetime.now().replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)

    # ~72 % trafic de fond + ~28 % pic nocturne force brute
    n_background = int(n_events * 0.72)
    n_spike = n_events - n_background

    rows: list[dict[str, Any]] = []

    def _pick_location():
        return LOCATIONS[int(rng.integers(0, len(LOCATIONS)))]

    def _random_ip(net: str) -> str:
        return f'{net}.{int(rng.integers(1, 254))}'

    # Trafic de fond
    for _ in range(n_background):
        loc = _pick_location()
        ts = start + timedelta(seconds=float(rng.integers(0, int(days * 86400))))
        hour = ts.hour
        # Légère hausse d'activité en journée
        user_weights = [0.55, 0.25, 0.20] if 8 <= hour <= 20 else [0.35, 0.35, 0.30]
        activity_weights = [0.35, 0.30, 0.15, 0.12, 0.08]
        grav_weights = [0.45, 0.30, 0.18, 0.07]
        activity = rng.choice(ACTIVITES, p=activity_weights)
        user_type = rng.choice(TYPES_USER, p=user_weights)
        if activity == 'connexion réussie':
            gravite = 'faible'
            user_type = 'légitime' if rng.random() < 0.7 else user_type
        elif activity in ('force brute', 'injection SQL'):
            gravite = rng.choice(['élevée', 'critique'], p=[0.55, 0.45])
            user_type = rng.choice(['robot', 'suspect'], p=[0.4, 0.6])
        else:
            gravite = rng.choice(GRAVITE_LABELS, p=grav_weights)

        rows.append({
            'horodatage': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'adresse_ip': _random_ip(loc['net']),
            'pays': loc['pays'],
            'ville': loc['ville'],
            'latitude': loc['lat'] + float(rng.normal(0, 0.08)),
            'longitude': loc['lon'] + float(rng.normal(0, 0.08)),
            'service_cible': rng.choice(SERVICES, p=[0.35, 0.20, 0.30, 0.15]),
            'compte_vise': rng.choice(COMPTES, p=[0.35, 0.30, 0.15, 0.20]),
            'type_utilisateur': user_type,
            'type_activite': activity,
            'gravite': gravite,
        })

    # Pic nocturne force brute (00h–05h) avec IP récurrentes
    for _ in range(n_spike):
        day_offset = int(rng.integers(0, days))
        hour = int(rng.choice([0, 1, 2, 3, 4, 5], p=[0.12, 0.18, 0.25, 0.22, 0.15, 0.08]))
        minute = int(rng.integers(0, 60))
        second = int(rng.integers(0, 60))
        ts = (start + timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=second)
        ip = rng.choice(BRUTE_FORCE_IPS)
        # Associer l'IP à un lieu cohérent avec son préfixe
        if ip.startswith('203.0.113'):
            candidates = [l for l in LOCATIONS if l['net'] == '203.0.113']
        elif ip.startswith('198.51.100'):
            candidates = [l for l in LOCATIONS if l['net'] == '198.51.100']
        else:
            candidates = [l for l in LOCATIONS if l['net'] == '192.0.2']
        loc = candidates[int(rng.integers(0, len(candidates)))]
        activity = rng.choice(
            ['force brute', 'échec de connexion', 'scan de ports'],
            p=[0.65, 0.25, 0.10],
        )
        gravite = rng.choice(['élevée', 'critique', 'moyenne'], p=[0.45, 0.40, 0.15])
        rows.append({
            'horodatage': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'adresse_ip': ip,
            'pays': loc['pays'],
            'ville': loc['ville'],
            'latitude': loc['lat'] + float(rng.normal(0, 0.05)),
            'longitude': loc['lon'] + float(rng.normal(0, 0.05)),
            'service_cible': rng.choice(['SSH', 'RDP', 'MySQL'], p=[0.55, 0.30, 0.15]),
            'compte_vise': rng.choice(['root', 'admin', 'administrator'], p=[0.5, 0.35, 0.15]),
            'type_utilisateur': rng.choice(['robot', 'suspect'], p=[0.55, 0.45]),
            'type_activite': activity,
            'gravite': gravite,
        })

    df = pd.DataFrame(rows)
    df['horodatage'] = pd.to_datetime(df['horodatage'])
    df = df.sort_values('horodatage').reset_index(drop=True)
    return df


def save_events_csv(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Enregistre le DataFrame au format CSV."""
    path = path or default_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out['horodatage'] = pd.to_datetime(out['horodatage']).dt.strftime('%Y-%m-%d %H:%M:%S')
    out.to_csv(path, index=False, encoding='utf-8')
    return path


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les noms de colonnes et types."""
    rename = {c: c.strip().lower() for c in df.columns}
    # Alias éventuels
    aliases = {
        'timestamp': 'horodatage',
        'ip': 'adresse_ip',
        'country': 'pays',
        'city': 'ville',
        'lat': 'latitude',
        'lon': 'longitude',
        'lng': 'longitude',
        'service': 'service_cible',
        'account': 'compte_vise',
        'user_type': 'type_utilisateur',
        'activity': 'type_activite',
        'type_activité': 'type_activite',
        'severity': 'gravite',
        'gravité': 'gravite',
    }
    df = df.rename(columns=rename)
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f'Colonnes manquantes: {", ".join(missing)}')
    df = df[REQUIRED_COLUMNS].copy()
    df['horodatage'] = pd.to_datetime(df['horodatage'], errors='coerce')
    df = df.dropna(subset=['horodatage'])
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['gravite'] = df['gravite'].astype(str).str.lower().str.replace('elevee', 'élevée', regex=False)
    return df.reset_index(drop=True)


def load_events(source: Path | str | bytes | io.BytesIO | None = None) -> pd.DataFrame:
    """Charge un CSV d'événements (chemin, bytes upload, ou fichier par défaut)."""
    if source is None:
        path = default_events_path()
        if not path.exists():
            df = generate_events_dataframe()
            save_events_csv(df, path)
            return df
        source = path
    if isinstance(source, (bytes, bytearray)):
        df = pd.read_csv(io.BytesIO(source))
    elif isinstance(source, io.BytesIO):
        df = pd.read_csv(source)
    else:
        df = pd.read_csv(source)
    return _normalize_columns(df)


def apply_filters(
    df: pd.DataFrame,
    *,
    date_start: str | None = None,
    date_end: str | None = None,
    pays: list[str] | None = None,
    type_activite: list[str] | None = None,
    gravite: list[str] | None = None,
    type_utilisateur: list[str] | None = None,
    service_cible: list[str] | None = None,
) -> pd.DataFrame:
    """Applique les filtres du tableau de bord."""
    out = df
    if date_start:
        out = out[out['horodatage'] >= pd.to_datetime(date_start)]
    if date_end:
        # Inclure toute la journée de fin
        end = pd.to_datetime(date_end) + timedelta(days=1) - timedelta(seconds=1)
        out = out[out['horodatage'] <= end]
    if pays:
        out = out[out['pays'].isin(pays)]
    if type_activite:
        out = out[out['type_activite'].isin(type_activite)]
    if gravite:
        g = [x.lower().replace('elevee', 'élevée') for x in gravite]
        out = out[out['gravite'].isin(g)]
    if type_utilisateur:
        out = out[out['type_utilisateur'].isin(type_utilisateur)]
    if service_cible:
        out = out[out['service_cible'].isin(service_cible)]
    return out


def build_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Chiffres clés."""
    total = int(len(df))
    fails = int((df['type_activite'] == 'échec de connexion').sum()) if total else 0
    return {
        'total_evenements': total,
        'ip_uniques': int(df['adresse_ip'].nunique()) if total else 0,
        'taux_echec': round((fails / total) * 100, 1) if total else 0.0,
        'alertes_critiques': int((df['gravite'] == 'critique').sum()) if total else 0,
        'nb_pays': int(df['pays'].nunique()) if total else 0,
    }


def build_map_bubbles(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Agrégation géo pour la carte à bulles."""
    if df.empty:
        return []
    grouped = df.groupby(['pays', 'ville'], as_index=False).agg(
        latitude=('latitude', 'mean'),
        longitude=('longitude', 'mean'),
        evenements=('adresse_ip', 'count'),
        gravite_moyenne_score=('gravite', lambda s: float(s.map(lambda x: GRAVITE_SCORE.get(str(x).lower(), 1)).mean())),
    )
    grouped['gravite_moyenne'] = grouped['gravite_moyenne_score'].map(
        lambda m: 'critique' if m >= 3.5 else 'élevée' if m >= 2.5 else 'moyenne' if m >= 1.5 else 'faible'
    )
    return grouped.drop(columns=['gravite_moyenne_score']).to_dict(orient='records')


def build_timeline(df: pd.DataFrame, granularity: str = 'heure') -> dict[str, Any]:
    """Série temporelle + seuil d'anomalie (moyenne + 2σ)."""
    if df.empty:
        return {'points': [], 'seuil': 0, 'granularity': granularity}
    tmp = df.copy()
    if granularity == 'jour':
        tmp['bucket'] = tmp['horodatage'].dt.floor('D')
    else:
        tmp['bucket'] = tmp['horodatage'].dt.floor('h')
    counts = tmp.groupby('bucket').size().reset_index(name='count')
    mean = float(counts['count'].mean()) if len(counts) else 0.0
    std = float(counts['count'].std(ddof=0)) if len(counts) else 0.0
    seuil = mean + 2 * std
    points = []
    for _, row in counts.iterrows():
        c = int(row['count'])
        points.append({
            'horodatage': row['bucket'].strftime('%Y-%m-%d %H:%M:%S'),
            'count': c,
            'anomalie': c > seuil,
        })
    return {'points': points, 'seuil': round(seuil, 2), 'granularity': granularity}


def build_top10(df: pd.DataFrame, dimension: str = 'adresse_ip') -> list[dict[str, Any]]:
    """Top 10 selon la dimension choisie."""
    allowed = {
        'adresse_ip': 'adresse_ip',
        'compte_vise': 'compte_vise',
        'pays': 'pays',
        'service_cible': 'service_cible',
    }
    col = allowed.get(dimension, 'adresse_ip')
    if df.empty:
        return []
    top = df[col].value_counts().head(10)
    return [{'label': str(k), 'count': int(v)} for k, v in top.items()]


def build_donut(df: pd.DataFrame, mode: str = 'type_utilisateur') -> list[dict[str, Any]]:
    """Répartition anneau (utilisateur ou activité)."""
    col = 'type_activite' if mode == 'type_activite' else 'type_utilisateur'
    if df.empty:
        return []
    vc = df[col].value_counts()
    return [{'label': str(k), 'count': int(v)} for k, v in vc.items()]


def build_heatmap(df: pd.DataFrame) -> dict[str, Any]:
    """Carte de chaleur heure × jour de la semaine."""
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    z = [[0 for _ in range(24)] for _ in range(7)]
    if not df.empty:
        tmp = df.copy()
        # pandas: Monday=0
        tmp['dow'] = tmp['horodatage'].dt.dayofweek
        tmp['hour'] = tmp['horodatage'].dt.hour
        for (dow, hour), count in tmp.groupby(['dow', 'hour']).size().items():
            z[int(dow)][int(hour)] = int(count)
    return {'jours': jours, 'heures': list(range(24)), 'z': z}


def build_top_ips_table(df: pd.DataFrame, limit: int = 25) -> list[dict[str, Any]]:
    """Tableau des IP les plus actives avec niveau de risque."""
    if df.empty:
        return []
    rows = []
    for ip, g in df.groupby('adresse_ip'):
        score = float(g['gravite'].map(lambda x: GRAVITE_SCORE.get(str(x).lower(), 1)).mean())
        attempts = int(len(g))
        # Score de risque composite
        risk_score = score + min(attempts / 200, 2.5)
        if risk_score >= 5:
            risk = 'critique'
        elif risk_score >= 3.5:
            risk = 'élevé'
        elif risk_score >= 2.2:
            risk = 'moyen'
        else:
            risk = 'faible'
        rows.append({
            'adresse_ip': ip,
            'pays': g['pays'].mode().iloc[0] if len(g['pays'].mode()) else g['pays'].iloc[0],
            'service_vise': g['service_cible'].mode().iloc[0] if len(g['service_cible'].mode()) else g['service_cible'].iloc[0],
            'compte_vise': g['compte_vise'].mode().iloc[0] if len(g['compte_vise'].mode()) else g['compte_vise'].iloc[0],
            'tentatives': attempts,
            'dernier_evenement': g['horodatage'].max().strftime('%Y-%m-%d %H:%M:%S'),
            'niveau_risque': risk,
            'risque_score': round(risk_score, 2),
        })
    rows.sort(key=lambda r: (-r['risque_score'], -r['tentatives']))
    return rows[:limit]


def filter_options(df: pd.DataFrame) -> dict[str, Any]:
    """Options disponibles pour les filtres."""
    if df.empty:
        return {
            'pays': [], 'type_activite': [], 'gravite': [],
            'type_utilisateur': [], 'service_cible': [],
            'date_min': None, 'date_max': None,
        }
    return {
        'pays': sorted(df['pays'].dropna().unique().tolist()),
        'type_activite': sorted(df['type_activite'].dropna().unique().tolist()),
        'gravite': [g for g in GRAVITE_LABELS if g in set(df['gravite'].unique())],
        'type_utilisateur': sorted(df['type_utilisateur'].dropna().unique().tolist()),
        'service_cible': sorted(df['service_cible'].dropna().unique().tolist()),
        'date_min': df['horodatage'].min().strftime('%Y-%m-%d'),
        'date_max': df['horodatage'].max().strftime('%Y-%m-%d'),
    }


def build_dashboard_payload(
    df: pd.DataFrame,
    *,
    granularity: str = 'heure',
    top_dimension: str = 'adresse_ip',
    donut_mode: str = 'type_utilisateur',
) -> dict[str, Any]:
    """Payload complet pour l'interface admin / Streamlit."""
    return {
        'kpis': build_kpis(df),
        'map': build_map_bubbles(df),
        'timeline': build_timeline(df, granularity=granularity),
        'top10': build_top10(df, dimension=top_dimension),
        'donut': build_donut(df, mode=donut_mode),
        'heatmap': build_heatmap(df),
        'top_ips': build_top_ips_table(df),
        'meta': {
            'simule': True,
            'note': 'Données simulées à des fins de démonstration portfolio — aucune donnée personnelle réelle.',
            'nb_lignes': int(len(df)),
        },
    }
