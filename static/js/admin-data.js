// ============================================
// Admin Data Management JavaScript
// ============================================

const API_BASE = '/api';

// Headers pour les requêtes API
const getHeaders = () => {
    return {
        'Content-Type': 'application/json'
    };
};

// ========== Navigation entre sections ==========
// Définir showSection globalement pour qu'elle soit accessible partout
function showSection(sectionName) {
    if (!sectionName) {
        console.error('showSection appelée sans nom de section');
        return;
    }
    
    // Masquer toutes les sections
    const allSections = document.querySelectorAll('.content-section');
    if (allSections.length === 0) {
        console.warn('Aucune section avec la classe content-section trouvée');
        return;
    }
    
    allSections.forEach(section => {
        section.style.display = 'none';
        section.classList.remove('active-section');
    });

    // Afficher la section demandée
    const targetSection = document.getElementById(`section-${sectionName}`);
    if (!targetSection) {
        console.error(`Section non trouvée: section-${sectionName}`);
        return;
    }
    
    targetSection.style.display = 'block';
    targetSection.classList.add('active-section');
    
    // Mettre à jour le titre de la page
    const pageTitleEl = document.getElementById('current-page');
    if (pageTitleEl) {
        const menuItem = document.querySelector(`[data-section="${sectionName}"]`);
        const pageTitle = menuItem ? menuItem.getAttribute('aria-label') || sectionName : sectionName;
        pageTitleEl.textContent = pageTitle;
    }
    
    // Charger les données si nécessaire
    if (sectionName === 'projects') {
        if (typeof initProjectsSection === 'function') {
            initProjectsSection();
        }
    } else if (sectionName === 'services') {
        if (typeof initServicesSection === 'function') {
            initServicesSection();
        }
    } else if (sectionName === 'contacts') {
        if (typeof loadContacts === 'function') {
            loadContacts();
        }
    } else if (sectionName === 'profile') {
        if (typeof loadProfile === 'function') {
            loadProfile();
        }
        if (typeof loadLoginHistory === 'function') {
            loadLoginHistory();
        }
    } else if (sectionName === 'skills') {
        if (typeof initSkillsSection === 'function') {
            initSkillsSection();
        }
    } else if (sectionName === 'partners') {
        if (typeof initPartnersSection === 'function') {
            initPartnersSection();
        }
    } else if (sectionName === 'dashboard') {
        if (typeof loadDashboardStats === 'function') {
            loadDashboardStats();
        }
    } else if (sectionName === 'admins') {
        if (typeof loadAdminUsers === 'function') {
            loadAdminUsers();
        }
    } else if (sectionName === 'homepage') {
        if (typeof loadHomepageData === 'function') {
            loadHomepageData();
        }
    }
}

// Initialiser la navigation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier que les éléments nécessaires existent
    const menuItems = document.querySelectorAll('.menu-item[data-section]');
    
    if (menuItems.length === 0) {
        console.warn('Aucun élément de menu avec data-section trouvé');
        return;
    }
    
    console.log(`✅ ${menuItems.length} éléments de menu trouvés`);
    
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                e.stopPropagation();
                
                const section = this.getAttribute('data-section');
                if (section) {
                    console.log(`🔄 Navigation vers la section: ${section}`);
                    showSection(section);
                    
                    // Mettre à jour l'état actif
                    menuItems.forEach(mi => mi.classList.remove('active'));
                    this.classList.add('active');
                } else {
                    console.error('Section non trouvée:', section);
                }
            }
        });
    });
    
    // Afficher la section dashboard par défaut si aucune section n'est active
    const activeSection = document.querySelector('.content-section.active-section');
    if (!activeSection) {
        console.log('Aucune section active, affichage du dashboard par défaut');
        showSection('dashboard');
    }
    
    // Vérifier l'état MongoDB au démarrage
    checkMongoDBStatusOnLoad();
    
    // Charger les données au démarrage
    console.log('🔄 Chargement initial des données...');
    loadHomepageData();
    loadSkills();
    loadPartners();
    loadProjects();
    loadServices();
    loadContacts();
});

