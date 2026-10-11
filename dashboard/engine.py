"""
Moteur de données partagé : chargement CSV, filtres et agrégats
pour Streamlit et pour la page /dashboard du portfolio Flask.
Données simulées uniquement (RFC 5737).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

COLONNES_REQUISES = [
    "horodatage",
    "adresse_ip",
    "pays",
    "ville",
    "latitude",
    "longitude",
    "service_cible",
    "compte_vise",
    "type_utilisateur",
    "type_activite",
    "gravite",
]

SCORE_GRAVITE = {"faible": 1, "moyenne": 2, "élevée": 3, "critique": 4}

JOURS_FR = {
    0: "Lundi",
    1: "Mardi",
    2: "Mercredi",
    3: "Jeudi",
    4: "Vendredi",
    5: "Samedi",
    6: "Dimanche",
}

DIR = Path(__file__).resolve().parent
CSV_CANDIDATS = [
    DIR / "events.csv",
    DIR.parent / "cyber-monitoring" / "events.csv",
]


def chemin_csv_defaut() -> Path:
    """Retourne le premier events.csv disponible."""
    for chemin in CSV_CANDIDATS:
        if chemin.is_file():
            return chemin
    return CSV_CANDIDATS[0]


def valider_colonnes(df: pd.DataFrame) -> None:
    manquantes = [c for c in COLONNES_REQUISES if c not in df.columns]
    if manquantes:
        raise ValueError(f"Colonnes manquantes : {', '.join(manquantes)}")


def preparer_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les types et ajoute les colonnes dérivées."""
    out = df.copy()
    out["horodatage"] = pd.to_datetime(out["horodatage"], errors="coerce")
    out = out.dropna(subset=["horodatage"])
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    out["score_gravite"] = out["gravite"].map(SCORE_GRAVITE).fillna(1)
    out["date"] = out["horodatage"].dt.date
    out["heure"] = out["horodatage"].dt.hour
    out["jour_semaine"] = out["horodatage"].dt.dayofweek
    out["jour_nom"] = out["jour_semaine"].map(JOURS_FR)
    return out


def charger_csv(chemin: str | Path | None = None) -> pd.DataFrame:
    path = Path(chemin) if chemin else chemin_csv_defaut()
    if not path.is_file():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}. Exécutez python dashboard/generate_events.py"
        )
    df = pd.read_csv(path)
    valider_colonnes(df)
    return preparer_dataframe(df)


def charger_depuis_bytes(contenu: bytes) -> pd.DataFrame:
    df = pd.read_csv(BytesIO(contenu))
    valider_colonnes(df)
    return preparer_dataframe(df)


def filtrer(
    df: pd.DataFrame,
    *,
    debut=None,
    fin=None,
    pays: list[str] | None = None,
    activites: list[str] | None = None,
    gravites: list[str] | None = None,
    utilisateurs: list[str] | None = None,
    services: list[str] | None = None,
) -> pd.DataFrame:
    """Applique les filtres sidebar / query string."""
    if df.empty:
        return df.copy()

    masque = pd.Series(True, index=df.index)
    if debut is not None:
        debut_ts = pd.to_datetime(debut).date()
        masque &= df["horodatage"].dt.date >= debut_ts
    if fin is not None:
        fin_ts = pd.to_datetime(fin).date()
        masque &= df["horodatage"].dt.date <= fin_ts
    if pays:
        masque &= df["pays"].isin(pays)
    if activites:
        masque &= df["type_activite"].isin(activites)
    if gravites:
        masque &= df["gravite"].isin(gravites)
    if utilisateurs:
        masque &= df["type_utilisateur"].isin(utilisateurs)
    if services:
        masque &= df["service_cible"].isin(services)
    return df.loc[masque].copy()


