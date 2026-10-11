"""
Génère un jeu de données simulé d'événements de cybersécurité (50 000 lignes, 30 jours).
Les adresses IP appartiennent uniquement aux plages de documentation (RFC 5737).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Plages réservées à la documentation (jamais des IP personnelles)
DOC_NETS = ("203.0.113.", "198.51.100.", "192.0.2.")

# Lieux fictifs (coordonnées approximatives publiques)
LOCATIONS = [
    ("France", "Paris", 48.8566, 2.3522),
    ("France", "Lyon", 45.7640, 4.8357),
    ("Canada", "Montréal", 45.5017, -73.5673),
    ("Canada", "Toronto", 43.6532, -79.3832),
    ("États-Unis", "New York", 40.7128, -74.0060),
    ("États-Unis", "San Francisco", 37.7749, -122.4194),
    ("Allemagne", "Berlin", 52.5200, 13.4050),
    ("Royaume-Uni", "Londres", 51.5074, -0.1278),
    ("Brésil", "São Paulo", -23.5505, -46.6333),
    ("Japon", "Tokyo", 35.6762, 139.6503),
    ("Inde", "Mumbai", 19.0760, 72.8777),
    ("Australie", "Sydney", -33.8688, 151.2093),
    ("Pays-Bas", "Amsterdam", 52.3676, 4.9041),
    ("Espagne", "Madrid", 40.4168, -3.7038),
    ("Singapour", "Singapour", 1.3521, 103.8198),
]

SERVICES = ["SSH", "RDP", "HTTP", "MySQL"]
COMPTES = ["root", "admin", "administrator", "user"]
TYPES_UTILISATEUR = ["légitime", "robot", "suspect"]
ACTIVITES = [
    "connexion réussie",
    "échec de connexion",
    "scan de ports",
    "force brute",
    "injection SQL",
]
GRAVITES = ["faible", "moyenne", "élevée", "critique"]

# Gravité dominante par type d'activité
GRAVITE_PAR_ACTIVITE = {
    "connexion réussie": ("faible", "moyenne"),
    "échec de connexion": ("faible", "moyenne", "élevée"),
    "scan de ports": ("moyenne", "élevée"),
    "force brute": ("élevée", "critique"),
    "injection SQL": ("élevée", "critique"),
}

# IP récurrentes pour le pic nocturne de force brute
BRUTE_FORCE_IPS = [
    "203.0.113.17",
    "203.0.113.88",
    "198.51.100.42",
    "198.51.100.201",
    "192.0.2.55",
    "192.0.2.199",
]


def _ip_aleatoire(rng: np.random.Generator) -> str:
    """Tire une IP dans une plage de documentation."""
    prefix = DOC_NETS[int(rng.integers(0, len(DOC_NETS)))]
    return f"{prefix}{int(rng.integers(1, 255))}"


def _choisir_activite(heure: int, rng: np.random.Generator) -> str:
    """
    Favorise la force brute la nuit (00h–05h).
    Le reste de la journée suit une distribution plus équilibrée.
    """
    if 0 <= heure <= 5:
        probs = [0.08, 0.22, 0.15, 0.48, 0.07]  # pic force brute
    else:
        probs = [0.35, 0.30, 0.15, 0.12, 0.08]
    return str(rng.choice(ACTIVITES, p=probs))


def _choisir_utilisateur(activite: str, rng: np.random.Generator) -> str:
    """Associe un profil utilisateur plausible à l'activité."""
    if activite == "connexion réussie":
        return str(rng.choice(TYPES_UTILISATEUR, p=[0.75, 0.15, 0.10]))
    if activite in ("force brute", "injection SQL"):
        return str(rng.choice(TYPES_UTILISATEUR, p=[0.05, 0.35, 0.60]))
    if activite == "scan de ports":
        return str(rng.choice(TYPES_UTILISATEUR, p=[0.05, 0.55, 0.40]))
    return str(rng.choice(TYPES_UTILISATEUR, p=[0.25, 0.35, 0.40]))


def _choisir_gravite(activite: str, rng: np.random.Generator) -> str:
    options = GRAVITE_PAR_ACTIVITE[activite]
    return str(rng.choice(options))


def generer_evenements(n: int = 50_000, jours: int = 30, graine: int = 42) -> pd.DataFrame:
    """Construit le DataFrame simulé d'événements de connexion."""
    rng = np.random.default_rng(graine)
    fin = datetime.now().replace(minute=0, second=0, microsecond=0)
    debut = fin - timedelta(days=jours)

    lignes = []
    for _ in range(n):
        # Tirage temporel uniforme sur 30 jours
        offset_sec = int(rng.integers(0, jours * 24 * 3600))
        ts = debut + timedelta(seconds=offset_sec)
        heure = ts.hour

        activite = _choisir_activite(heure, rng)

        # IP récurrentes la nuit pour les attaques de force brute
        if activite == "force brute" and 0 <= heure <= 5 and rng.random() < 0.65:
            adresse_ip = str(rng.choice(BRUTE_FORCE_IPS))
        else:
            adresse_ip = _ip_aleatoire(rng)

        pays, ville, lat, lon = LOCATIONS[int(rng.integers(0, len(LOCATIONS)))]
        # Léger bruit géo pour varier les bulles
        lat = float(lat + rng.normal(0, 0.15))
        lon = float(lon + rng.normal(0, 0.15))

        lignes.append(
            {
                "horodatage": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "adresse_ip": adresse_ip,
                "pays": pays,
                "ville": ville,
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "service_cible": str(rng.choice(SERVICES)),
                "compte_vise": str(rng.choice(COMPTES)),
                "type_utilisateur": _choisir_utilisateur(activite, rng),
                "type_activite": activite,
                "gravite": _choisir_gravite(activite, rng),
            }
        )

    df = pd.DataFrame(lignes)
    df = df.sort_values("horodatage").reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère events.csv simulé")
    parser.add_argument("-n", type=int, default=50_000, help="Nombre d'événements")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "events.csv",
        help="Chemin du CSV de sortie",
    )
    args = parser.parse_args()

    df = generer_evenements(n=args.n)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, encoding="utf-8")
    print(f"Ecrit {len(df):,} evenements -> {args.output}")


if __name__ == "__main__":
    main()