// Vérifier l'état MongoDB au chargement
async function checkMongoDBStatusOnLoad() {
    // Attendre un peu pour que les requêtes se lancent
    setTimeout(async () => {
        try {
            // Tester une API pour voir si MongoDB est disponible
            const response = await fetch(`${API_BASE}/skills`);
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                if (data.error === 'MongoDB non disponible' || response.status === 503) {
                    showMongoDBWarningBanner();
                }
            }
        } catch (error) {
            // Ignorer les erreurs silencieusement
        }
    }, 2000);
}

function showMongoDBWarningBanner() {
    // Vérifier si le bandeau existe déjà
    if (document.getElementById('mongodb-config-warning')) {
        return;
    }
    
    const banner = document.createElement('div');
    banner.id = 'mongodb-config-warning';
    banner.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 1.5rem 2rem;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        font-family: 'Roboto Mono', monospace;
    `;
    
    banner.innerHTML = `
        <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 2rem;">
            <div style="flex: 1;">
                <strong style="font-size: 1.1rem; display: block; margin-bottom: 0.5rem;">⚠️ MongoDB non configuré</strong>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.95;">
                    La variable <code style="background: rgba(255,255,255,0.2); padding: 0.2rem 0.4rem; border-radius: 3px;">MONGO_URI</code> n'est pas définie en production.
                    Les données ne peuvent pas être chargées. 
                    <a href="#" onclick="window.open('https://help.pythonanywhere.com/pages/environment-variables-for-web-apps/', '_blank'); return false;" 
                       style="color: white; text-decoration: underline; font-weight: bold;">
                       Consultez le guide de configuration
                    </a>
                </p>
            </div>
            <button onclick="document.getElementById('mongodb-config-warning').remove(); document.querySelector('.main-content').style.paddingTop = '0';" 
                    style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); 
                           color: white; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; 
                           font-size: 0.9rem; white-space: nowrap;">
                ✕ Fermer
            </button>
        </div>
    `;
    
    document.body.insertBefore(banner, document.body.firstChild);
    
    // Ajuster le padding du contenu principal
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.style.paddingTop = '100px';
    }
}

// ========== Fonctions utilitaires ==========
// Ne pas redéfinir showToast - utiliser celle de admin.js
// Si showToast n'existe pas encore, créer une version simple
if (typeof window.showToast !== 'function') {
    window.showToast = function(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) {
            console.log(`[${type.toUpperCase()}] ${message}`);
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
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    };
}

// Fonction pour gérer les erreurs 401 (session expirée)
async function handle401Error() {
    if (typeof window.showToast === 'function') {
        window.showToast('Session expirée. Veuillez vous reconnecter.', 'error');
    } else {
        console.error('Session expirée. Veuillez vous reconnecter.');
    }
    setTimeout(() => {
        window.location.href = '/admin/login';
    }, 2000);
    return false;
}

// ========== Homepage Management ==========
async function loadHomepageData() {
    try {
        const response = await fetch(`${API_BASE}/homepage`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data && !data.error && Object.keys(data).length > 0) {
            const badgeEl = document.getElementById('homepage-badge');
            const title1El = document.getElementById('homepage-title1');
            const title2El = document.getElementById('homepage-title2');
            const descEl = document.getElementById('homepage-description');
            const emailEl = document.getElementById('homepage-email');
            const ctaEl = document.getElementById('homepage-cta');
            const aboutTitleEl = document.getElementById('homepage-about-title');
            const aboutNameEl = document.getElementById('homepage-about-name');
            const aboutSubtitleEl = document.getElementById('homepage-about-subtitle');
            const aboutDescEl = document.getElementById('homepage-about-description');
            
            if (badgeEl) badgeEl.value = data.badge || '';
            if (title1El) title1El.value = data.title_line1 || '';
            if (title2El) title2El.value = data.title_line2 || '';
            if (descEl) descEl.value = data.description || '';
            if (emailEl) emailEl.value = data.email || '';
            if (ctaEl) ctaEl.value = data.cta_text || '';
            if (aboutTitleEl) aboutTitleEl.value = data.about_title || '';
            if (aboutNameEl) aboutNameEl.value = data.about_name || '';
            if (aboutSubtitleEl) aboutSubtitleEl.value = data.about_subtitle || '';
            if (aboutDescEl) aboutDescEl.value = data.about_description || '';
        }
    } catch (error) {
        console.error('Erreur lors du chargement des données homepage:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Erreur lors du chargement des données. MongoDB est peut-être indisponible.', 'error');
        } else {
            console.error('Erreur lors du chargement des données homepage');
        }
    }
}

// Attacher l'événement submit au formulaire homepage
document.addEventListener('DOMContentLoaded', function() {
    const homepageForm = document.getElementById('homepage-form');
    if (homepageForm) {
        homepageForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                badge: document.getElementById('homepage-badge').value,
                title_line1: document.getElementById('homepage-title1').value,
                title_line2: document.getElementById('homepage-title2').value,
                description: document.getElementById('homepage-description').value,
                email: document.getElementById('homepage-email').value,
                cta_text: document.getElementById('homepage-cta').value,
                about_title: document.getElementById('homepage-about-title').value,
                about_name: document.getElementById('homepage-about-name').value,
                about_subtitle: document.getElementById('homepage-about-subtitle').value,
                about_description: document.getElementById('homepage-about-description').value,
                type: 'header'
            };

            try {
                const response = await fetch(`${API_BASE}/homepage`, {
                    method: 'PUT',
                    headers: getHeaders(),
                    body: JSON.stringify(formData)
                });

                if (!response.ok) {
                    const result = await response.json();
                    if (response.status === 401) {
                        await handle401Error();
                        return;
                    }
                    if (typeof window.showToast === 'function') {
                        window.showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
                    }
                    return;
                }
                
                const result = await response.json();
                if (result.success) {
                    if (typeof window.showToast === 'function') {
                        window.showToast('Données enregistrées avec succès !', 'success');
                    }
                } else {
                    if (typeof window.showToast === 'function') {
                        window.showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
                    }
                }
            } catch (error) {
                console.error('Erreur:', error);
                    if (typeof window.showToast === 'function') {
                        window.showToast('Erreur lors de l\'enregistrement', 'error');
                    }
            }
        });
    }
});

// ========== Skills Management ==========
let allSkillsData = [];

async function loadSkills() {
    try {
        console.log('🔄 Chargement des compétences...');
        const response = await fetch(`${API_BASE}/skills`);
        
        // Vérifier le statut de la réponse avant de parser le JSON
        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                // Si le JSON ne peut pas être parsé, utiliser un message par défaut
                errorData = { error: 'Erreur serveur', message: `Erreur HTTP ${response.status}` };
            }
            
            const skillsList = document.getElementById('skills-list');
            if (skillsList) {
                skillsList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${errorData.message || 'La connexion à MongoDB n\'est pas configurée. Vérifiez la variable MONGO_URI.'}</p>
                    </div>
                `;
            }
            console.error('❌ Erreur lors du chargement des compétences:', errorData.message || errorData.error);
            return;
        }
        
        const data = await response.json();
        
        // Vérifier si c'est une erreur MongoDB dans les données
        if (data.error && data.error === 'MongoDB non disponible') {
            const skillsList = document.getElementById('skills-list');
            if (skillsList) {
                skillsList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à MongoDB n\'est pas configurée. Vérifiez la variable MONGO_URI.'}</p>
                    </div>
                `;
            }
            console.error('❌ MongoDB non disponible pour les compétences');
            return;
        }
        
        const skills = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${skills.length} compétence(s) chargée(s)`);
        
        allSkillsData = skills;
        displaySkills(skills);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des compétences:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Erreur lors du chargement des compétences', 'error');
        } else {
            console.error('Erreur lors du chargement des compétences');
        }
        const skillsList = document.getElementById('skills-list');
        if (skillsList) {
            skillsList.innerHTML = '<p>Aucune compétence disponible.</p>';
        }
    }
}

