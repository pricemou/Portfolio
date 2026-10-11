"""
Tableau de bord cybersécurité (Streamlit + Plotly).
Réutilise le même moteur que l'admin Flask du portfolio.

Lancement :
  streamlit run cyber_monitoring/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyber_monitoring.data_engine import (  # noqa: E402
    apply_filters,
    build_dashboard_payload,
    filter_options,
    load_events,
)

st.set_page_config(
    page_title='Monitoring cybersécurité',
    page_icon='🛡️',
    layout='wide',
)

GRAVITE_COLOR = {
    'faible': '#4dba87',
    'moyenne': '#f0ad4e',
    'élevée': '#e67e22',
    'critique': '#dc3545',
}


@st.cache_data(show_spinner=False)
def _load_default():
    return load_events()


def main():
    st.title('Monitoring cybersécurité')
    st.caption(
        'Données simulées à des fins de démonstration portfolio — '
        'aucune donnée personnelle réelle. IP de documentation (RFC 5737).'
    )

    st.sidebar.header('Filtres')
    uploaded = st.sidebar.file_uploader('Téléverser un CSV', type=['csv'])
    if uploaded is not None:
        df_raw = load_events(uploaded.getvalue())
        st.sidebar.success(f'CSV chargé ({len(df_raw)} lignes)')
    else:
        df_raw = _load_default()

    opts = filter_options(df_raw)
    date_range = st.sidebar.date_input(
        'Période',
        value=(
            pd.to_datetime(opts['date_min']).date() if opts['date_min'] else None,
            pd.to_datetime(opts['date_max']).date() if opts['date_max'] else None,
        ),
    )
    pays = st.sidebar.multiselect('Pays', opts['pays'], default=[])
    activite = st.sidebar.multiselect("Type d'activité", opts['type_activite'], default=[])
    gravite = st.sidebar.multiselect('Gravité', opts['gravite'], default=[])
    user_type = st.sidebar.multiselect("Type d'utilisateur", opts['type_utilisateur'], default=[])
    service = st.sidebar.multiselect('Service cible', opts['service_cible'], default=[])

    start = end = None
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = str(date_range[0]), str(date_range[1])

    df = apply_filters(
        df_raw,
        date_start=start,
        date_end=end,
        pays=pays or None,
        type_activite=activite or None,
        gravite=gravite or None,
        type_utilisateur=user_type or None,
        service_cible=service or None,
    )

    gran = st.sidebar.radio('Granularité temporelle', ['heure', 'jour'], horizontal=True)
    top_dim = st.sidebar.selectbox(
        'Top 10 — dimension',
        ['adresse_ip', 'compte_vise', 'pays', 'service_cible'],
        format_func=lambda x: {
            'adresse_ip': 'Adresses IP',
            'compte_vise': 'Comptes visés',
            'pays': 'Pays',
            'service_cible': 'Services cibles',
        }[x],
    )
    donut_mode = st.sidebar.radio(
        'Anneau',
        ['type_utilisateur', 'type_activite'],
        format_func=lambda x: "Type d'utilisateur" if x == 'type_utilisateur' else "Type d'activité",
    )

    payload = build_dashboard_payload(
        df, granularity=gran, top_dimension=top_dim, donut_mode=donut_mode
    )
    k = payload['kpis']

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Événements', f"{k['total_evenements']:,}".replace(',', ' '))
    c2.metric('IP uniques', f"{k['ip_uniques']:,}".replace(',', ' '))
    c3.metric("Taux d'échec", f"{k['taux_echec']} %")
    c4.metric('Alertes critiques', f"{k['alertes_critiques']:,}".replace(',', ' '))
    c5.metric('Pays', k['nb_pays'])

    # 1. Carte
    st.subheader('Origine des connexions')
    map_df = pd.DataFrame(payload['map'])
    if map_df.empty:
        st.info('Aucune donnée pour la carte.')
    else:
        fig_map = px.scatter_geo(
            map_df,
            lat='latitude',
            lon='longitude',
            size='evenements',
            color='gravite_moyenne',
            hover_name='ville',
            hover_data={'pays': True, 'evenements': True, 'latitude': False, 'longitude': False},
            color_discrete_map=GRAVITE_COLOR,
            projection='natural earth',
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=420, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_map, use_container_width=True)

    # 2. Timeline
    st.subheader('Évolution temporelle')
    tl = payload['timeline']
    tl_df = pd.DataFrame(tl['points'])
    if tl_df.empty:
        st.info('Aucune série temporelle.')
    else:
        fig_tl = go.Figure()
        fig_tl.add_trace(go.Scatter(
            x=tl_df['horodatage'], y=tl_df['count'], mode='lines',
            name='Événements', line=dict(color='#4dba87'),
        ))
        fig_tl.add_hline(y=tl['seuil'], line_dash='dash', line_color='#f0ad4e',
                         annotation_text=f"Seuil anomalie ({tl['seuil']})")
        anom = tl_df[tl_df['anomalie']]
        if not anom.empty:
            fig_tl.add_trace(go.Scatter(
                x=anom['horodatage'], y=anom['count'], mode='markers',
                name='Dépassement', marker=dict(color='#dc3545', size=9),
            ))
        fig_tl.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_tl, use_container_width=True)

    col_a, col_b = st.columns(2)

    # 3. Top 10
    with col_a:
        st.subheader('Top 10')
        top_df = pd.DataFrame(payload['top10'])
        if top_df.empty:
            st.info('Pas de top 10.')
        else:
            fig_bar = px.bar(top_df, x='count', y='label', orientation='h',
                             color_discrete_sequence=['#4dba87'])
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, height=380,
                                  margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)

    # 4. Donut
    with col_b:
        st.subheader('Répartition')
        donut_df = pd.DataFrame(payload['donut'])
        if donut_df.empty:
            st.info('Pas de répartition.')
        else:
            fig_d = go.Figure(data=[go.Pie(
                labels=donut_df['label'], values=donut_df['count'], hole=0.55,
            )])
            fig_d.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_d, use_container_width=True)

    # 5. Heatmap
    st.subheader('Activité par heure et jour')
    hm = payload['heatmap']
    fig_hm = go.Figure(data=go.Heatmap(
        z=hm['z'], x=[str(h) for h in hm['heures']], y=hm['jours'],
        colorscale='Tealgrn',
    ))
    fig_hm.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_hm, use_container_width=True)

    # Tableau IP
    st.subheader('IP les plus actives')
    ips = pd.DataFrame(payload['top_ips'])
    if ips.empty:
        st.info('Aucune IP.')
    else:
        st.dataframe(
            ips.drop(columns=['risque_score'], errors='ignore'),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == '__main__':
    main()
