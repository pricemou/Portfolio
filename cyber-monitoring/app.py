"""
Tableau de bord interactif de monitoring cybersécurité (Streamlit + Plotly).
Données simulées — aucune donnée personnelle réelle.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
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
COULEUR_GRAVITE = {
    "faible": "#6c757d",
    "moyenne": "#f0ad4e",
    "élevée": "#fd7e14",
    "critique": "#dc3545",
}

JOURS_FR = {
    0: "Lundi",
    1: "Mardi",
    2: "Mercredi",
    3: "Jeudi",
    4: "Vendredi",
    5: "Samedi",
    6: "Dimanche",
}

THEME_PLOTLY = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#e8e8e8", "family": "Inter, Segoe UI, sans-serif"},
    "margin": dict(l=40, r=20, t=40, b=40),
}

CSV_DEFAUT = Path(__file__).resolve().parent / "events.csv"


# ---------------------------------------------------------------------------
# Chargement et préparation des données
# ---------------------------------------------------------------------------
def valider_colonnes(df: pd.DataFrame) -> None:
    """Vérifie que le CSV contient toutes les colonnes attendues."""
    manquantes = [c for c in COLONNES_REQUISES if c not in df.columns]
    if manquantes:
        raise ValueError(f"Colonnes manquantes : {', '.join(manquantes)}")


def preparer_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les types et ajoute des colonnes dérivées utiles aux graphiques."""
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


@st.cache_data(show_spinner="Chargement des événements…")
def charger_csv_defaut(chemin: str) -> pd.DataFrame:
    """Charge le CSV par défaut (mis en cache)."""
    df = pd.read_csv(chemin)
    valider_colonnes(df)
    return preparer_dataframe(df)


def charger_depuis_upload(fichier) -> pd.DataFrame:
    """Charge un CSV téléversé depuis la barre latérale."""
    contenu = fichier.read()
    df = pd.read_csv(BytesIO(contenu))
    valider_colonnes(df)
    return preparer_dataframe(df)


# ---------------------------------------------------------------------------
# Filtres (barre latérale)
# ---------------------------------------------------------------------------
def appliquer_filtres(df: pd.DataFrame) -> pd.DataFrame:
    """Affiche les widgets de filtre et retourne le sous-ensemble filtré."""
    st.sidebar.header("Filtres")
    st.sidebar.caption(
        "Les données affichées sont **simulées** (IP de documentation RFC 5737). "
        "Aucune donnée personnelle réelle n’est utilisée."
    )

    upload = st.sidebar.file_uploader(
        "Téléverser un CSV (mêmes colonnes)",
        type=["csv"],
        help="Remplace le jeu de données par défaut pour cette session.",
    )
    if upload is not None:
        try:
            df = charger_depuis_upload(upload)
            st.sidebar.success(f"Fichier chargé : {upload.name} ({len(df):,} lignes)")
        except Exception as exc:  # noqa: BLE001
            st.sidebar.error(f"CSV invalide : {exc}")

    dmin, dmax = df["horodatage"].min().date(), df["horodatage"].max().date()
    periode = st.sidebar.date_input(
        "Période",
        value=(dmin, dmax),
        min_value=dmin,
        max_value=dmax,
    )
    if isinstance(periode, (list, tuple)) and len(periode) == 2:
        debut, fin = periode
    else:
        debut = fin = periode if not isinstance(periode, (list, tuple)) else periode[0]

    pays = st.sidebar.multiselect("Pays", sorted(df["pays"].dropna().unique()), default=[])
    activites = st.sidebar.multiselect(
        "Type d’activité", sorted(df["type_activite"].dropna().unique()), default=[]
    )
    gravites = st.sidebar.multiselect(
        "Gravité", ["faible", "moyenne", "élevée", "critique"], default=[]
    )
    utilisateurs = st.sidebar.multiselect(
        "Type d’utilisateur", sorted(df["type_utilisateur"].dropna().unique()), default=[]
    )
    services = st.sidebar.multiselect(
        "Service cible", sorted(df["service_cible"].dropna().unique()), default=[]
    )

    masque = (df["horodatage"].dt.date >= debut) & (df["horodatage"].dt.date <= fin)
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


# ---------------------------------------------------------------------------
# Indicateurs clés
# ---------------------------------------------------------------------------
def afficher_kpis(df: pd.DataFrame) -> None:
    """Rangée de chiffres clés en haut du tableau de bord."""
    total = len(df)
    ip_uniques = df["adresse_ip"].nunique() if total else 0
    echecs = (
        (df["type_activite"] == "échec de connexion").sum() / total * 100 if total else 0.0
    )
    critiques = int((df["gravite"] == "critique").sum()) if total else 0
    pays = df["pays"].nunique() if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Événements", f"{total:,}".replace(",", " "))
    c2.metric("IP uniques", f"{ip_uniques:,}".replace(",", " "))
    c3.metric("Taux d’échec", f"{echecs:.1f} %")
    c4.metric("Alertes critiques", f"{critiques:,}".replace(",", " "))
    c5.metric("Pays", f"{pays}")