function displaySkills(skills) {
    const skillsList = document.getElementById('skills-list');
    if (!skillsList) return;
    
    if (skills.length === 0) {
        skillsList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucune compétence disponible.</p>';
        return;
    }
    
    skillsList.innerHTML = '';
    skills.forEach(skill => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3>${skill.title || 'Sans titre'}</h3>
                    <p>${skill.description || ''}</p>
                    <p style="color: var(--gray); font-size: 0.9rem; margin-top: 0.5rem;">
                        <strong>Projets:</strong> ${skill.projects_count || 0} | 
                        <strong>Ordre:</strong> ${skill.order || 0}
                    </p>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn btn-sm btn-primary" onclick="editSkill('${skill._id}')">Modifier</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSkill('${skill._id}')">Supprimer</button>
                </div>
            </div>
        `;
        skillsList.appendChild(card);
    });
}

function initSkillsSection() {
    loadSkills();
}

function editSkill(skillId) {
    console.log('Modifier compétence:', skillId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

function deleteSkill(skillId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette compétence ?')) {
        return;
    }
    console.log('Supprimer compétence:', skillId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

// ========== Partners Management ==========
let allPartnersData = [];

async function loadPartners() {
    try {
        console.log('🔄 Chargement des partenaires...');
        const response = await fetch(`${API_BASE}/partners`);
        
        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: 'Erreur serveur', message: `Erreur HTTP ${response.status}` };
            }
            
            const partnersList = document.getElementById('partners-list');
            if (partnersList) {
                partnersList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            console.error('❌ Erreur lors du chargement des partenaires:', errorData.message || errorData.error);
            return;
        }
        
        const data = await response.json();
        
        if (data.error && data.error === 'MongoDB non disponible') {
            const partnersList = document.getElementById('partners-list');
            if (partnersList) {
                partnersList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            if (typeof window.showToast === 'function') {
                window.showToast('Impossible de charger les partenaires : MongoDB non disponible', 'error');
            } else {
                console.error('MongoDB non disponible pour les partenaires');
            }
            return;
        }
        
        const partners = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${partners.length} partenaire(s) chargé(s)`);
        
        allPartnersData = partners;
        displayPartners(partners);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des partenaires:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Erreur lors du chargement des partenaires', 'error');
        } else {
            console.error('Erreur lors du chargement des partenaires');
        }
        const partnersList = document.getElementById('partners-list');
        if (partnersList) {
            partnersList.innerHTML = '<p>Aucun partenaire disponible.</p>';
        }
    }
}

