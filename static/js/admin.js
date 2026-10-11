// ============================================
// Admin Panel JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Toggle user dropdown
    const userMenuTrigger = document.getElementById('userMenuTrigger');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userMenuTrigger && userDropdown) {
        userMenuTrigger.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        document.addEventListener('click', function(e) {
            if (!userMenuTrigger.contains(e.target) && !userDropdown.contains(e.target)) {
                userDropdown.classList.remove('show');
            }
        });
    }

    initAdminGlobalSearch();
    
    // Support modal
    const supportBtn = document.getElementById('supportBtn');
    if (supportBtn) {
        supportBtn.addEventListener('click', function() {
            openSupportModal();
        });
    }
    
    // Navigation menu: les liens /admin/<section> naviguent normalement (routes serveur)
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            const href = this.getAttribute('href') || '';
            // Ne pas forcer l'état actif sur les liens externes (retour site)
            if (href.startsWith('/admin')) {
                menuItems.forEach(mi => mi.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // Close modal on overlay click
    const supportModal = document.getElementById('supportModal');
    if (supportModal) {
        supportModal.addEventListener('click', function(e) {
            if (e.target === supportModal) {
                closeSupportModal();
            }
        });
    }
    
    // Close service modal on overlay click
    const serviceModal = document.getElementById('serviceModal');
    if (serviceModal) {
        serviceModal.addEventListener('click', function(e) {
            if (e.target === serviceModal) {
                if (typeof closeServiceModal === 'function') {
                    closeServiceModal();
                }
            }
        });
    }
    
    // Close project modal on overlay click
    const projectModal = document.getElementById('projectModal');
    if (projectModal) {
        projectModal.addEventListener('click', function(e) {
            if (e.target === projectModal) {
                if (typeof closeProjectModal === 'function') {
                    closeProjectModal();
                }
            }
        });
    }
    
    // Close project detail modal on overlay click
    const projectDetailModal = document.getElementById('projectDetailModal');
    if (projectDetailModal) {
        projectDetailModal.addEventListener('click', function(e) {
            if (e.target === projectDetailModal) {
                if (typeof closeProjectDetailModal === 'function') {
                    closeProjectDetailModal();
                }
            }
        });
    }
});

// ============================================
// Recherche globale (barre collée en haut)
// ============================================
function initAdminGlobalSearch() {
    const input = document.getElementById('admin-global-search');
    const clearBtn = document.getElementById('admin-search-clear');
    if (!input) return;

    let debounceTimer = null;

    const syncClear = () => {
        if (!clearBtn) return;
        clearBtn.hidden = !input.value.trim();
    };

    const runSearch = () => {
        const query = input.value.trim().toLowerCase();
        syncClear();
        filterActiveAdminSection(query);
    };

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(runSearch, 160);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            input.value = '';
            runSearch();
            input.blur();
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            input.value = '';
            runSearch();
            input.focus();
        });
    }

    syncClear();
}

function filterActiveAdminSection(query) {
    const section = document.querySelector('.content-section.active-section');
    if (!section) return;

    const cards = section.querySelectorAll('.admin-card');
    if (!cards.length) return;

    let visible = 0;
    cards.forEach((card) => {
        const text = (card.textContent || '').toLowerCase();
        const match = !query || text.includes(query);
        card.style.display = match ? '' : 'none';
        if (match) visible += 1;
    });

    let empty = section.querySelector('.admin-search-empty');
    if (query && visible === 0) {
        if (!empty) {
            empty = document.createElement('p');
            empty.className = 'admin-search-empty';
            empty.style.cssText = 'color:var(--gray);text-align:center;padding:1.5rem;';
            section.appendChild(empty);
        }
        empty.textContent = `Aucun résultat pour « ${query} »`;
        empty.hidden = false;
    } else if (empty) {
        empty.hidden = true;
    }
}

window.filterActiveAdminSection = filterActiveAdminSection;

// ============================================
// Support Modal Functions
// ============================================
function openSupportModal() {
    const modal = document.getElementById('supportModal');
    if (modal) {
        modal.classList.add('open');
    }
}

function closeSupportModal() {
    const modal = document.getElementById('supportModal');
    if (modal) {
        modal.classList.remove('open');
    }
}

// ============================================
// Right Panel Functions
// ============================================
function toggleRightPanel() {
    const rightPanel = document.getElementById('right-panel');
    const toggleButton = document.getElementById('right-panel-toggle');
    const mainContent = document.querySelector('.main-content');
    
    if (!rightPanel) return;
    
    const isHidden = rightPanel.classList.contains('hidden');
    
    if (isHidden) {
        rightPanel.classList.remove('hidden');
        rightPanel.setAttribute('aria-hidden', 'false');
        if (toggleButton) toggleButton.classList.remove('show');
        if (mainContent) mainContent.classList.add('panel-open');
    } else {
        rightPanel.classList.add('hidden');
        rightPanel.setAttribute('aria-hidden', 'true');
        if (toggleButton) toggleButton.classList.add('show');
        if (mainContent) mainContent.classList.remove('panel-open');
    }
}

// ============================================
// Panel Stats Functions
// ============================================
function loadPanelStats() {
    // Simulate loading stats
    const refreshBtn = document.querySelector('.panel-refresh-btn i');
    if (refreshBtn) {
        refreshBtn.style.animation = 'spin 1s linear';
        setTimeout(() => {
            refreshBtn.style.animation = '';
            updatePanelStats();
        }, 1000);
    } else {
        updatePanelStats();
    }
}

