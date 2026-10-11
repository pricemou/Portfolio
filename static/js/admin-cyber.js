/**
 * Tableau de bord monitoring cybersécurité (Plotly) — section admin.
 */
(function () {
    'use strict';

    const STATE = {
        granularity: 'heure',
        topDimension: 'adresse_ip',
        donutMode: 'type_utilisateur',
        topIps: [],
        sortKey: 'tentatives',
        sortDir: 'desc',
        loaded: false,
    };

    const GRAVITE_COLOR = {
        faible: '#4dba87',
        moyenne: '#f0ad4e',
        élevée: '#e67e22',
        critique: '#dc3545',
    };

    const PLOT_LAYOUT = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#cfcfcf', family: 'Roboto Mono, monospace', size: 11 },
        margin: { l: 48, r: 24, t: 24, b: 48 },
        legend: { orientation: 'h', y: 1.12 },
    };

    function $(id) {
        return document.getElementById(id);
    }

    function selectedValues(selectEl) {
        if (!selectEl) return [];
        return Array.from(selectEl.selectedOptions).map((o) => o.value);
    }

    function fillSelect(selectEl, values) {
        if (!selectEl) return;
        const prev = new Set(selectedValues(selectEl));
        selectEl.innerHTML = (values || [])
            .map((v) => `<option value="${escapeAttr(v)}"${prev.has(v) ? ' selected' : ''}>${escapeHtml(v)}</option>`)
            .join('');
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text == null ? '' : String(text);
        return d.innerHTML;
    }

    function escapeAttr(text) {
        return String(text ?? '')
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;');
    }

    function formatInt(n) {
        return Number(n || 0).toLocaleString('fr-FR');
    }

    function collectFilters() {
        return {
            date_start: $('cyber-date-start')?.value || null,
            date_end: $('cyber-date-end')?.value || null,
            pays: selectedValues($('cyber-filter-pays')),
            type_activite: selectedValues($('cyber-filter-activite')),
            gravite: selectedValues($('cyber-filter-gravite')),
            type_utilisateur: selectedValues($('cyber-filter-user')),
            service_cible: selectedValues($('cyber-filter-service')),
            granularity: STATE.granularity,
            top_dimension: STATE.topDimension,
            donut_mode: STATE.donutMode,
        };
    }

    function applyOptions(options) {
        if (!options) return;
        if (options.date_min && $('cyber-date-start') && !$('cyber-date-start').value) {
            $('cyber-date-start').value = options.date_min;
        }
        if (options.date_max && $('cyber-date-end') && !$('cyber-date-end').value) {
            $('cyber-date-end').value = options.date_max;
        }
        fillSelect($('cyber-filter-pays'), options.pays);
        fillSelect($('cyber-filter-activite'), options.type_activite);
        fillSelect($('cyber-filter-gravite'), options.gravite);
        fillSelect($('cyber-filter-user'), options.type_utilisateur);
        fillSelect($('cyber-filter-service'), options.service_cible);
    }

    function renderKpis(kpis) {
        if (!kpis) return;
        if ($('cyber-kpi-total')) $('cyber-kpi-total').textContent = formatInt(kpis.total_evenements);
        if ($('cyber-kpi-ips')) $('cyber-kpi-ips').textContent = formatInt(kpis.ip_uniques);
        if ($('cyber-kpi-fail')) $('cyber-kpi-fail').textContent = `${kpis.taux_echec} %`;
        if ($('cyber-kpi-crit')) $('cyber-kpi-crit').textContent = formatInt(kpis.alertes_critiques);
        if ($('cyber-kpi-pays')) $('cyber-kpi-pays').textContent = formatInt(kpis.nb_pays);
    }

    function renderMap(rows) {
        const el = $('cyber-chart-map');
        if (!el || typeof Plotly === 'undefined') return;
        if (!rows || !rows.length) {
            Plotly.purge(el);
            el.innerHTML = '<p class="cyber-empty">Aucune donnée géographique.</p>';
            return;
        }
        const colors = rows.map((r) => GRAVITE_COLOR[r.gravite_moyenne] || '#777');
        const trace = {
            type: 'scattergeo',
            lat: rows.map((r) => r.latitude),
            lon: rows.map((r) => r.longitude),
            text: rows.map((r) => `${r.ville}, ${r.pays}<br>${formatInt(r.evenements)} événements<br>Gravité moy. : ${r.gravite_moyenne}`),
            marker: {
                size: rows.map((r) => Math.max(8, Math.sqrt(r.evenements) * 1.8)),
                color: colors,
                line: { width: 0.5, color: '#1a1a1a' },
                opacity: 0.85,
            },
            hoverinfo: 'text',
        };
        const layout = {
            ...PLOT_LAYOUT,
            geo: {
                projection: { type: 'natural earth' },
                showland: true,
                landcolor: '#2a2b30',
                showocean: true,
                oceancolor: '#1c1d21',
                showcountries: true,
                countrycolor: '#3a3b40',
                bgcolor: 'rgba(0,0,0,0)',
            },
            height: 420,
            margin: { l: 0, r: 0, t: 10, b: 0 },
        };
        Plotly.newPlot(el, [trace], layout, { responsive: true, displayModeBar: false });
    }

    function renderTimeline(timeline) {
        const el = $('cyber-chart-timeline');
        if (!el || typeof Plotly === 'undefined') return;
        const points = timeline?.points || [];
        if (!points.length) {
            Plotly.purge(el);
            el.innerHTML = '<p class="cyber-empty">Aucune série temporelle.</p>';
            return;
        }
        const x = points.map((p) => p.horodatage);
        const y = points.map((p) => p.count);
        const anomX = points.filter((p) => p.anomalie).map((p) => p.horodatage);
        const anomY = points.filter((p) => p.anomalie).map((p) => p.count);
        const traces = [
            {
                type: 'scatter',
                mode: 'lines',
                x,
                y,
                name: 'Événements',
                line: { color: '#4dba87', width: 2 },
            },
            {
                type: 'scatter',
                mode: 'markers',
                x: anomX,
                y: anomY,
                name: 'Dépassement',
                marker: { color: '#dc3545', size: 8 },
            },
        ];
        const layout = {
            ...PLOT_LAYOUT,
            height: 340,
            shapes: [{
                type: 'line',
                xref: 'paper',
                x0: 0,
                x1: 1,
                y0: timeline.seuil,
                y1: timeline.seuil,
                line: { color: '#f0ad4e', width: 2, dash: 'dash' },
            }],
            annotations: [{
                xref: 'paper',
                x: 1,
                y: timeline.seuil,
                xanchor: 'right',
                text: `Seuil ${timeline.seuil}`,
                showarrow: false,
                font: { color: '#f0ad4e', size: 11 },
                yshift: 12,
            }],
        };
        Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });
    }

    function renderTop10(rows) {
        const el = $('cyber-chart-top10');
        if (!el || typeof Plotly === 'undefined') return;
        if (!rows || !rows.length) {
            Plotly.purge(el);
            el.innerHTML = '<p class="cyber-empty">Pas de top 10.</p>';
            return;
        }
        const ordered = [...rows].reverse();
        const trace = {
            type: 'bar',
            orientation: 'h',
            x: ordered.map((r) => r.count),
            y: ordered.map((r) => r.label),
            marker: { color: '#4dba87' },
            hovertemplate: '%{y}<br>%{x} événements<extra></extra>',
        };
        Plotly.newPlot(el, [trace], {
            ...PLOT_LAYOUT,
            height: 380,
            margin: { l: 120, r: 20, t: 10, b: 40 },
        }, { responsive: true, displayModeBar: false });
    }

    function renderDonut(rows) {
        const el = $('cyber-chart-donut');
        if (!el || typeof Plotly === 'undefined') return;
        if (!rows || !rows.length) {
            Plotly.purge(el);
            el.innerHTML = '<p class="cyber-empty">Pas de répartition.</p>';
            return;
        }
        const trace = {
            type: 'pie',
            labels: rows.map((r) => r.label),
            values: rows.map((r) => r.count),
            hole: 0.55,
            textinfo: 'label+percent',
            marker: {
                colors: ['#4dba87', '#5b8def', '#f0ad4e', '#e67e22', '#dc3545', '#9b59b6'],
            },
        };
        Plotly.newPlot(el, [trace], {
            ...PLOT_LAYOUT,
            height: 380,
            showlegend: false,
            margin: { l: 10, r: 10, t: 10, b: 10 },
        }, { responsive: true, displayModeBar: false });
    }

    function renderHeatmap(hm) {
        const el = $('cyber-chart-heatmap');
        if (!el || typeof Plotly === 'undefined') return;
        if (!hm) return;
        const trace = {
            type: 'heatmap',
            z: hm.z,
            x: (hm.heures || []).map(String),
            y: hm.jours || [],
            colorscale: [
                [0, '#1c1d21'],
                [0.35, '#1f4d3a'],
                [0.7, '#4dba87'],
                [1, '#a8f0c8'],
            ],
            hovertemplate: '%{y} %{x}h — %{z} événements<extra></extra>',
        };
        Plotly.newPlot(el, [trace], {
            ...PLOT_LAYOUT,
            height: 360,
            xaxis: { title: 'Heure', dtick: 1 },
            yaxis: { title: 'Jour', autorange: 'reversed' },
        }, { responsive: true, displayModeBar: false });
    }

    function riskClass(level) {
        const map = {
            faible: 'risk-low',
            moyen: 'risk-med',
            élevé: 'risk-high',
            critique: 'risk-crit',
        };
        return map[level] || 'risk-med';
    }

    function renderIpsTable() {
        const tbody = $('cyber-ips-tbody');
        if (!tbody) return;
        const key = STATE.sortKey;
        const dir = STATE.sortDir === 'asc' ? 1 : -1;
        const rows = [...STATE.topIps].sort((a, b) => {
            const av = a[key];
            const bv = b[key];
            if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir;
            return String(av).localeCompare(String(bv), 'fr') * dir;
        });
        tbody.innerHTML = rows.map((r) => `
            <tr>
                <td><code>${escapeHtml(r.adresse_ip)}</code></td>
                <td>${escapeHtml(r.pays)}</td>
                <td>${escapeHtml(r.service_vise)}</td>
                <td>${escapeHtml(r.compte_vise)}</td>
                <td>${formatInt(r.tentatives)}</td>
                <td>${escapeHtml(r.dernier_evenement)}</td>
                <td><span class="cyber-risk ${riskClass(r.niveau_risque)}">${escapeHtml(r.niveau_risque)}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="7" class="cyber-empty">Aucune IP.</td></tr>';
    }

    async function refreshCyberDashboard() {
        const section = $('section-cyber');
        if (!section || typeof Plotly === 'undefined') return;
        try {
            const res = await fetch('/api/admin/cyber/dashboard', {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(collectFilters()),
            });
            const json = await res.json();
            if (!res.ok) {
                if (typeof showToast === 'function') showToast(json.error || 'Erreur cyber', 'error');
                return;
            }
            const data = json.data || {};
            if (data.options) applyOptions(data.options);
            renderKpis(data.kpis);
            renderMap(data.map);
            renderTimeline(data.timeline);
            renderTop10(data.top10);
            renderDonut(data.donut);
            renderHeatmap(data.heatmap);
            STATE.topIps = data.top_ips || [];
            renderIpsTable();
            const src = $('cyber-source-label');
            if (src) {
                src.textContent = data.source === 'upload'
                    ? `Source : CSV téléversé (${formatInt(data.meta?.nb_lignes || 0)} lignes)`
                    : `Source : simulé (${formatInt(data.meta?.nb_lignes || 0)} lignes)`;
            }
            STATE.loaded = true;
        } catch (err) {
            console.error(err);
            if (typeof showToast === 'function') showToast('Erreur chargement monitoring cyber', 'error');
        }
    }

    function bindCyberUi() {
        const section = $('section-cyber');
        if (!section || section.dataset.bound === '1') return;
        section.dataset.bound = '1';

        $('cyber-apply-filters')?.addEventListener('click', () => refreshCyberDashboard());
        $('cyber-clear-filters')?.addEventListener('click', () => {
            ['cyber-filter-pays', 'cyber-filter-activite', 'cyber-filter-gravite', 'cyber-filter-user', 'cyber-filter-service']
                .forEach((id) => {
                    const el = $(id);
                    if (!el) return;
                    Array.from(el.options).forEach((o) => { o.selected = false; });
                });
            refreshCyberDashboard();
        });

        document.querySelectorAll('[data-cyber-granularity]').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[data-cyber-granularity]').forEach((b) => b.classList.remove('active'));
                btn.classList.add('active');
                STATE.granularity = btn.getAttribute('data-cyber-granularity') || 'heure';
                refreshCyberDashboard();
            });
        });

        document.querySelectorAll('[data-cyber-donut]').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[data-cyber-donut]').forEach((b) => b.classList.remove('active'));
                btn.classList.add('active');
                STATE.donutMode = btn.getAttribute('data-cyber-donut') || 'type_utilisateur';
                refreshCyberDashboard();
            });
        });

        $('cyber-top-dimension')?.addEventListener('change', (e) => {
            STATE.topDimension = e.target.value;
            refreshCyberDashboard();
        });

        document.querySelectorAll('#cyber-ips-table th[data-sort]').forEach((th) => {
            th.style.cursor = 'pointer';
            th.addEventListener('click', () => {
                const key = th.getAttribute('data-sort');
                if (STATE.sortKey === key) {
                    STATE.sortDir = STATE.sortDir === 'asc' ? 'desc' : 'asc';
                } else {
                    STATE.sortKey = key;
                    STATE.sortDir = key === 'tentatives' ? 'desc' : 'asc';
                }
                renderIpsTable();
            });
        });

        $('cyber-csv-upload')?.addEventListener('change', async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            const fd = new FormData();
            fd.append('file', file);
            const res = await fetch('/api/admin/cyber/upload', {
                method: 'POST',
                credentials: 'include',
                body: fd,
            });
            const json = await res.json().catch(() => ({}));
            if (typeof showToast === 'function') {
                showToast(res.ok ? (json.message || 'CSV chargé') : (json.error || 'Erreur upload'), res.ok ? 'success' : 'error');
            }
            if (res.ok) {
                if (json.options) {
                    $('cyber-date-start').value = json.options.date_min || '';
                    $('cyber-date-end').value = json.options.date_max || '';
                    applyOptions(json.options);
                }
                refreshCyberDashboard();
            }
            e.target.value = '';
        });

        $('cyber-reset-btn')?.addEventListener('click', async () => {
            const res = await fetch('/api/admin/cyber/reset', {
                method: 'POST',
                credentials: 'include',
            });
            const json = await res.json().catch(() => ({}));
            if (typeof showToast === 'function') {
                showToast(res.ok ? (json.message || 'Jeu simulé') : (json.error || 'Erreur'), res.ok ? 'success' : 'error');
            }
            if (res.ok && json.options) {
                $('cyber-date-start').value = json.options.date_min || '';
                $('cyber-date-end').value = json.options.date_max || '';
                applyOptions(json.options);
                refreshCyberDashboard();
            }
        });
    }

    window.loadCyberDashboard = function loadCyberDashboard() {
        bindCyberUi();
        refreshCyberDashboard();
    };
})();