function displayPartners(partners) {
    const partnersList = document.getElementById('partners-list');
    if (!partnersList) return;
    
    if (partners.length === 0) {
        partnersList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun partenaire disponible.</p>';
        return;
    }
    
    partnersList.innerHTML = '';
    partners.forEach(partner => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    ${partner.image ? `<img src="/static/${partner.image}" alt="${partner.name}" style="width: 60px; height: auto;">` : ''}
                    <div>
                        <h3>${partner.name || 'Sans nom'}</h3>
                        <p style="color: var(--gray); font-size: 0.9rem;"><strong>Ordre:</strong> ${partner.order || 0}</p>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn btn-sm btn-primary" onclick="editPartner('${partner._id}')">Modifier</button>
                    <button class="btn btn-sm btn-danger" onclick="deletePartner('${partner._id}')">Supprimer</button>
                </div>
            </div>
        `;
        partnersList.appendChild(card);
    });
}

function initPartnersSection() {
    loadPartners();
}

function editPartner(partnerId) {
    console.log('Modifier partenaire:', partnerId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

function deletePartner(partnerId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce partenaire ?')) {
        return;
    }
    console.log('Supprimer partenaire:', partnerId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

// ========== Projects Management ==========
let allProjectsData = [];

async function loadProjects() {
    try {
        console.log('🔄 Chargement des projets...');
        const response = await fetch(`${API_BASE}/projects`);
        
        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: 'Erreur serveur', message: `Erreur HTTP ${response.status}` };
            }
            
            const projectsList = document.getElementById('projects-list');
            if (projectsList) {
                projectsList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            console.error('❌ Erreur lors du chargement des projets:', errorData.message || errorData.error);
            return;
        }
        
        const data = await response.json();
        
        if (data.error && data.error === 'MongoDB non disponible') {
            const projectsList = document.getElementById('projects-list');
            if (projectsList) {
                projectsList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            if (typeof window.showToast === 'function') {
                window.showToast('Impossible de charger les projets : MongoDB non disponible', 'error');
            } else {
                console.error('MongoDB non disponible pour les projets');
            }
            return;
        }
        
        const projects = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${projects.length} projet(s) chargé(s)`);
        
        allProjectsData = projects;
        displayProjects(projects);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des projets:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Erreur lors du chargement des projets', 'error');
        } else {
            console.error('Erreur lors du chargement des projets');
        }
        const projectsList = document.getElementById('projects-list');
        if (projectsList) {
            projectsList.innerHTML = '<p>Aucun projet disponible.</p>';
        }
    }
}

