/**
 * Tableau de bord cybersécurité — charge les agrégats Flask et dessine Plotly.
 */
(function () {
    const PLOT_LAYOUT = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e8e8e8', family: 'Roboto Mono, Segoe UI, sans-serif' },
        margin: { l: 48, r: 24, t: 32, b: 48 },
    };

    const PLOT_CONFIG = { responsive: true, displayModeBar: false };

    let ipRows = [];
    let sortKey = 'tentatives';
    let sortAsc = false;

    function selectedValues(selectEl) {
        return Array.from(selectEl.selectedOptions).map((o) => o.value);
    }

    function fillSelect(selectEl, values, selectedAll) {
        selectEl.innerHTML = '';
        values.forEach((v) => {
            const opt = document.createElement('option');
            opt.value = v;
            opt.textContent = v;
            if (selectedAll) opt.selected = true;
            selectEl.appendChild(opt);
        });
    }

    function fmt(n) {
        return Number(n || 0).toLocaleString('fr-FR');
    }

    function buildQuery() {
        const params = new URLSearchParams();
        const debut = document.getElementById('f-debut').value;
        const fin = document.getElementById('f-fin').value;
        if (debut) params.set('debut', debut);
        if (fin) params.set('fin', fin);

        selectedValues(document.getElementById('f-pays')).forEach((v) => params.append('pays', v));
        selectedValues(document.getElementById('f-activite')).forEach((v) => params.append('activite', v));
        selectedValues(document.getElementById('f-gravite')).forEach((v) => params.append('gravite', v));
        selectedValues(document.getElementById('f-utilisateur')).forEach((v) => params.append('utilisateur', v));
        selectedValues(document.getElementById('f-service')).forEach((v) => params.append('service', v));

        const gran = document.querySelector('input[name="granularite"]:checked');
        params.set('granularite', gran ? gran.value : 'heure');
        params.set('top', document.getElementById('top-dim').value);
        const donut = document.querySelector('input[name="donut"]:checked');
        params.set('donut', donut ? donut.value : 'utilisateur');
        return params;
    }

    function renderKpis(kpis) {
        document.getElementById('kpi-total').textContent = fmt(kpis.total_evenements);
        document.getElementById('kpi-ips').textContent = fmt(kpis.ip_uniques);
        document.getElementById('kpi-echec').textContent = `${kpis.taux_echec} %`;
        document.getElementById('kpi-crit').textContent = fmt(kpis.alertes_critiques);
        document.getElementById('kpi-pays').textContent = fmt(kpis.nb_pays);
    }

    function renderCarte(rows) {
        const fig = {
            data: [{
                type: 'scattergeo',
                lat: rows.map((r) => r.latitude),
                lon: rows.map((r) => r.longitude),
                text: rows.map((r) => `${r.ville}, ${r.pays}<br>Événements : ${r.evenements}<br>Gravité moy. : ${Number(r.gravite_moy).toFixed(2)}`),
                hoverinfo: 'text',
                marker: {
                    size: rows.map((r) => Math.max(6, Math.min(48, Math.sqrt(r.evenements) * 1.8))),
                    color: rows.map((r) => r.gravite_moy),
                    colorscale: [[0, '#6c757d'], [0.33, '#f0ad4e'], [0.66, '#fd7e14'], [1, '#dc3545']],
                    cmin: 1,
                    cmax: 4,
                    colorbar: { title: 'Gravité', thickness: 12 },
                    line: { width: 0 },
                },
            }],
            layout: {
                ...PLOT_LAYOUT,
                geo: {
                    projection: { type: 'natural earth' },
                    showland: true,
                    landcolor: '#2a2d34',
                    oceancolor: '#1a1c22',
                    showcountries: true,
                    countrycolor: '#555',
                    bgcolor: 'rgba(0,0,0,0)',
                },
                height: 400,
                margin: { l: 0, r: 0, t: 10, b: 0 },
            },
        };
        Plotly.newPlot('chart-carte', fig.data, fig.layout, PLOT_CONFIG);
    }

    function renderTemporel(temporel) {
        const pts = temporel.points || [];
        const x = pts.map((p) => p.horodatage);
        const y = pts.map((p) => p.evenements);
        const anomX = pts.filter((p) => p.anomalie).map((p) => p.horodatage);
        const anomY = pts.filter((p) => p.anomalie).map((p) => p.evenements);

        const data = [
            {
                type: 'scatter',
                mode: 'lines',
                name: 'Événements',
                x,
                y,
                line: { color: '#4dba87', width: 2 },
            },
            {
                type: 'scatter',
                mode: 'markers',
                name: 'Dépassement',
                x: anomX,
                y: anomY,
                marker: { color: '#dc3545', size: 9 },
            },
        ];
        const layout = {
            ...PLOT_LAYOUT,
            height: 400,
            shapes: [{
                type: 'line',
                xref: 'paper',
                x0: 0,
                x1: 1,
                y0: temporel.seuil,
                y1: temporel.seuil,
                line: { color: '#f0ad4e', width: 2, dash: 'dash' },
            }],
            annotations: [{
                xref: 'paper',
                x: 0,
                y: temporel.seuil,
                text: `Seuil anomalie (${Math.round(temporel.seuil)})`,
                showarrow: false,
                xanchor: 'left',
                yanchor: 'bottom',
                font: { color: '#f0ad4e', size: 11 },
            }],
            xaxis: { gridcolor: 'rgba(255,255,255,0.06)', title: 'Temps' },
            yaxis: { gridcolor: 'rgba(255,255,255,0.06)', title: 'Événements' },
            legend: { orientation: 'h', y: 1.12 },
        };
        Plotly.newPlot('chart-temporel', data, layout, PLOT_CONFIG);
    }

    function renderTop10(rows) {
        const labels = rows.map((r) => r.label).reverse();
        const values = rows.map((r) => r.valeur).reverse();
        Plotly.newPlot(
            'chart-top10',
            [{
                type: 'bar',
                orientation: 'h',
                x: values,
                y: labels,
                marker: { color: '#4dba87' },
                text: values,
                textposition: 'outside',
            }],
            {
                ...PLOT_LAYOUT,
                height: 400,
                margin: { l: 120, r: 40, t: 20, b: 40 },
                xaxis: { title: 'Événements', gridcolor: 'rgba(255,255,255,0.06)' },
            },
            PLOT_CONFIG
        );
    }

    function renderDonut(rows) {
        Plotly.newPlot(
            'chart-donut',
            [{
                type: 'pie',
                labels: rows.map((r) => r.label),
                values: rows.map((r) => r.valeur),
                hole: 0.55,
                textinfo: 'percent+label',
            }],
            { ...PLOT_LAYOUT, height: 400, showlegend: true },
            PLOT_CONFIG
        );
    }

    function renderHeatmap(hm) {
        Plotly.newPlot(
            'chart-heatmap',
            [{
                type: 'heatmap',
                z: hm.z,
                x: hm.x.map(String),
                y: hm.y,
                colorscale: 'YlOrRd',
                colorbar: { title: 'Événements' },
                hovertemplate: 'Jour : %{y}<br>Heure : %{x}h<br>Événements : %{z}<extra></extra>',
            }],
            {
                ...PLOT_LAYOUT,
                height: 420,
                xaxis: { title: 'Heure de la journée' },
                yaxis: { title: 'Jour de la semaine' },
            },
            PLOT_CONFIG
        );
    }

    function renderTable(rows) {
        ipRows = rows.slice();
        sortAndPaintTable();
    }

    function sortAndPaintTable() {
        const sorted = ipRows.slice().sort((a, b) => {
            const av = a[sortKey];
            const bv = b[sortKey];
            if (typeof av === 'number' && typeof bv === 'number') {
                return sortAsc ? av - bv : bv - av;
            }
            return sortAsc
                ? String(av).localeCompare(String(bv), 'fr')
                : String(bv).localeCompare(String(av), 'fr');
        });
        const tbody = document.querySelector('#cyber-ip-table tbody');
        tbody.innerHTML = sorted.map((r) => `
            <tr>
                <td>${escapeHtml(r.ip)}</td>
                <td>${escapeHtml(r.pays)}</td>
                <td>${escapeHtml(r.service_vise)}</td>
                <td>${escapeHtml(r.compte_vise)}</td>
                <td>${fmt(r.tentatives)}</td>
                <td>${escapeHtml(r.dernier_evenement)}</td>
                <td class="risk-${escapeHtml(r.niveau_risque)}">${escapeHtml(r.niveau_risque)}</td>
            </tr>
        `).join('');
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text == null ? '' : String(text);
        return d.innerHTML;
    }

    async function loadMeta() {
        const res = await fetch('/api/dashboard/meta');
        if (!res.ok) throw new Error('Métadonnées indisponibles');
        const meta = await res.json();
        document.getElementById('f-debut').value = meta.date_min || '';
        document.getElementById('f-fin').value = meta.date_max || '';
        document.getElementById('f-debut').min = meta.date_min || '';
        document.getElementById('f-debut').max = meta.date_max || '';
        document.getElementById('f-fin').min = meta.date_min || '';
        document.getElementById('f-fin').max = meta.date_max || '';
        fillSelect(document.getElementById('f-pays'), meta.pays || [], false);
        fillSelect(document.getElementById('f-activite'), meta.type_activite || [], false);
        fillSelect(document.getElementById('f-gravite'), meta.gravite || [], false);
        fillSelect(document.getElementById('f-utilisateur'), meta.type_utilisateur || [], false);
        fillSelect(document.getElementById('f-service'), meta.service_cible || [], false);
    }

    async function loadData() {
        const res = await fetch(`/api/dashboard/data?${buildQuery().toString()}`);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || 'Erreur de chargement');
        }
        const data = await res.json();
        renderKpis(data.kpis || {});
        renderCarte(data.carte || []);
        renderTemporel(data.temporel || { points: [], seuil: 0 });
        renderTop10(data.top10 || []);
        renderDonut(data.repartition || []);
        renderHeatmap(data.heatmap || { z: [], x: [], y: [] });
        renderTable(data.ip_actives || []);
    }

    async function refreshAll() {
        try {
            await loadData();
        } catch (e) {
            console.error(e);
            alert(e.message || 'Erreur dashboard');
        }
    }

    function bindEvents() {
        document.getElementById('cyber-apply').addEventListener('click', refreshAll);
        document.querySelectorAll('input[name="granularite"]').forEach((el) => {
            el.addEventListener('change', refreshAll);
        });
        document.querySelectorAll('input[name="donut"]').forEach((el) => {
            el.addEventListener('change', refreshAll);
        });
        document.getElementById('top-dim').addEventListener('change', refreshAll);

        document.querySelectorAll('#cyber-ip-table th[data-sort]').forEach((th) => {
            th.addEventListener('click', () => {
                const key = th.getAttribute('data-sort');
                if (sortKey === key) sortAsc = !sortAsc;
                else {
                    sortKey = key;
                    sortAsc = key !== 'tentatives';
                }
                sortAndPaintTable();
            });
        });

        document.getElementById('cyber-upload').addEventListener('change', async (ev) => {
            const file = ev.target.files && ev.target.files[0];
            if (!file) return;
            const fd = new FormData();
            fd.append('file', file);
            const status = document.getElementById('cyber-upload-status');
            status.hidden = false;
            status.textContent = 'Téléversement…';
            const res = await fetch('/api/dashboard/upload', { method: 'POST', body: fd });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                status.textContent = data.error || 'Échec upload';
                return;
            }
            status.textContent = `Chargé : ${data.nom} (${fmt(data.lignes)} lignes)`;
            await loadMeta();
            await refreshAll();
        });

        document.getElementById('cyber-reset-csv').addEventListener('click', async () => {
            await fetch('/api/dashboard/reset', { method: 'POST' });
            document.getElementById('cyber-upload').value = '';
            const status = document.getElementById('cyber-upload-status');
            status.hidden = false;
            status.textContent = 'Données par défaut rétablies';
            await loadMeta();
            await refreshAll();
        });
    }

    document.addEventListener('DOMContentLoaded', async () => {
        if (!document.getElementById('cyber-dashboard')) return;
        if (typeof Plotly === 'undefined') {
            alert('Plotly n’a pas pu être chargé (CSP / réseau).');
            return;
        }
        bindEvents();
        try {
            await loadMeta();
            await refreshAll();
        } catch (e) {
            console.error(e);
            alert(e.message || 'Impossible d’initialiser le tableau de bord. Générez events.csv si besoin.');
        }
    });
})();