# ---------------------------------------------------------------------------
# Vue 1 — Carte du monde à bulles
# ---------------------------------------------------------------------------
def vue_carte_bulles(df: pd.DataFrame) -> go.Figure:
    """Origine des connexions : taille = volume, couleur = gravité moyenne."""
    if df.empty:
        return go.Figure()

    agg = (
        df.groupby(["pays", "ville", "latitude", "longitude"], as_index=False)
        .agg(evenements=("adresse_ip", "count"), gravite_moy=("score_gravite", "mean"))
    )
    fig = px.scatter_geo(
        agg,
        lat="latitude",
        lon="longitude",
        size="evenements",
        color="gravite_moy",
        color_continuous_scale=["#6c757d", "#f0ad4e", "#fd7e14", "#dc3545"],
        range_color=(1, 4),
        hover_name="ville",
        hover_data={
            "pays": True,
            "ville": True,
            "evenements": True,
            "latitude": False,
            "longitude": False,
            "gravite_moy": ":.2f",
        },
        size_max=48,
        labels={"evenements": "Événements", "gravite_moy": "Gravité moy.", "pays": "Pays"},
    )
    fig.update_geos(
        projection_type="natural earth",
        showcountries=True,
        showcoastlines=True,
        bgcolor="rgba(0,0,0,0)",
        landcolor="#2a2d34",
        oceancolor="#1a1c22",
        countrycolor="#555",
    )
    fig.update_layout(
        **THEME_PLOTLY,
        coloraxis_colorbar=dict(title="Gravité"),
        height=480,
    )
    return fig


# ---------------------------------------------------------------------------
# Vue 2 — Courbe temporelle + seuil d’anomalie
# ---------------------------------------------------------------------------
def vue_courbe_temporelle(df: pd.DataFrame, granularite: str) -> go.Figure:
    """Événements par heure ou par jour, avec seuil et dépassements en rouge."""
    if df.empty:
        return go.Figure()

    serie = df.set_index("horodatage").resample("h" if granularite == "Heure" else "D").size()
    serie = serie.rename("evenements").reset_index()
    # Seuil = moyenne + 2 écarts-types
    mu, sigma = serie["evenements"].mean(), serie["evenements"].std(ddof=0)
    seuil = float(mu + 2 * sigma) if sigma > 0 else float(mu) + 1
    serie["anomalie"] = serie["evenements"] > seuil

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=serie["horodatage"],
            y=serie["evenements"],
            mode="lines",
            name="Événements",
            line=dict(color="#4dba87", width=2),
        )
    )
    fig.add_hline(
        y=seuil,
        line_dash="dash",
        line_color="#f0ad4e",
        annotation_text=f"Seuil anomalie ({seuil:.0f})",
        annotation_position="top left",
    )
    anomalies = serie[serie["anomalie"]]
    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies["horodatage"],
                y=anomalies["evenements"],
                mode="markers",
                name="Dépassement",
                marker=dict(color="#dc3545", size=9, symbol="circle"),
            )
        )
    fig.update_layout(
        **THEME_PLOTLY,
        xaxis_title="Temps",
        yaxis_title="Nombre d’événements",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
    return fig


# ---------------------------------------------------------------------------
# Vue 3 — Top 10 barres horizontales
# ---------------------------------------------------------------------------
def vue_top10(df: pd.DataFrame, dimension: str) -> go.Figure:
    """Top 10 selon la dimension choisie (IP, compte, pays, service)."""
    mapping = {
        "Adresses IP": "adresse_ip",
        "Comptes visés": "compte_vise",
        "Pays": "pays",
        "Services cibles": "service_cible",
    }
    col = mapping[dimension]
    if df.empty:
        return go.Figure()

    top = df[col].value_counts().head(10).sort_values(ascending=True)
    fig = go.Figure(
        go.Bar(
            x=top.values,
            y=top.index.astype(str),
            orientation="h",
            marker_color="#4dba87",
            text=top.values,
            textposition="outside",
        )
    )
    fig.update_layout(
        **THEME_PLOTLY,
        xaxis_title="Événements",
        yaxis_title=dimension,
        height=420,
        margin=dict(l=120, r=40, t=40, b=40),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
    return fig


# ---------------------------------------------------------------------------
# Vue 4 — Anneau (donut)
# ---------------------------------------------------------------------------
def vue_donut(df: pd.DataFrame, mode: str) -> go.Figure:
    """Répartition par type d’utilisateur ou par type d’activité."""
    col = "type_utilisateur" if mode == "Type d’utilisateur" else "type_activite"
    if df.empty:
        return go.Figure()

    counts = df[col].value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.55,
            marker=dict(colors=px.colors.qualitative.Set2),
            textinfo="percent+label",
        )
    )
    fig.update_layout(**THEME_PLOTLY, height=420, showlegend=True)
    return fig