function displayProjects(projects) {
    const projectsList = document.getElementById('projects-list');
    if (!projectsList) return;
    
    if (projects.length === 0) {
        projectsList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun projet disponible.</p>';
        return;
    }
    
    projectsList.innerHTML = '';
    projects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        const statusBadge = project.status === 'published' ? '<span style="color: var(--green);">● Publié</span>' : 
                           project.status === 'draft' ? '<span style="color: orange;">● Brouillon</span>' : 
                           '<span style="color: gray;">● Archivé</span>';
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <h3>${project.title || 'Sans titre'}</h3>
                    <p style="color: var(--gray); margin: 0.5rem 0;"><strong>Technologies:</strong> ${project.technologies || 'N/A'}</p>
                    <p style="color: var(--gray); margin: 0.5rem 0;">${project.description ? (project.description.substring(0, 100) + '...') : ''}</p>
                    <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.9rem;">
                        ${statusBadge}
                        ${project.featured ? '<span style="color: gold;">⭐ En vedette</span>' : ''}
                        <span><strong>Ordre:</strong> ${project.order || 0}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; margin-left: 1rem;">
                    <button class="btn btn-sm btn-primary" onclick="editProject('${project._id}')">Modifier</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProject('${project._id}')">Supprimer</button>
                </div>
            </div>
        `;
        projectsList.appendChild(card);
    });
}

function initProjectsSection() {
    loadProjects();
}

function editProject(projectId) {
    console.log('Modifier projet:', projectId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

function deleteProject(projectId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce projet ?')) {
        return;
    }
    console.log('Supprimer projet:', projectId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

// ========== Services Management ==========
let allServicesData = [];

async function loadServices() {
    try {
        console.log('🔄 Chargement des services...');
        const response = await fetch(`${API_BASE}/services`);
        
        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: 'Erreur serveur', message: `Erreur HTTP ${response.status}` };
            }
            
            const servicesList = document.getElementById('services-list');
            if (servicesList) {
                servicesList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            console.error('❌ Erreur lors du chargement des services:', errorData.message || errorData.error);
            return;
        }
        
        const data = await response.json();
        
        if (data.error && data.error === 'MongoDB non disponible') {
            const servicesList = document.getElementById('services-list');
            if (servicesList) {
                servicesList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            if (typeof window.showToast === 'function') {
                window.showToast('Impossible de charger les services : MongoDB non disponible', 'error');
            } else {
                console.error('MongoDB non disponible pour les services');
            }
            return;
        }
        
        const services = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${services.length} service(s) chargé(s)`);
        
        allServicesData = services;
        displayServices(services);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des services:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Erreur lors du chargement des services', 'error');
        } else {
            console.error('Erreur lors du chargement des services');
        }
        const servicesList = document.getElementById('services-list');
        if (servicesList) {
            servicesList.innerHTML = '<p>Aucun service disponible.</p>';
        }
    }
}