def calculer_kpis(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    echecs = (
        float((df["type_activite"] == "échec de connexion").sum() / total * 100)
        if total
        else 0.0
    )
    return {
        "total_evenements": total,
        "ip_uniques": int(df["adresse_ip"].nunique()) if total else 0,
        "taux_echec": round(echecs, 1),
        "alertes_critiques": int((df["gravite"] == "critique").sum()) if total else 0,
        "nb_pays": int(df["pays"].nunique()) if total else 0,
    }


def agg_carte(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    agg = (
        df.groupby(["pays", "ville", "latitude", "longitude"], as_index=False)
        .agg(evenements=("adresse_ip", "count"), gravite_moy=("score_gravite", "mean"))
    )
    return agg.to_dict(orient="records")


def agg_temporel(df: pd.DataFrame, granularite: str = "heure") -> dict[str, Any]:
    if df.empty:
        return {"points": [], "seuil": 0}
    rule = "h" if granularite.lower().startswith("h") else "D"
    serie = df.set_index("horodatage").resample(rule).size().rename("evenements").reset_index()
    mu = float(serie["evenements"].mean())
    sigma = float(serie["evenements"].std(ddof=0))
    seuil = mu + 2 * sigma if sigma > 0 else mu + 1
    points = [
        {
            "horodatage": row["horodatage"].isoformat(),
            "evenements": int(row["evenements"]),
            "anomalie": bool(row["evenements"] > seuil),
        }
        for _, row in serie.iterrows()
    ]
    return {"points": points, "seuil": float(seuil)}


def agg_top10(df: pd.DataFrame, dimension: str) -> list[dict[str, Any]]:
    mapping = {
        "ip": "adresse_ip",
        "adresse_ip": "adresse_ip",
        "compte": "compte_vise",
        "compte_vise": "compte_vise",
        "pays": "pays",
        "service": "service_cible",
        "service_cible": "service_cible",
    }
    col = mapping.get(dimension, "adresse_ip")
    if df.empty:
        return []
    top = df[col].value_counts().head(10)
    return [{"label": str(k), "valeur": int(v)} for k, v in top.items()]


def agg_repartition(df: pd.DataFrame, mode: str) -> list[dict[str, Any]]:
    col = "type_utilisateur" if mode.startswith("utilisateur") else "type_activite"
    if df.empty:
        return []
    counts = df[col].value_counts()
    return [{"label": str(k), "valeur": int(v)} for k, v in counts.items()]


def agg_heatmap(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"z": [[0] * 24 for _ in range(7)], "x": list(range(24)), "y": [JOURS_FR[i] for i in range(7)]}
    pivot = (
        df.groupby(["jour_semaine", "heure"])
        .size()
        .reset_index(name="n")
        .pivot(index="jour_semaine", columns="heure", values="n")
        .reindex(index=range(7), columns=range(24))
        .fillna(0)
    )
    return {
        "z": pivot.values.astype(int).tolist(),
        "x": list(range(24)),
        "y": [JOURS_FR[i] for i in range(7)],
    }


def niveau_risque(score_moy: float, n: int, critiques: int) -> str:
    points = score_moy * 10 + min(n / 50, 10) + critiques * 2
    if points >= 40:
        return "Critique"
    if points >= 28:
        return "Élevé"
    if points >= 16:
        return "Moyen"
    return "Faible"


def tableau_ip_actives(df: pd.DataFrame, top_n: int = 25) -> list[dict[str, Any]]:
    if df.empty:
        return []
    rows = []
    for ip, g in df.groupby("adresse_ip"):
        rows.append(
            {
                "ip": ip,
                "pays": g["pays"].mode().iloc[0] if not g["pays"].mode().empty else "—",
                "service_vise": g["service_cible"].mode().iloc[0]
                if not g["service_cible"].mode().empty
                else "—",
                "compte_vise": g["compte_vise"].mode().iloc[0]
                if not g["compte_vise"].mode().empty
                else "—",
                "tentatives": int(len(g)),
                "dernier_evenement": g["horodatage"].max().strftime("%Y-%m-%d %H:%M"),
                "niveau_risque": niveau_risque(
                    float(g["score_gravite"].mean()),
                    len(g),
                    int((g["gravite"] == "critique").sum()),
                ),
            }
        )
    rows.sort(key=lambda r: r["tentatives"], reverse=True)
    return rows[:top_n]


def options_filtres(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "pays": [],
            "type_activite": [],
            "gravite": ["faible", "moyenne", "élevée", "critique"],
            "type_utilisateur": [],
            "service_cible": [],
            "date_min": None,
            "date_max": None,
        }
    return {
        "pays": sorted(df["pays"].dropna().unique().tolist()),
        "type_activite": sorted(df["type_activite"].dropna().unique().tolist()),
        "gravite": ["faible", "moyenne", "élevée", "critique"],
        "type_utilisateur": sorted(df["type_utilisateur"].dropna().unique().tolist()),
        "service_cible": sorted(df["service_cible"].dropna().unique().tolist()),
        "date_min": df["horodatage"].min().date().isoformat(),
        "date_max": df["horodatage"].max().date().isoformat(),
    }


def construire_payload(
    df: pd.DataFrame,
    *,
    granularite: str = "heure",
    top_dimension: str = "ip",
    donut_mode: str = "utilisateur",
) -> dict[str, Any]:
    """Payload JSON complet pour la page portfolio."""
    return {
        "kpis": calculer_kpis(df),
        "carte": agg_carte(df),
        "temporel": agg_temporel(df, granularite),
        "top10": agg_top10(df, top_dimension),
        "repartition": agg_repartition(df, donut_mode),
        "heatmap": agg_heatmap(df),
        "ip_actives": tableau_ip_actives(df),
        "nb_lignes": len(df),
        "note": (
            "Données entièrement simulées — IP de documentation RFC 5737 "
            "(192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24). "
            "Aucune donnée personnelle réelle."
        ),
    }