# ---------------------------------------------------------------------------
# Vue 5 — Carte de chaleur heure × jour
# ---------------------------------------------------------------------------
def vue_heatmap(df: pd.DataFrame) -> go.Figure:
    """Matrice heure (0–23) × jour de la semaine."""
    if df.empty:
        return go.Figure()

    pivot = (
        df.groupby(["jour_semaine", "heure"])
        .size()
        .reset_index(name="n")
        .pivot(index="jour_semaine", columns="heure", values="n")
        .reindex(index=range(7), columns=range(24))
        .fillna(0)
    )
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[str(h) for h in range(24)],
            y=[JOURS_FR[i] for i in range(7)],
            colorscale="YlOrRd",
            colorbar=dict(title="Événements"),
            hovertemplate="Jour : %{y}<br>Heure : %{x}h<br>Événements : %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        **THEME_PLOTLY,
        xaxis_title="Heure de la journée",
        yaxis_title="Jour de la semaine",
        height=420,
    )
    return fig


# ---------------------------------------------------------------------------
# Tableau des IP les plus actives
# ---------------------------------------------------------------------------
def niveau_risque(score_moy: float, n: int, critiques: int) -> str:
    """Calcule un niveau de risque simple à partir du volume et de la gravité."""
    points = score_moy * 10 + min(n / 50, 10) + critiques * 2
    if points >= 40:
        return "Critique"
    if points >= 28:
        return "Élevé"
    if points >= 16:
        return "Moyen"
    return "Faible"


def tableau_ip_actives(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """Agrège les IP les plus actives avec indicateurs de risque."""
    if df.empty:
        return pd.DataFrame()

    rows = []
    for ip, g in df.groupby("adresse_ip"):
        rows.append(
            {
                "IP": ip,
                "Pays": g["pays"].mode().iloc[0] if not g["pays"].mode().empty else "—",
                "Service visé": g["service_cible"].mode().iloc[0]
                if not g["service_cible"].mode().empty
                else "—",
                "Compte visé": g["compte_vise"].mode().iloc[0]
                if not g["compte_vise"].mode().empty
                else "—",
                "Tentatives": len(g),
                "Dernier événement": g["horodatage"].max(),
                "Niveau de risque": niveau_risque(
                    float(g["score_gravite"].mean()),
                    len(g),
                    int((g["gravite"] == "critique").sum()),
                ),
            }
        )
    table = pd.DataFrame(rows).sort_values("Tentatives", ascending=False).head(top_n)
    table["Dernier événement"] = table["Dernier événement"].dt.strftime("%Y-%m-%d %H:%M")
    return table.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Application principale
# ---------------------------------------------------------------------------
def configurer_page() -> None:
    """Configuration globale Streamlit."""
    st.set_page_config(
        page_title="Monitoring cybersécurité",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
        div[data-testid="stMetric"] {
            background: #2d2e32;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            padding: 0.75rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    configurer_page()

    st.title("Monitoring cybersécurité")
    st.caption(
        "Tableau de bord interactif — données **entièrement simulées** à des fins de démonstration portfolio. "
        "Adresses IP issues des plages de documentation (RFC 5737)."
    )

    if not CSV_DEFAUT.exists():
        st.error(
            f"Fichier introuvable : `{CSV_DEFAUT.name}`. "
            "Exécutez d’abord `python generate_events.py`."
        )
        st.stop()

    try:
        df_base = charger_csv_defaut(str(CSV_DEFAUT))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Impossible de charger les données : {exc}")
        st.stop()

    df = appliquer_filtres(df_base)

    if df.empty:
        st.warning("Aucun événement ne correspond aux filtres sélectionnés.")
        st.stop()

    afficher_kpis(df)
    st.divider()

    # --- Vues 1 & 2 ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Carte des origines")
        st.plotly_chart(vue_carte_bulles(df), use_container_width=True)
    with col_b:
        st.subheader("Évolution temporelle")
        granularite = st.radio(
            "Granularité",
            ["Heure", "Jour"],
            horizontal=True,
            key="granularite_temps",
        )
        st.plotly_chart(vue_courbe_temporelle(df, granularite), use_container_width=True)

    # --- Vues 3 & 4 ---
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Top 10")
        dimension = st.selectbox(
            "Dimension",
            ["Adresses IP", "Comptes visés", "Pays", "Services cibles"],
            key="top10_dim",
        )
        st.plotly_chart(vue_top10(df, dimension), use_container_width=True)
    with col_d:
        st.subheader("Répartition")
        mode_donut = st.radio(
            "Vue",
            ["Type d’utilisateur", "Type d’activité"],
            horizontal=True,
            key="donut_mode",
        )
        st.plotly_chart(vue_donut(df, mode_donut), use_container_width=True)

    # --- Vue 5 ---
    st.subheader("Activité par heure et jour")
    st.plotly_chart(vue_heatmap(df), use_container_width=True)

    # --- Tableau IP ---
    st.subheader("IP les plus actives")
    st.caption("Tableau triable — risque dérivé du volume et de la gravité moyenne.")
    st.dataframe(
        tableau_ip_actives(df),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.info(
        "**Note :** ce tableau de bord utilise exclusivement des données fictives. "
        "Les adresses IP appartiennent aux plages réservées à la documentation "
        "(192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24)."
    )


if __name__ == "__main__":
    main()