function displayServices(services) {
    const servicesList = document.getElementById('services-list');
    if (!servicesList) return;
    
    if (services.length === 0) {
        servicesList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun service disponible.</p>';
        return;
    }
    
    servicesList.innerHTML = '';
    services.forEach(service => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1; display: flex; align-items: center; gap: 1rem;">
                    ${service.icon ? `<img src="/static/${service.icon}" alt="${service.title}" style="width: 48px; height: 48px;">` : ''}
                    <div>
                        <h3>${service.title || 'Sans titre'}</h3>
                        <p style="color: var(--gray); margin: 0.5rem 0;">${service.description ? (service.description.substring(0, 150) + '...') : ''}</p>
                        <span style="font-size: 0.9rem; color: var(--gray);"><strong>Ordre:</strong> ${service.order || 0}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; margin-left: 1rem;">
                    <button class="btn btn-sm btn-primary" onclick="editService('${service._id}')">Modifier</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteService('${service._id}')">Supprimer</button>
                </div>
            </div>
        `;
        servicesList.appendChild(card);
    });
}

function initServicesSection() {
    loadServices();
}

function editService(serviceId) {
    console.log('Modifier service:', serviceId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

function deleteService(serviceId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce service ?')) {
        return;
    }
    console.log('Supprimer service:', serviceId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

// ========== Contacts Management ==========
let allContacts = [];

async function loadContacts() {
    try {
        console.log('🔄 Chargement des contacts...');
        const response = await fetch(`${API_BASE}/contacts`, {
            headers: getHeaders()
        });
        
        const contactsList = document.getElementById('contacts-list');
        if (!contactsList) return;
        
        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: 'Erreur serveur', message: `Erreur HTTP ${response.status}` };
            }
            
            contactsList.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: var(--gray);">
                    <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                    <p>${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                </div>
            `;
            console.error('❌ Erreur lors du chargement des contacts:', errorData.message || errorData.error);
            return;
        }
        
        const data = await response.json();
        
        if (data.error && data.error === 'MongoDB non disponible') {
            contactsList.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: var(--gray);">
                    <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                    <p>${data.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                </div>
            `;
            if (typeof window.showToast === 'function') {
                window.showToast('Impossible de charger les contacts : MongoDB non disponible', 'error');
            } else {
                console.error('MongoDB non disponible pour les contacts');
            }
            return;
        }
        
        const contacts = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${contacts.length} contact(s) chargé(s)`);
        
        allContacts = contacts;
        displayContacts(contacts);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des contacts:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Erreur lors du chargement des contacts', 'error');
        } else {
            console.error('Erreur lors du chargement des contacts');
        }
        const contactsList = document.getElementById('contacts-list');
        if (contactsList) {
            contactsList.innerHTML = '<p>Aucun message disponible.</p>';
        }
    }
}

function displayContacts(contacts) {
    const contactsList = document.getElementById('contacts-list');
    if (!contactsList) return;
    
    if (contacts.length === 0) {
        contactsList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun message de contact reçu.</p>';
        return;
    }
    
    contactsList.innerHTML = '';
    contacts.forEach(contact => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        const date = new Date(contact.created_at);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        card.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <h3>${contact.subject || 'Sans sujet'}</h3>
                        <div style="color: var(--gray); font-size: 0.9rem; margin: 0.5rem 0;">
                            <p><strong>De:</strong> ${contact.name} (<a href="mailto:${contact.email}">${contact.email}</a>)</p>
                            <p><strong>Date:</strong> ${formattedDate}</p>
                        </div>
                        <div style="background: var(--dark-bg); padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                            <p style="color: var(--white); white-space: pre-wrap;">${contact.message || ''}</p>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <a href="mailto:${contact.email}?subject=Re: ${encodeURIComponent(contact.subject || '')}" class="btn btn-sm btn-primary">Répondre</a>
                    <button class="btn btn-sm btn-danger" onclick="deleteContact('${contact._id}')">Supprimer</button>
                </div>
            </div>
        `;
        contactsList.appendChild(card);
    });
}

function deleteContact(contactId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {
        return;
    }
    console.log('Supprimer contact:', contactId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

// ========== Profile Management ==========
function loadProfile() {
    console.log('Chargement du profil');
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

function loadLoginHistory() {
    console.log('Chargement de l\'historique de connexion');
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

// ========== Admin Users Management ==========
function loadAdminUsers() {
    console.log('Chargement des administrateurs');
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}
