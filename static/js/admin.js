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
    
    // Support modal
    const supportBtn = document.getElementById('supportBtn');
    if (supportBtn) {
        supportBtn.addEventListener('click', function() {
            openSupportModal();
        });
    }
    
    // Navigation menu items - La navigation est gérée par admin-data.js
    // On garde juste la gestion des liens externes (sans data-section)
    const menuItems = document.querySelectorAll('.menu-item:not([data-section])');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Pour les liens externes, on ne fait rien de spécial
            // La navigation interne est gérée par admin-data.js
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
});

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
        toggleButton.classList.remove('show');
        if (mainContent) {
            mainContent.style.marginRight = '360px';
        }
    } else {
        rightPanel.classList.add('hidden');
        toggleButton.classList.add('show');
        if (mainContent) {
            mainContent.style.marginRight = '0';
        }
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
                activeProjects.textContent = stats.total_projects || 0;
            }
            
            const panelServices = document.getElementById('panel-services');
            if (panelServices) {
                panelServices.textContent = stats.total_services || 0;
            }
            
            const panelContacts = document.getElementById('panel-contacts');
            if (panelContacts) {
                panelContacts.textContent = stats.total_contacts || 0;
            }
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
    } catch (error) {
        console.debug('Erreur lors du chargement des stats du dashboard:', error);
    }
}

function loadTopProjects(projects) {
    const topProjectsList = document.getElementById('top-projects-list');
    if (!topProjectsList) return;
    
    if (!projects || projects.length === 0) {
        topProjectsList.innerHTML = '<p style="color: var(--gray);">Aucun projet avec des vues pour le moment.</p>';
        return;
    }
    
    topProjectsList.innerHTML = '';
    
    projects.forEach((project, index) => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        card.style.display = 'flex';
        card.style.justifyContent = 'space-between';
        card.style.alignItems = 'center';
        card.style.marginBottom = '0.5rem';
        
        card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="
                    background: var(--green, #4DBA87);
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 0.9rem;
                ">${index + 1}</span>
                <div>
                    <strong>${project.title || 'Projet sans titre'}</strong>
                    <p style="color: var(--gray); font-size: 0.85rem; margin: 0.25rem 0 0 0;">${project.views || 0} vue${(project.views || 0) > 1 ? 's' : ''}</p>
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
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, 3000);
}

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