async function updatePanelStats() {
    // Update last update time
    const lastUpdate = document.getElementById('panel-last-update');
    if (lastUpdate) {
        const now = new Date();
        lastUpdate.textContent = `Mis à jour: ${now.toLocaleTimeString('fr-FR')}`;
    }
    
    // Charger les statistiques depuis l'API
    try {
        const response = await fetch('/api/analytics/stats?days=30', {
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        
        if (response.ok) {
            const stats = await response.json();
            
            // Mettre à jour les statistiques du panel
            const activeProjects = document.getElementById('panel-active-projects');
            if (activeProjects) {
                // Afficher les projets publiés
                const publishedProjects = stats.projects_by_status?.published || stats.total_projects || 0;
                activeProjects.textContent = publishedProjects;
            }
            
            const panelServices = document.getElementById('panel-services');
            if (panelServices) {
                panelServices.textContent = stats.total_services || 0;
            }
            
            const panelContacts = document.getElementById('panel-contacts');
            if (panelContacts) {
                // Afficher les messages non lus avec indicateur
                const unreadCount = stats.unread_contacts || 0;
                const totalCount = stats.total_contacts || 0;
                if (unreadCount > 0) {
                    panelContacts.innerHTML = `${totalCount} <span style="color: var(--green); font-size: 0.75em;">(${unreadCount} non lus)</span>`;
                } else {
                    panelContacts.textContent = totalCount;
                }
            }
            
            // Mettre à jour le taux d'engagement
            const satisfaction = document.getElementById('panel-satisfaction');
            if (satisfaction) {
                const engagement = stats.engagement_rate || 0;
                satisfaction.textContent = `${engagement}%`;
            }
            
            // Mettre à jour les vues totales
            const totalViews = document.getElementById('panel-total-views');
            if (totalViews) {
                const views = stats.total_views || 0;
                totalViews.textContent = views.toLocaleString('fr-FR');
            }
        } else {
            console.error('Erreur lors du chargement des stats:', response.status);
        }
    } catch (error) {
        console.debug('Erreur lors du chargement des stats:', error);
    }
}

async function loadDashboardStats() {
    try {
        const response = await fetch('/api/analytics/stats?days=30', {
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Pas connecté, ignorer
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        
        // Mettre à jour les statistiques du dashboard
        const totalProjects = document.getElementById('total-projects');
        if (totalProjects) {
            totalProjects.textContent = stats.total_projects || 0;
        }
        
        const totalViews = document.getElementById('total-views');
        if (totalViews) {
            totalViews.textContent = (stats.total_views || 0).toLocaleString('fr-FR');
        }
        
        const totalVisitors = document.getElementById('total-visitors');
        if (totalVisitors) {
            totalVisitors.textContent = (stats.total_visitors || 0).toLocaleString('fr-FR');
        }
        
        const engagementRate = document.getElementById('engagement-rate');
        if (engagementRate) {
            engagementRate.textContent = `${stats.engagement_rate || 0}%`;
        }
        
        // Charger les graphiques
        loadCharts(stats);
        
        // Charger le top des projets
        loadTopProjects(stats.top_projects || []);

        const failed = document.getElementById('failed-logins');
        if (failed) failed.textContent = stats.failed_logins_24h || 0;
        const alerts = document.getElementById('security-alerts');
        if (alerts) alerts.textContent = stats.security_alerts_24h || 0;
        const openErr = document.getElementById('open-errors');
        if (openErr) openErr.textContent = stats.open_errors || 0;
        loadMonitoringLists();
    } catch (error) {
        console.debug('Erreur lors du chargement des stats du dashboard:', error);
    }
}

async function loadMonitoringLists() {
    try {
        const response = await fetch('/api/monitoring/overview', { credentials: 'include' });
        if (!response.ok) return;
        const data = await response.json();
        const sec = document.getElementById('security-events-list');
        if (sec) {
            const items = data.recent_security || [];
            sec.innerHTML = items.length
                ? items.map((e) => `<div class="admin-card dashboard-list-item"><strong>${e.type || ''}</strong> · ${e.severity || ''} · <span class="dashboard-meta">${e.path || ''}</span><br><small class="dashboard-meta">${e.created_at || ''}</small></div>`).join('')
                : '<p class="dashboard-empty">Aucun événement récent.</p>';
        }
        const err = document.getElementById('error-logs-list');
        if (err) {
            const items = data.recent_errors || [];
            err.innerHTML = items.length
                ? items.map((e) => `<div class="admin-card dashboard-list-item"><strong>${e.level || 'error'}</strong> — ${e.message || ''}<br><small class="dashboard-meta">${e.created_at || ''} · ${e.path || ''}</small></div>`).join('')
                : '<p class="dashboard-empty">Aucune erreur récente.</p>';
        }
    } catch (e) {
        console.debug(e);
    }
}

let careerCache = {};

function escapeCareerHtml(text) {
    if (text == null) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function openCareerModalEl(modal) {
    if (!modal) return;
    if (typeof openModalEl === 'function') {
        openModalEl(modal);
        return;
    }
    modal.style.display = 'flex';
    modal.classList.add('open');
}

function closeCareerModalEl(modal) {
    if (!modal) return;
    if (typeof closeModalEl === 'function') {
        closeModalEl(modal);
        return;
    }
    modal.style.display = 'none';
    modal.classList.remove('open');
}

function fillCareerForm(item) {
    const set = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.value = value ?? '';
    };
    set('career-id', item?.id || '');
    set('career-title', item?.title || '');
    set('career-org', item?.org || '');
    set('career-location', item?.location || '');
    set('career-start', item?.start || '');
    set('career-end', item?.end || '');
    set('career-kind', item?.kind || 'emploi');
    set('career-status', item?.status || 'published');
    set('career-order', item?.order_index ?? 0);
    set('career-bullets', item?.bullets || '');
}

function initCareerForm() {
    const form = document.getElementById('career-form');
    if (!form || form.dataset.bound) return;
    form.dataset.bound = '1';
    form.addEventListener('submit', handleCareerSubmit);
}

async function loadCareerAdmin() {
    const list = document.getElementById('career-list');
    if (!list) return;
    initCareerForm();
    const res = await fetch('/api/career', { credentials: 'include' });
    if (!res.ok) {
        showToast('Impossible de charger le parcours', 'error');
        return;
    }
    const items = await res.json();
    careerCache = {};
    (items || []).forEach((item) => {
        if (item && item.id != null) careerCache[item.id] = item;
    });

    const renderList = (item) => {
        const period = `${escapeCareerHtml(item.start || '')} → ${escapeCareerHtml(item.end || 'aujourd’hui')}`;
        const heading = [item.title, item.org].filter(Boolean).map(escapeCareerHtml).join(' — ');
        return `
        <div class="admin-card">
            <div class="admin-card-row">
                <div class="admin-card-main">
                    <h3>${heading || 'Sans titre'}</h3>
                    <div class="admin-card-meta">
                        <span>${period}</span>
                        <span>${escapeCareerHtml(item.kind || '')}</span>
                        <span>${escapeCareerHtml(item.location || '')}</span>
                    </div>
                    <p>${escapeCareerHtml(item.bullets || '')}</p>
                </div>
                <div class="admin-card-actions">
                    <button type="button" class="btn btn-sm btn-ghost" onclick="editCareer(${item.id})"><i class="fas fa-edit"></i> Modifier</button>
                    <button type="button" class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteCareer(${item.id})"><i class="fas fa-trash"></i> Supprimer</button>
                </div>
            </div>
        </div>`;
    };
    const renderGrid = (item) => {
        const initial = (item.title || 'P').trim().charAt(0).toUpperCase();
        const period = `${escapeCareerHtml(item.start || '')} → ${escapeCareerHtml(item.end || 'aujourd’hui')}`;
        return `
            <article class="admin-grid-card">
                <div class="admin-grid-card-icon">${escapeCareerHtml(initial)}</div>
                <h3 class="admin-grid-card-title">${escapeCareerHtml(item.title || 'Sans titre')}</h3>
                <p class="admin-grid-card-text">${escapeCareerHtml(item.org || '')}</p>
                <div class="admin-card-meta">
                    <span>${period}</span>
                    <span>${escapeCareerHtml(item.kind || '')}</span>
                </div>
                <div class="admin-card-actions">
                    <button type="button" class="btn btn-sm btn-ghost" onclick="editCareer(${item.id})" title="Modifier"><i class="fas fa-edit"></i></button>
                    <button type="button" class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteCareer(${item.id})" title="Supprimer"><i class="fas fa-trash"></i></button>
                </div>
            </article>
        `;
    };
    setAdminListItems('career', items || [], {
        listId: 'career-list',
        paginationId: 'career-pagination',
        countId: 'career-count-label',
        listBtnId: 'career-view-list',
        gridBtnId: 'career-view-grid',
        emptyHtml: '<p class="admin-empty">Aucune entrée.</p>',
        countLabel: (n) => (n === 1 ? '1 entrée' : `${n} entrées`),
        renderList,
        renderGrid,
    });
}

function openCareerModal() {
    initCareerForm();
    const modal = document.getElementById('careerModal');
    const titleEl = document.getElementById('careerModalTitle');
    if (titleEl) titleEl.textContent = 'Nouvelle entrée';
    fillCareerForm(null);
    openCareerModalEl(modal);
}

function editCareer(id) {
    initCareerForm();
    const item = careerCache[id];
    if (!item) {
        showToast('Entrée introuvable', 'error');
        return;
    }
    const modal = document.getElementById('careerModal');
    const titleEl = document.getElementById('careerModalTitle');
    if (titleEl) titleEl.textContent = 'Modifier l’entrée';
    fillCareerForm(item);
    openCareerModalEl(modal);
}

function closeCareerModal() {
    closeCareerModalEl(document.getElementById('careerModal'));
}

async function handleCareerSubmit(event) {
    event.preventDefault();
    const id = (document.getElementById('career-id')?.value || '').trim();
    const title = (document.getElementById('career-title')?.value || '').trim();
    if (!title) {
        showToast('Le titre est requis', 'error');
        return;
    }
    const payload = {
        title,
        org: (document.getElementById('career-org')?.value || '').trim(),
        location: (document.getElementById('career-location')?.value || '').trim(),
        start: (document.getElementById('career-start')?.value || '').trim(),
        end: (document.getElementById('career-end')?.value || '').trim(),
        kind: document.getElementById('career-kind')?.value || 'emploi',
        status: document.getElementById('career-status')?.value || 'published',
        order_index: parseInt(document.getElementById('career-order')?.value, 10) || 0,
        bullets: (document.getElementById('career-bullets')?.value || '').trim(),
    };
    const url = id ? `/api/career/${id}` : '/api/career';
    const method = id ? 'PUT' : 'POST';
    const res = await fetch(url, {
        method,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        showToast(data.error || 'Erreur enregistrement parcours', 'error');
        return;
    }
    showToast(id ? 'Parcours mis à jour' : 'Parcours ajouté', 'success');
    closeCareerModal();
    loadCareerAdmin();
}

async function deleteCareer(id) {
    const ok = await adminConfirm({
        title: 'Supprimer cette entrée ?',
        message: 'Elle sera retirée du parcours public et placée en corbeille.',
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!ok) return;
    const res = await fetch(`/api/career/${id}`, { method: 'DELETE', credentials: 'include' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        showToast(data.error || 'Erreur lors de la suppression', 'error');
        return;
    }
    showToast('Entrée supprimée', 'success');
    loadCareerAdmin();
}

let certsCache = {};
let certsAllItems = [];
let certsPage = 1;
const CERTS_PER_PAGE = 9;
let certsView = 'list';

try {
    const savedView = localStorage.getItem('admin-certs-view');
    if (savedView === 'grid' || savedView === 'list') certsView = savedView;
} catch (_) { /* ignore */ }

function openCertModalEl(modal) {
    if (!modal) return;
    if (typeof openModalEl === 'function') {
        openModalEl(modal);
        return;
    }
    modal.style.display = 'flex';
    modal.style.opacity = '1';
    modal.classList.add('open');
}

function closeCertModalEl(modal) {
    if (!modal) return;
    if (typeof closeModalEl === 'function') {
        closeModalEl(modal);
        return;
    }
    modal.style.display = 'none';
    modal.style.opacity = '0';
    modal.classList.remove('open');
}

function initCertForm() {
    const form = document.getElementById('cert-form');
    if (!form || form.dataset.bound) return;
    form.dataset.bound = '1';
    form.addEventListener('submit', handleCertSubmit);
}

function certImageUrl(code) {
    if (!code) return '';
    return (
        'https://s3.amazonaws.com/coursera_assets/meta_images/generated/' +
        `CERTIFICATE_LANDING_PAGE/CERTIFICATE_LANDING_PAGE~${code}/` +
        `CERTIFICATE_LANDING_PAGE~${code}.jpeg`
    );
}

function syncCertsViewToggle() {
    const listBtn = document.getElementById('certs-view-list');
    const gridBtn = document.getElementById('certs-view-grid');
    const list = document.getElementById('certs-list');
    if (listBtn) {
        listBtn.classList.toggle('is-active', certsView === 'list');
        listBtn.setAttribute('aria-pressed', certsView === 'list' ? 'true' : 'false');
    }
    if (gridBtn) {
        gridBtn.classList.toggle('is-active', certsView === 'grid');
        gridBtn.setAttribute('aria-pressed', certsView === 'grid' ? 'true' : 'false');
    }
    if (list) list.dataset.view = certsView;
}

function setCertsView(view) {
    certsView = view === 'grid' ? 'grid' : 'list';
    try {
        localStorage.setItem('admin-certs-view', certsView);
    } catch (_) { /* ignore */ }
    syncCertsViewToggle();
    renderCertsAdmin();
}

function goToCertsPage(page) {
    const totalPages = Math.max(1, Math.ceil(certsAllItems.length / CERTS_PER_PAGE));
    certsPage = Math.min(Math.max(1, Number(page) || 1), totalPages);
    renderCertsAdmin();
    const shell = document.querySelector('#section-certifications .certs-shell');
    if (shell) shell.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderCertItemList(item) {
    const domain = item.domain || 'autre';
    const initial = domain.trim().charAt(0).toUpperCase() || 'C';
    const status = (item.status || 'published').toLowerCase();
    const statusClass = status === 'published' ? 'is-published' : status === 'draft' ? 'is-draft' : 'is-muted';
    return `
        <article class="cert-item${item.featured ? ' is-featured' : ''}">
            <div class="cert-item-icon" aria-hidden="true">${initial}</div>
            <div class="cert-item-body">
                <div class="cert-item-top">
                    <div class="cert-item-heading">
                        <h3 class="cert-item-title">${item.title || 'Sans titre'}</h3>
                        ${item.featured ? '<span class="cert-chip cert-chip--star"><i class="fas fa-star"></i> Vedette</span>' : ''}
                    </div>
                    <div class="cert-item-actions">
                        <button type="button" class="btn btn-ghost btn-sm" onclick="viewCert(${item.id})">
                            <i class="fas fa-eye"></i> Visualiser
                        </button>
                        <button type="button" class="btn btn-ghost btn-sm" onclick="editCert(${item.id})">
                            <i class="fas fa-edit"></i> Modifier
                        </button>
                        <button type="button" class="btn btn-ghost btn-sm btn-danger-ghost" onclick="deleteCert(${item.id})">
                            <i class="fas fa-trash"></i> Supprimer
                        </button>
                    </div>
                </div>
                <div class="cert-item-meta">
                    <span class="cert-chip">${domain}</span>
                    <span class="cert-chip cert-chip--code">${item.code || '—'}</span>
                    <span class="cert-chip cert-chip--status ${statusClass}">${item.status || 'published'}</span>
                </div>
            </div>
        </article>
    `;
}

function renderCertItemGrid(item) {
    const domain = item.domain || 'autre';
    const status = (item.status || 'published').toLowerCase();
    const statusClass = status === 'published' ? 'is-published' : status === 'draft' ? 'is-draft' : 'is-muted';
    const imageUrl = certImageUrl(item.code || '');
    return `
        <article class="cert-grid-card${item.featured ? ' is-featured' : ''}">
            <button type="button" class="cert-grid-media" onclick="viewCert(${item.id})" title="Visualiser">
                ${imageUrl ? `<img src="${imageUrl}" alt="" loading="lazy" onerror="this.classList.add('is-broken'); this.nextElementSibling.hidden=false;">` : ''}
                <div class="cert-grid-fallback" ${imageUrl ? 'hidden' : ''}><i class="fas fa-certificate"></i></div>
                ${item.featured ? '<span class="cert-chip cert-chip--star cert-grid-badge"><i class="fas fa-star"></i> Vedette</span>' : ''}
            </button>
            <div class="cert-grid-body">
                <h3 class="cert-grid-title">${item.title || 'Sans titre'}</h3>
                <div class="cert-item-meta">
                    <span class="cert-chip">${domain}</span>
                    <span class="cert-chip cert-chip--status ${statusClass}">${item.status || 'published'}</span>
                </div>
                <p class="cert-grid-code">${item.code || '—'}</p>
                <div class="cert-item-actions">
                    <button type="button" class="btn btn-ghost btn-sm" onclick="viewCert(${item.id})" title="Visualiser"><i class="fas fa-eye"></i></button>
                    <button type="button" class="btn btn-ghost btn-sm" onclick="editCert(${item.id})" title="Modifier"><i class="fas fa-edit"></i></button>
                    <button type="button" class="btn btn-ghost btn-sm btn-danger-ghost" onclick="deleteCert(${item.id})" title="Supprimer"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        </article>
    `;
}

function renderCertsAdmin() {
    const list = document.getElementById('certs-list');
    const countLabel = document.getElementById('certs-count-label');
    const pagination = document.getElementById('certs-pagination');
    if (!list) return;

    syncCertsViewToggle();

    const total = certsAllItems.length;
    if (countLabel) {
        countLabel.textContent = total === 1 ? '1 certification' : `${total} certifications`;
    }

    if (!total) {
        list.className = 'admin-list certs-list';
        list.dataset.view = certsView;
        list.innerHTML = `
            <div class="certs-empty">
                <span class="certs-empty-icon" aria-hidden="true"><i class="fas fa-certificate"></i></span>
                <p class="certs-empty-title">Aucune certification</p>
                <p class="certs-empty-hint">Ajoutez un diplôme ou un certificat à mettre en avant.</p>
            </div>
        `;
        if (pagination) pagination.innerHTML = '';
        return;
    }

    const totalPages = Math.max(1, Math.ceil(total / CERTS_PER_PAGE));
    if (certsPage > totalPages) certsPage = totalPages;
    const start = (certsPage - 1) * CERTS_PER_PAGE;
    const pageItems = certsAllItems.slice(start, start + CERTS_PER_PAGE);

    list.dataset.view = certsView;
    list.className = certsView === 'grid'
        ? 'certs-list certs-grid'
        : 'admin-list certs-list';

    list.innerHTML = pageItems.map((item) => (
        certsView === 'grid' ? renderCertItemGrid(item) : renderCertItemList(item)
    )).join('');

    if (typeof createPagination === 'function' && pagination) {
        createPagination(certsPage, totalPages, 'goToCertsPage', 'certs-pagination');
    } else if (pagination) {
        pagination.innerHTML = totalPages > 1
            ? `<div class="pagination"><button class="pagination-btn" ${certsPage <= 1 ? 'disabled' : `onclick="goToCertsPage(${certsPage - 1})"`}>‹ Précédent</button>
               <span class="pagination-ellipsis">Page ${certsPage} / ${totalPages}</span>
               <button class="pagination-btn" ${certsPage >= totalPages ? 'disabled' : `onclick="goToCertsPage(${certsPage + 1})"`}>Suivant ›</button></div>`
            : '';
    }
}

async function loadCertsAdmin() {
    const list = document.getElementById('certs-list');
    if (!list) return;
    initCertForm();
    const res = await fetch('/api/certifications', { credentials: 'include' });
    if (!res.ok) return;
    const items = await res.json();
    certsAllItems = Array.isArray(items) ? items : [];
    certsCache = {};
    certsAllItems.forEach((item) => {
        if (item && item.id != null) certsCache[item.id] = item;
    });
    certsPage = 1;
    renderCertsAdmin();
}

function fillCertForm(item) {
    document.getElementById('cert-id').value = item?.id || '';
    document.getElementById('cert-title').value = item?.title || '';
    document.getElementById('cert-code').value = item?.code || '';
    document.getElementById('cert-domain').value = item?.domain || 'data-ai';
    document.getElementById('cert-status').value = item?.status || 'published';
    document.getElementById('cert-order').value = item?.order_index ?? 0;
    document.getElementById('cert-url').value = item?.url || '';
    document.getElementById('cert-featured').checked = Boolean(Number(item?.featured));
}

function openCertModal() {
    initCertForm();
    const modal = document.getElementById('certModal');
    const titleEl = document.getElementById('certModalTitle');
    if (titleEl) titleEl.textContent = 'Nouvelle certification';
    fillCertForm(null);
    openCertModalEl(modal);
}

function editCert(id) {
    initCertForm();
    const item = certsCache[id];
    if (!item) {
        showToast('Certification introuvable', 'error');
        return;
    }
    const modal = document.getElementById('certModal');
    const titleEl = document.getElementById('certModalTitle');
    if (titleEl) titleEl.textContent = 'Modifier la certification';
    fillCertForm(item);
    openCertModalEl(modal);
}

function closeCertModal() {
    closeCertModalEl(document.getElementById('certModal'));
}

function viewCert(id) {
    const item = certsCache[id];
    if (!item) {
        showToast('Certification introuvable', 'error');
        return;
    }
    const code = item.code || '';
    const certUrl = item.url || (code
        ? `https://www.coursera.org/account/accomplishments/certificate/${code}`
        : '');
    const verifyUrl = code
        ? `https://www.coursera.org/account/accomplishments/verify/${code}`
        : '';
    const imageUrl = certImageUrl(code);

    const titleEl = document.getElementById('cert-view-title');
    const domainEl = document.getElementById('cert-view-domain');
    const codeEl = document.getElementById('cert-view-code');
    const statusEl = document.getElementById('cert-view-status');
    const img = document.getElementById('cert-view-image');
    const fallback = document.getElementById('cert-view-fallback');
    const link = document.getElementById('cert-view-link');
    const verify = document.getElementById('cert-view-verify');

    if (titleEl) titleEl.textContent = item.title || 'Certification';
    if (domainEl) domainEl.textContent = item.domain || '—';
    if (codeEl) codeEl.textContent = code || '—';
    if (statusEl) statusEl.textContent = item.status || 'published';

    if (link) {
        if (certUrl) {
            link.href = certUrl;
            link.hidden = false;
        } else {
            link.hidden = true;
        }
    }
    if (verify) {
        if (verifyUrl) {
            verify.href = verifyUrl;
            verify.hidden = false;
        } else {
            verify.hidden = true;
        }
    }

    if (img && fallback) {
        if (imageUrl) {
            img.hidden = false;
            fallback.hidden = true;
            img.alt = item.title || 'Certificat';
            img.onerror = () => {
                img.hidden = true;
                fallback.hidden = false;
            };
            img.src = imageUrl;
        } else {
            img.removeAttribute('src');
            img.hidden = true;
            fallback.hidden = false;
        }
    }

    openCertModalEl(document.getElementById('certViewModal'));
}

function closeCertViewModal() {
    closeCertModalEl(document.getElementById('certViewModal'));
}

async function handleCertSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('cert-id').value;
    const payload = {
        title: document.getElementById('cert-title').value.trim(),
        code: document.getElementById('cert-code').value.trim(),
        domain: document.getElementById('cert-domain').value,
        status: document.getElementById('cert-status').value || 'published',
        order_index: Number(document.getElementById('cert-order').value || 0),
        url: document.getElementById('cert-url').value.trim(),
        featured: document.getElementById('cert-featured').checked,
    };
    if (!payload.title || !payload.code) {
        showToast('Titre et code requis', 'error');
        return;
    }
    const isEdit = Boolean(id);
    const res = await fetch(isEdit ? `/api/certifications/${id}` : '/api/certifications', {
        method: isEdit ? 'PUT' : 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        showToast(data.error || 'Erreur lors de l’enregistrement', 'error');
        return;
    }
    showToast(isEdit ? 'Certification mise à jour' : 'Certification ajoutée', 'success');
    closeCertModal();
    loadCertsAdmin();
}

async function deleteCert(id) {
    const ok = await adminConfirm({
        title: 'Supprimer cette certification ?',
        message: 'Elle sera déplacée dans la corbeille et retirée du site public.',
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!ok) return;
    const res = await fetch(`/api/certifications/${id}`, { method: 'DELETE', credentials: 'include' });
    if (res.ok) {
        showToast('Certification supprimée', 'success');
        loadCertsAdmin();
    } else {
        showToast('Erreur lors de la suppression', 'error');
    }
}

/** @deprecated alias — soft-delete */
async function archiveCert(id) {
    return deleteCert(id);
}

const LEGAL_PAGE_LABELS = {
    confidentialite: 'Confidentialité',
    mentions: 'Mentions légales',
};

function escapeLegalPreview(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function updateLegalPreview() {
    const slug = document.getElementById('legal-slug')?.value || 'confidentialite';
    const title = document.getElementById('legal-title')?.value || '';
    const body = document.getElementById('legal-body')?.value || '';
    const kicker = document.getElementById('legal-preview-kicker');
    const titleEl = document.getElementById('legal-preview-title');
    const bodyEl = document.getElementById('legal-preview-body');
    if (kicker) kicker.textContent = LEGAL_PAGE_LABELS[slug] || 'Page légale';
    if (titleEl) titleEl.textContent = title.trim() || 'Titre de la page';
    if (bodyEl) {
        const text = body.trim();
        bodyEl.innerHTML = text
            ? escapeLegalPreview(text).replace(/\n/g, '<br>')
            : 'Le contenu apparaîtra ici.';
    }
}

function initLegalEditor() {
    const form = document.getElementById('legal-form');
    if (!form || form.dataset.previewBound) return;
    form.dataset.previewBound = '1';
    form.addEventListener('input', updateLegalPreview);
    updateLegalPreview();
}

function selectLegalPage(slug) {
    const input = document.getElementById('legal-slug');
    if (input) input.value = slug;
    document.querySelectorAll('.legal-tab').forEach((tab) => {
        const active = tab.getAttribute('data-legal-slug') === slug;
        tab.classList.toggle('is-active', active);
        tab.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    loadLegalPage();
}

async function loadLegalPage() {
    initLegalEditor();
    const slug = document.getElementById('legal-slug')?.value;
    if (!slug) return;
    const res = await fetch(`/api/site-pages/${slug}`, { credentials: 'include' });
    if (!res.ok) return;
    const page = await res.json();
    const title = document.getElementById('legal-title');
    const body = document.getElementById('legal-body');
    if (title) title.value = page.title || '';
    if (body) body.value = page.body || '';
    updateLegalPreview();
}

async function saveLegalPage(event) {
    event.preventDefault();
    const slug = document.getElementById('legal-slug').value;
    const title = document.getElementById('legal-title').value;
    const body = document.getElementById('legal-body').value;
    const res = await fetch(`/api/site-pages/${slug}`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body }),
    });
    showToast(res.ok ? 'Page enregistrée' : 'Erreur enregistrement', res.ok ? 'success' : 'error');
    if (res.ok) updateLegalPreview();
    return false;
}

function formatMediaSize(bytes) {
    const n = Number(bytes) || 0;
    if (n < 1024) return `${n} o`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} Ko`;
    return `${(n / (1024 * 1024)).toFixed(1)} Mo`;
}

function isMediaImage(name) {
    return /\.(jpe?g|png|webp|gif)$/i.test(name || '');
}

function resetMediaDropzone() {
    const title = document.getElementById('media-dropzone-title');
    const fileLabel = document.getElementById('media-dropzone-file');
    const zone = document.getElementById('media-dropzone');
    if (title) title.hidden = false;
    if (fileLabel) {
        fileLabel.hidden = true;
        fileLabel.textContent = '';
    }
    if (zone) zone.classList.remove('has-file', 'is-dragover');
}

function initMediaDropzone() {
    const input = document.getElementById('media-file');
    const zone = document.getElementById('media-dropzone');
    const title = document.getElementById('media-dropzone-title');
    const fileLabel = document.getElementById('media-dropzone-file');
    if (!input || !zone || zone.dataset.bound) return;
    zone.dataset.bound = '1';

    const syncFile = () => {
        const file = input.files && input.files[0];
        if (!file) {
            resetMediaDropzone();
            return;
        }
        zone.classList.add('has-file');
        if (title) title.hidden = true;
        if (fileLabel) {
            fileLabel.hidden = false;
            fileLabel.textContent = `${file.name} · ${formatMediaSize(file.size)}`;
        }
    };

    input.addEventListener('change', syncFile);
    ['dragenter', 'dragover'].forEach((evt) => {
        zone.addEventListener(evt, (e) => {
            e.preventDefault();
            zone.classList.add('is-dragover');
        });
    });
    ['dragleave', 'drop'].forEach((evt) => {
        zone.addEventListener(evt, (e) => {
            e.preventDefault();
            zone.classList.remove('is-dragover');
        });
    });
    zone.addEventListener('drop', (e) => {
        const files = e.dataTransfer && e.dataTransfer.files;
        if (!files || !files.length) return;
        try {
            const dt = new DataTransfer();
            dt.items.add(files[0]);
            input.files = dt.files;
        } catch (_) {
            return;
        }
        syncFile();
    });
}

async function loadMediaAdmin() {
    const list = document.getElementById('media-list');
    if (!list) return;
    initMediaDropzone();
    const res = await fetch('/api/media', { credentials: 'include' });
    if (!res.ok) return;
    const items = await res.json();
    const renderGrid = (m) => {
        const name = m.original_name || m.filename || 'fichier';
        const path = m.path || '';
        const url = path ? `/static/${path}` : '';
        const thumb = isMediaImage(name) && url
            ? `<img src="${url}" alt="" loading="lazy">`
            : `<i class="fas fa-file-alt"></i>`;
        return `
            <article class="media-card">
                <div class="media-card-thumb">${thumb}</div>
                <div class="media-card-body">
                    <h4 class="media-card-name" title="${name}">${name}</h4>
                    <p class="media-card-meta">${formatMediaSize(m.size)} · ${path ? `/static/${path}` : '—'}</p>
                    <div class="media-card-actions">
                        ${url ? `<a class="btn btn-ghost btn-sm" href="${url}" target="_blank" rel="noopener">Ouvrir</a>` : ''}
                        <button type="button" class="btn btn-ghost btn-sm btn-danger-ghost" onclick="deleteMedia(${m.id})">Corbeille</button>
                    </div>
                </div>
            </article>
        `;
    };
    const renderList = (m) => {
        const name = m.original_name || m.filename || 'fichier';
        const path = m.path || '';
        const url = path ? `/static/${path}` : '';
        return `
            <div class="admin-card">
                <div class="admin-card-row">
                    <div class="admin-card-main admin-card-main--media">
                        ${isMediaImage(name) && url
                            ? `<img class="admin-list-thumb" src="${url}" alt="" loading="lazy">`
                            : '<div class="admin-list-thumb admin-list-thumb--empty"><i class="fas fa-file-alt"></i></div>'}
                        <div>
                            <h3>${name}</h3>
                            <div class="admin-card-meta">
                                <span>${formatMediaSize(m.size)}</span>
                                <span>${path ? `/static/${path}` : '—'}</span>
                            </div>
                        </div>
                    </div>
                    <div class="admin-card-actions">
                        ${url ? `<a class="btn btn-ghost btn-sm" href="${url}" target="_blank" rel="noopener">Ouvrir</a>` : ''}
                        <button type="button" class="btn btn-ghost btn-sm btn-danger-ghost" onclick="deleteMedia(${m.id})">Corbeille</button>
                    </div>
                </div>
            </div>
        `;
    };
    setAdminListItems('media', items || [], {
        listId: 'media-list',
        paginationId: 'media-pagination',
        countId: 'media-count-label',
        listBtnId: 'media-view-list',
        gridBtnId: 'media-view-grid',
        defaultView: 'grid',
        listClass: 'admin-list',
        gridClass: 'media-grid',
        emptyHtml: `
            <div class="media-empty">
                <span class="media-empty-icon" aria-hidden="true"><i class="fas fa-images"></i></span>
                <p class="media-empty-title">Aucun fichier</p>
                <p class="media-empty-hint">Téléversez une image ou un PDF pour commencer.</p>
            </div>
        `,
        countLabel: (n) => (n === 1 ? '1 fichier' : `${n} fichiers`),
        perPage: 12,
        renderList,
        renderGrid,
    });
}

async function uploadMedia(event) {
    event.preventDefault();
    const file = document.getElementById('media-file').files[0];
    if (!file) return false;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('alt_text', document.getElementById('media-alt').value || '');
    const res = await fetch('/api/media', { method: 'POST', credentials: 'include', body: fd });
    const data = await res.json().catch(() => ({}));
    showToast(res.ok ? 'Fichier téléversé' : (data.error || 'Erreur upload'), res.ok ? 'success' : 'error');
    if (res.ok) {
        document.getElementById('media-upload-form').reset();
        resetMediaDropzone();
        loadMediaAdmin();
    }
    return false;
}

async function deleteMedia(id) {
    const ok = await adminConfirm({
        title: 'Supprimer ce fichier ?',
        message: 'Le fichier sera placé dans la corbeille.',
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!ok) return;
    const res = await fetch(`/api/media/${id}`, { method: 'DELETE', credentials: 'include' });
    if (res.ok) loadMediaAdmin();
}

async function loadTrashAdmin() {
    const list = document.getElementById('trash-list');
    if (!list) return;
    const res = await fetch('/api/trash', { credentials: 'include' });
    if (!res.ok) return;
    const items = await res.json();
    const actions = (item) => `
        <button type="button" class="btn btn-sm btn-ghost" onclick="restoreTrash('${item.entity}', ${item.id})"><i class="fas fa-undo"></i> Restaurer</button>
        <button type="button" class="btn btn-sm btn-ghost btn-danger-ghost" onclick="purgeTrash('${item.entity}', ${item.id})"><i class="fas fa-times"></i> Purger</button>
    `;
    const renderList = (item) => `
        <div class="admin-card">
            <div class="admin-card-row">
                <div class="admin-card-main">
                    <h3>${item.entity} — ${item.label}</h3>
                    <div class="admin-card-meta"><span>${item.deleted_at || ''}</span></div>
                </div>
                <div class="admin-card-actions">${actions(item)}</div>
            </div>
        </div>
    `;
    const renderGrid = (item) => {
        const initial = (item.entity || 'T').trim().charAt(0).toUpperCase();
        return `
            <article class="admin-grid-card">
                <div class="admin-grid-card-icon">${initial}</div>
                <h3 class="admin-grid-card-title">${item.label || item.entity}</h3>
                <p class="admin-grid-card-text">${item.entity}</p>
                <div class="admin-card-meta"><span>${item.deleted_at || ''}</span></div>
                <div class="admin-card-actions">${actions(item)}</div>
            </article>
        `;
    };
    setAdminListItems('trash', items || [], {
        listId: 'trash-list',
        paginationId: 'trash-pagination',
        countId: 'trash-count-label',
        listBtnId: 'trash-view-list',
        gridBtnId: 'trash-view-grid',
        emptyHtml: '<p class="admin-empty">Corbeille vide.</p>',
        countLabel: (n) => (n === 1 ? '1 élément' : `${n} éléments`),
        renderList,
        renderGrid,
    });
}

async function restoreTrash(entity, id) {
    const res = await fetch('/api/trash/restore', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity, id }),
    });
    if (res.ok) loadTrashAdmin();
}

async function purgeTrash(entity, id) {
    const ok = await adminConfirm({
        title: 'Suppression définitive ?',
        message: 'Cette action est irréversible. L’élément sera effacé définitivement.',
        confirmLabel: 'Purger',
        danger: true,
        icon: 'fa-skull-crossbones',
    });
    if (!ok) return;
    const res = await fetch('/api/trash/purge', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity, id }),
    });
    if (res.ok) {
        showToast('Élément purgé', 'success');
        loadTrashAdmin();
    } else {
        showToast('Erreur lors de la purge', 'error');
    }
}

async function loadAuditAdmin() {
    const list = document.getElementById('audit-list');
    if (!list) return;
    const res = await fetch('/api/audit', { credentials: 'include' });
    if (!res.ok) return;
    const items = await res.json();
    list.innerHTML = (items || []).map((a) => `
        <div class="admin-card">
            <strong>${a.action}</strong> · ${a.entity || ''} #${a.entity_id || ''}
            <p style="color:var(--gray);margin:0.35rem 0;">admin ${a.admin_id || ''} · ${a.created_at || ''}</p>
        </div>
    `).join('') || '<p style="color:var(--gray)">Aucun événement.</p>';
}

async function load2FAStatus() {
    const el = document.getElementById('2fa-status');
    if (!el) return;
    const res = await fetch('/api/admin/2fa/status', { credentials: 'include' });
    if (!res.ok) return;
    const data = await res.json();
    if (!data.available) {
        el.textContent = 'pyotp non disponible sur le serveur.';
        return;
    }
    el.textContent = data.enabled ? '2FA activée sur ce compte.' : '2FA désactivée.';
}

async function setup2FA() {
    const res = await fetch('/api/admin/2fa/setup', { method: 'POST', credentials: 'include' });
    const data = await res.json();
    if (!res.ok) {
        showToast(data.error || 'Erreur 2FA', 'error');
        return;
    }
    document.getElementById('2fa-setup-box').style.display = 'block';
    document.getElementById('2fa-secret').textContent = data.secret || '';
    document.getElementById('2fa-uri').textContent = data.otpauth_url || '';
}

async function enable2FA() {
    const code = document.getElementById('2fa-enable-code').value;
    const res = await fetch('/api/admin/2fa/enable', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
    });
    const data = await res.json();
    if (!res.ok) {
        showToast(data.error || 'Code invalide', 'error');
        return;
    }
    document.getElementById('2fa-backup-box').style.display = 'block';
    document.getElementById('2fa-backup-codes').textContent = (data.backup_codes || []).join('\n');
    document.getElementById('2fa-setup-box').style.display = 'none';
    load2FAStatus();
    showToast('2FA activée', 'success');
}

async function disable2FA() {
    const code = prompt('Code TOTP pour désactiver la 2FA');
    if (!code) return;
    const res = await fetch('/api/admin/2fa/disable', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
    });
    const data = await res.json();
    showToast(res.ok ? '2FA désactivée' : (data.error || 'Erreur'), res.ok ? 'success' : 'error');
    if (res.ok) load2FAStatus();
}

// Chargement des sections avancées délégué à showSection() (admin-data.js)
// pour n'afficher / charger que la section active de la route.

function loadTopProjects(projects) {
    const topProjectsList = document.getElementById('top-projects-list');
    if (!topProjectsList) return;
    
    if (!projects || projects.length === 0) {
        topProjectsList.innerHTML = '<p class="dashboard-empty">Aucun projet avec des vues pour le moment.</p>';
        return;
    }
    
    topProjectsList.innerHTML = '';
    
    projects.forEach((project, index) => {
        const card = document.createElement('div');
        card.className = 'admin-card dashboard-list-item dashboard-list-row';
        
        card.innerHTML = `
            <div class="dashboard-list-row-main">
                <span class="dashboard-rank">${index + 1}</span>
                <div>
                    <strong>${project.title || 'Projet sans titre'}</strong>
                    <p class="dashboard-meta" style="margin: 0.25rem 0 0 0;">${project.views || 0} vue${(project.views || 0) > 1 ? 's' : ''}</p>
                </div>
            </div>
        `;
        
        topProjectsList.appendChild(card);
    });
}

function loadCharts(stats) {
    // Graphique des vues par jour
    const viewsChart = document.getElementById('views-chart');
    if (viewsChart && stats.views_by_day && stats.views_by_day.length > 0) {
        renderSimpleChart(viewsChart, stats.views_by_day, 'views', 'Vues par jour');
    }
    
    // Graphique des visiteurs par jour
    const visitorsChart = document.getElementById('visitors-chart');
    if (visitorsChart && stats.visitors_by_day && stats.visitors_by_day.length > 0) {
        renderSimpleChart(visitorsChart, stats.visitors_by_day, 'visitors', 'Visiteurs par jour');
    }
}

function renderSimpleChart(container, data, key, title) {
    if (!data || data.length === 0) {
        container.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucune donnée disponible</p>';
        return;
    }
    
    const maxValue = Math.max(...data.map(d => d[key] || 0), 1);
    const chartHeight = 200;
    
    let chartHTML = `<div style="margin-bottom: 1rem;"><strong>${title}</strong></div>`;
    chartHTML += `<div style="display: flex; align-items: flex-end; gap: 2px; height: ${chartHeight}px; padding: 1rem 0;">`;
    
    data.forEach((item, index) => {
        const value = item[key] || 0;
        const height = (value / maxValue) * chartHeight;
        const date = new Date(item.date);
        const dayLabel = date.getDate();
        
        chartHTML += `
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; position: relative;">
                <div style="
                    width: 100%;
                    background: linear-gradient(to top, var(--green, #4DBA87), rgba(77, 186, 135, 0.5));
                    height: ${height}px;
                    border-radius: 4px 4px 0 0;
                    transition: all 0.3s ease;
                    cursor: pointer;
                " 
                title="${dayLabel}/${date.getMonth() + 1}: ${value} ${key === 'views' ? 'vues' : 'visiteurs'}"
                onmouseover="this.style.opacity='0.8'"
                onmouseout="this.style.opacity='1'">
                </div>
                <span style="font-size: 0.7rem; color: var(--gray); margin-top: 0.5rem; writing-mode: vertical-rl; text-orientation: mixed;">${dayLabel}</span>
            </div>
        `;
    });
    
    chartHTML += '</div>';
    container.innerHTML = chartHTML;
}

// ============================================
// Toast Notifications
// ============================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.log(`[${(type || 'info').toUpperCase()}] ${message}`);
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode === container) {
                container.removeChild(toast);
            }
        }, 300);
    }, 3000);
}
window.showToast = showToast;

// ============================================
// Confirmation dialog (remplace window.confirm)
// ============================================
let adminConfirmResolver = null;

function closeAdminConfirm(result) {
    const modal = document.getElementById('adminConfirmModal');
    if (!modal) {
        if (adminConfirmResolver) {
            adminConfirmResolver(Boolean(result));
            adminConfirmResolver = null;
        }
        return;
    }
    if (typeof closeModalEl === 'function') {
        closeModalEl(modal);
    } else {
        modal.classList.remove('open');
        modal.style.display = 'none';
    }
    if (adminConfirmResolver) {
        adminConfirmResolver(Boolean(result));
        adminConfirmResolver = null;
    }
}

function initAdminConfirmModal() {
    const modal = document.getElementById('adminConfirmModal');
    if (!modal || modal.dataset.bound) return;
    modal.dataset.bound = '1';
    const cancelBtn = document.getElementById('admin-confirm-cancel');
    const okBtn = document.getElementById('admin-confirm-ok');
    if (cancelBtn) cancelBtn.addEventListener('click', () => closeAdminConfirm(false));
    if (okBtn) okBtn.addEventListener('click', () => closeAdminConfirm(true));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeAdminConfirm(false);
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('open')) {
            closeAdminConfirm(false);
        }
    });
}

/**
 * @param {string|{title?:string,message?:string,confirmLabel?:string,cancelLabel?:string,danger?:boolean,icon?:string}} options
 * @returns {Promise<boolean>}
 */
function adminConfirm(options) {
    initAdminConfirmModal();
    const opts = typeof options === 'string' ? { message: options } : (options || {});
    const title = opts.title || 'Confirmer';
    const message = opts.message || 'Voulez-vous continuer ?';
    const confirmLabel = opts.confirmLabel || 'Confirmer';
    const cancelLabel = opts.cancelLabel || 'Annuler';
    const danger = opts.danger !== false;
    const icon = opts.icon || (danger ? 'fa-exclamation-triangle' : 'fa-question-circle');

    const modal = document.getElementById('adminConfirmModal');
    const titleEl = document.getElementById('admin-confirm-title');
    const messageEl = document.getElementById('admin-confirm-message');
    const okBtn = document.getElementById('admin-confirm-ok');
    const cancelBtn = document.getElementById('admin-confirm-cancel');
    const iconWrap = document.getElementById('admin-confirm-icon');

    if (!modal) {
        return Promise.resolve(window.confirm([title, message].filter(Boolean).join('\n\n')));
    }

    if (titleEl) titleEl.textContent = title;
    if (messageEl) messageEl.textContent = message;
    if (okBtn) {
        okBtn.textContent = confirmLabel;
        okBtn.classList.toggle('btn-danger', danger);
    }
    if (cancelBtn) cancelBtn.textContent = cancelLabel;
    if (iconWrap) {
        iconWrap.innerHTML = `<i class="fas ${icon}"></i>`;
    }
    modal.classList.toggle('is-danger', danger);

    return new Promise((resolve) => {
        adminConfirmResolver = resolve;
        if (typeof openModalEl === 'function') {
            openModalEl(modal);
        } else {
            modal.style.display = 'flex';
            requestAnimationFrame(() => modal.classList.add('open'));
        }
        window.setTimeout(() => okBtn && okBtn.focus(), 60);
    });
}
window.adminConfirm = adminConfirm;

// ============================================
// Loading Overlay
// ============================================
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Exposer les handlers onclick de l'admin (career, certs, media, trash, audit, 2FA, UI)
Object.assign(window, {
    openSupportModal,
    closeSupportModal,
    toggleRightPanel,
    loadPanelStats,
    loadDashboardStats,
    adminConfirm,
    loadCareerAdmin,
    openCareerModal,
    editCareer,
    closeCareerModal,
    deleteCareer,
    loadCertsAdmin,
    openCertModal,
    closeCertModal,
    setCertsView,
    goToCertsPage,
    viewCert,
    closeCertViewModal,
    editCert,
    deleteCert,
    archiveCert,
    loadLegalPage,
    saveLegalPage,
    selectLegalPage,
    updateLegalPreview,
    loadMediaAdmin,
    uploadMedia,
    deleteMedia,
    loadTrashAdmin,
    restoreTrash,
    purgeTrash,
    loadAuditAdmin,
    load2FAStatus,
    setup2FA,
    enable2FA,
    disable2FA,
    showLoading,
    hideLoading,
    initAdminGlobalSearch,
    filterActiveAdminSection,
});

