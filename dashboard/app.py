"""
Tableau de bord interactif de monitoring cybersécurité (Streamlit + Plotly).
Données simulées — aucune donnée personnelle réelle.
Lancement : streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Permet l'import de engine.py depuis le dossier dashboard
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import (  # noqa: E402
    charger_csv,
    charger_depuis_bytes,
    chemin_csv_defaut,
    filtrer,
    tableau_ip_actives,
)

THEME_PLOTLY = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#e8e8e8", "family": "Inter, Segoe UI, sans-serif"},
    "margin": dict(l=40, r=20, t=40, b=40),
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


def configurer_page() -> None:
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


@st.cache_data(show_spinner="Chargement des événements…")
def charger_csv_cache(chemin: str):
    return charger_csv(chemin)


def appliquer_filtres_sidebar(df):
    """Widgets de filtre + téléversement CSV."""
    st.sidebar.header("Filtres")
    st.sidebar.caption(
        "Données **simulées** (IP RFC 5737). Aucune donnée personnelle réelle."
    )

    upload = st.sidebar.file_uploader(
        "Téléverser un CSV (mêmes colonnes)",
        type=["csv"],
        help="Remplace le jeu par défaut pour cette session.",
    )
    if upload is not None:
        try:
            df = charger_depuis_bytes(upload.read())
            st.sidebar.success(f"Fichier chargé : {upload.name} ({len(df):,} lignes)")
        except Exception as exc:  # noqa: BLE001
            st.sidebar.error(f"CSV invalide : {exc}")

    dmin, dmax = df["horodatage"].min().date(), df["horodatage"].max().date()
    periode = st.sidebar.date_input("Période", value=(dmin, dmax), min_value=dmin, max_value=dmax)
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

    return filtrer(
        df,
        debut=debut,
        fin=fin,
        pays=pays or None,
        activites=activites or None,
        gravites=gravites or None,
        utilisateurs=utilisateurs or None,
        services=services or None,
    )


def afficher_kpis(df) -> None:
    total = len(df)
    echecs = (df["type_activite"] == "échec de connexion").sum() / total * 100 if total else 0.0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Événements", f"{total:,}".replace(",", " "))
    c2.metric("IP uniques", f"{df['adresse_ip'].nunique():,}".replace(",", " "))
    c3.metric("Taux d’échec", f"{echecs:.1f} %")
    c4.metric("Alertes critiques", f"{int((df['gravite'] == 'critique').sum()):,}".replace(",", " "))
    c5.metric("Pays", f"{df['pays'].nunique()}")


def vue_carte_bulles(df) -> go.Figure:
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
    fig.update_layout(**THEME_PLOTLY, coloraxis_colorbar=dict(title="Gravité"), height=480)
    return fig


def vue_courbe_temporelle(df, granularite: str) -> go.Figure:
    if df.empty:
        return go.Figure()
    serie = df.set_index("horodatage").resample("h" if granularite == "Heure" else "D").size()
    serie = serie.rename("evenements").reset_index()
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
                marker=dict(color="#dc3545", size=9),
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


def vue_top10(df, dimension: str) -> go.Figure:
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
    return fig


def vue_donut(df, mode: str) -> go.Figure:
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


def vue_heatmap(df) -> go.Figure:
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


def main() -> None:
    configurer_page()
    st.title("Monitoring cybersécurité")
    st.caption(
        "Tableau de bord interactif — données **entièrement simulées** (portfolio). "
        "IP de documentation RFC 5737."
    )

    csv_path = chemin_csv_defaut()
    if not csv_path.exists():
        st.error("Fichier events.csv introuvable. Exécutez : python dashboard/generate_events.py")
        st.stop()

    try:
        df_base = charger_csv_cache(str(csv_path))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Impossible de charger les données : {exc}")
        st.stop()

    df = appliquer_filtres_sidebar(df_base)
    if df.empty:
        st.warning("Aucun événement ne correspond aux filtres.")
        st.stop()

    afficher_kpis(df)
    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Carte des origines")
        st.plotly_chart(vue_carte_bulles(df), use_container_width=True)
    with col_b:
        st.subheader("Évolution temporelle")
        granularite = st.radio("Granularité", ["Heure", "Jour"], horizontal=True, key="g")
        st.plotly_chart(vue_courbe_temporelle(df, granularite), use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Top 10")
        dimension = st.selectbox(
            "Dimension",
            ["Adresses IP", "Comptes visés", "Pays", "Services cibles"],
            key="top",
        )
        st.plotly_chart(vue_top10(df, dimension), use_container_width=True)
    with col_d:
        st.subheader("Répartition")
        mode = st.radio(
            "Vue",
            ["Type d’utilisateur", "Type d’activité"],
            horizontal=True,
            key="donut",
        )
        st.plotly_chart(vue_donut(df, mode), use_container_width=True)

    st.subheader("Activité par heure et jour")
    st.plotly_chart(vue_heatmap(df), use_container_width=True)

    st.subheader("IP les plus actives")
    st.caption("Tableau triable — risque dérivé du volume et de la gravité.")
    import pandas as pd

    rows = tableau_ip_actives(df)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.info(
        "**Note :** données fictives uniquement. Plages IP documentation : "
        "192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24."
    )


if __name__ == "__main__":
    main()
