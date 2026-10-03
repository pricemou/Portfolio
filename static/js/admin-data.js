// ============================================
// Admin Data Management JavaScript
// ============================================

const API_BASE = '/api';

// Variable pour stocker l'ID de l'admin connecté
let currentAdminId = null;

// Fonction utilitaire pour échapper le HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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
        if (typeof initProfileSection === 'function') {
            initProfileSection();
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
    } else if (activeSection.id === 'section-dashboard' && typeof loadDashboardStats === 'function') {
        // Stats jamais chargées sinon (dashboard déjà active au premier rendu)
        loadDashboardStats();
    }
    
    // Charger les données au démarrage
    console.log('🔄 Chargement des données initiales...');
    loadHomepageData();
    loadSkills();
    loadPartners();
    loadProjects();
    loadServices();
    loadContacts();
});

// ========== Fonctions utilitaires ==========
// showToast est défini dans admin.js (chargé avant ce fichier).
// Ne pas le redéfinir avec le même nom : sinon window.showToast s'appelle lui-même → stack overflow.
if (typeof window.showToast !== 'function') {
    window.showToast = function (message, type = 'info') {
        console.log(`[${(type || 'info').toUpperCase()}] ${message}`);
    };
}

// Fonction pour gérer les erreurs 401 (session expirée)
async function handle401Error() {
    showToast('Session expirée. Veuillez vous reconnecter.', 'error');
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
            showToast('Erreur lors du chargement des données. La base de données est peut-être indisponible.', 'error');
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
                    showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
            return;
        }
        
            const result = await response.json();
                if (result.success) {
                    showToast('Données enregistrées avec succès !', 'success');
        } else {
                    showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
                showToast('Erreur lors de l\'enregistrement', 'error');
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
        const data = await response.json();
        
        // Vérifier si c'est une erreur de base de données
        if (!response.ok || (data.error && data.error === 'Base de données non disponible')) {
            const skillsList = document.getElementById('skills-list');
            if (skillsList) {
                skillsList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à la base de données n\'est pas disponible.'}</p>
                    </div>
                `;
            }
            showToast('Impossible de charger les compétences : Base de données non disponible', 'error');
            return;
        }
        
        const skills = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${skills.length} compétence(s) chargée(s)`);
        
        allSkillsData = skills;
        displaySkills(skills);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des compétences:', error);
        showToast('Erreur lors du chargement des compétences', 'error');
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
                    <p style="color: var(--gray); font-size: 0.9rem;">
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
    showToast('Fonctionnalité à implémenter', 'info');
}

function deleteSkill(skillId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette compétence ?')) {
        fetch(`${API_BASE}/skills/${skillId}`, {
            method: 'DELETE',
            headers: getHeaders()
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Compétence supprimée', 'success');
                loadSkills();
            } else {
                showToast(data.error || 'Erreur lors de la suppression', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur lors de la suppression', 'error');
        });
    }
}

// ========== Partners Management ==========
let allPartnersData = [];

async function loadPartners() {
    try {
        console.log('🔄 Chargement des partenaires...');
        const response = await fetch(`${API_BASE}/partners`);
        const data = await response.json();
        
        if (!response.ok || (data.error && data.error === 'Base de données non disponible')) {
            const partnersList = document.getElementById('partners-list');
            if (partnersList) {
                partnersList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à la base de données n\'est pas disponible.'}</p>
                    </div>
                `;
            }
            showToast('Impossible de charger les partenaires : Base de données non disponible', 'error');
            return;
        }
        
        const partners = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${partners.length} partenaire(s) chargé(s)`);
        
        allPartnersData = partners;
        displayPartners(partners);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des partenaires:', error);
        showToast('Erreur lors du chargement des partenaires', 'error');
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
    showToast('Fonctionnalité à implémenter', 'info');
}

async function deletePartner(partnerId) {
    if (!partnerId) {
        showToast('ID partenaire invalide', 'error');
        return;
    }
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce partenaire ?')) {
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/partners/${partnerId}`, {
            method: 'DELETE',
            headers: getHeaders(),
            credentials: 'same-origin'
        });
        let data = {};
        try {
            data = await response.json();
        } catch (_) {
            data = {};
        }
        if (response.ok && data.success) {
            showToast('Partenaire supprimé', 'success');
            loadPartners();
            return;
        }
        if (response.status === 401) {
            await handle401Error();
            return;
        }
        if (response.status === 404) {
            showToast(data.error || 'Partenaire introuvable (peut-être déjà supprimé)', 'error');
            loadPartners();
            return;
        }
        showToast(data.error || `Erreur lors de la suppression (${response.status})`, 'error');
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
}

// ========== Projects Management ==========
let allProjectsData = [];

async function loadProjects() {
    try {
        console.log('🔄 Chargement des projets...');
        const response = await fetch(`${API_BASE}/projects`);
        const data = await response.json();
        
        if (!response.ok || (data.error && data.error === 'Base de données non disponible')) {
            const projectsList = document.getElementById('projects-list');
            if (projectsList) {
                projectsList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à la base de données n\'est pas disponible.'}</p>
                    </div>
                `;
            }
            showToast('Impossible de charger les projets : Base de données non disponible', 'error');
            return;
        }
        
        const projects = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${projects.length} projet(s) chargé(s)`);
        
        allProjectsData = projects;
        displayProjects(projects);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des projets:', error);
        showToast('Erreur lors du chargement des projets', 'error');
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
        
        const statusBadge = project.status === 'published' 
            ? '<span style="background: var(--green); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">● Publié</span>' 
            : project.status === 'draft' 
            ? '<span style="background: orange; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">● Brouillon</span>' 
            : '<span style="background: gray; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">● Archivé</span>';
        
        const featuredBadge = project.featured 
            ? '<span style="background: var(--primary); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;"><i class="fas fa-star"></i> Vedette</span>' 
            : '';
        
        const description = project.description || '';
        const truncatedDesc = description.length > 100 ? description.substring(0, 100) + '...' : description;
        
        const links = [];
        if (project.link) links.push(`<a href="${escapeHtml(project.link)}" target="_blank" style="color: var(--green); margin-right: 0.5rem;"><i class="fas fa-external-link-alt"></i> Site</a>`);
        if (project.github_link) links.push(`<a href="${escapeHtml(project.github_link)}" target="_blank" style="color: var(--green);"><i class="fab fa-github"></i> GitHub</a>`);
        
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start; gap: 1rem;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <h3 style="margin: 0;">${escapeHtml(project.title || 'Sans titre')}</h3>
                        ${statusBadge}
                        ${featuredBadge}
                    </div>
                    <p style="color: var(--gray); margin: 0.5rem 0;"><strong>Technologies:</strong> ${escapeHtml(project.technologies || 'N/A')}</p>
                    <p style="color: var(--gray); margin: 0.5rem 0; line-height: 1.5;">${escapeHtml(truncatedDesc)}</p>
                    ${links.length > 0 ? `<div style="margin-top: 0.5rem;">${links.join('')}</div>` : ''}
                    <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.85rem; color: var(--gray);">
                        <span><strong>Ordre:</strong> ${project.order || 0}</span>
                        ${project.views !== undefined ? `<span><strong>Vues:</strong> ${project.views || 0}</span>` : ''}
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-shrink: 0;">
                    <button class="btn btn-sm btn-info" onclick="viewProjectDetail('${project._id}')" title="Voir détail">
                        <i class="fas fa-eye"></i> Détail
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="editProject('${project._id}')" title="Modifier">
                        <i class="fas fa-edit"></i> Modifier
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProject('${project._id}', '${escapeHtml(project.title)}')" title="Supprimer">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>
                </div>
            </div>
        `;
        projectsList.appendChild(card);
    });
}

function initProjectsSection() {
    loadProjects();
    // Initialiser le formulaire de projet
    const projectForm = document.getElementById('project-form');
    if (projectForm) {
        projectForm.addEventListener('submit', handleProjectSubmit);
    }
}

// Exposer la fonction globalement
window.openProjectModal = function openProjectModal() {
    const modal = document.getElementById('projectModal');
    const modalTitle = document.getElementById('projectModalTitle');
    const projectIdInput = document.getElementById('project-id');
    
    if (modal) {
        // Afficher la modale avec les styles nécessaires
        modal.style.display = 'flex';
        modal.style.opacity = '1';
        modal.classList.add('open');
        
        if (modalTitle) modalTitle.textContent = 'Nouveau projet';
        if (projectIdInput) projectIdInput.value = '';
        
        // Réinitialiser le formulaire
        const form = document.getElementById('project-form');
        if (form) {
            form.reset();
            const statusInput = document.getElementById('project-status');
            const orderInput = document.getElementById('project-order');
            const featuredInput = document.getElementById('project-featured');
            if (statusInput) statusInput.value = 'published';
            if (orderInput) orderInput.value = '0';
            if (featuredInput) featuredInput.checked = false;
        }
        
        // Focus sur le premier champ après un court délai pour l'animation
        setTimeout(() => {
            const titleInput = document.getElementById('project-title');
            if (titleInput) titleInput.focus();
        }, 100);
    } else {
        console.error('Modal projectModal introuvable');
    }
};

// Exposer la fonction globalement
window.closeProjectModal = function closeProjectModal() {
    const modal = document.getElementById('projectModal');
    if (modal) {
        modal.style.display = 'none';
        modal.style.opacity = '0';
        modal.classList.remove('open');
        const form = document.getElementById('project-form');
        if (form) {
            form.reset();
            const projectIdInput = document.getElementById('project-id');
            if (projectIdInput) projectIdInput.value = '';
        }
    }
};

async function editProject(projectId) {
    const project = allProjectsData.find(p => p._id === projectId);
    if (!project) {
        showToast('Projet non trouvé', 'error');
        return;
    }
    
    // Ouvrir la modale
    const modal = document.getElementById('projectModal');
    const modalTitle = document.getElementById('projectModalTitle');
    const projectIdInput = document.getElementById('project-id');
    const titleInput = document.getElementById('project-title');
    const technologiesInput = document.getElementById('project-technologies');
    const descriptionInput = document.getElementById('project-description');
    const linkInput = document.getElementById('project-link');
    const githubInput = document.getElementById('project-github');
    const imageInput = document.getElementById('project-image');
    const additionalImagesInput = document.getElementById('project-additional-images');
    const statusInput = document.getElementById('project-status');
    const orderInput = document.getElementById('project-order');
    const featuredInput = document.getElementById('project-featured');
    
    if (modal) {
        // Afficher la modale avec les styles nécessaires
        modal.style.display = 'flex';
        modal.style.opacity = '1';
        modal.classList.add('open');
        
        if (modalTitle) modalTitle.textContent = 'Modifier le projet';
        if (projectIdInput) projectIdInput.value = projectId;
        if (titleInput) titleInput.value = project.title || '';
        if (technologiesInput) technologiesInput.value = project.technologies || '';
        if (descriptionInput) descriptionInput.value = project.description || '';
        if (linkInput) linkInput.value = project.link || '';
        if (githubInput) githubInput.value = project.github_link || '';
        if (imageInput) imageInput.value = project.image || '';
        if (additionalImagesInput) {
            const additionalImages = project.additional_images || '';
            additionalImagesInput.value = Array.isArray(additionalImages) 
                ? additionalImages.join(', ') 
                : additionalImages;
        }
        if (statusInput) statusInput.value = project.status || 'published';
        if (orderInput) orderInput.value = project.order || 0;
        if (featuredInput) featuredInput.checked = project.featured || false;
        
        // Focus sur le titre après un court délai
        setTimeout(() => {
            if (titleInput) titleInput.focus();
        }, 100);
    }
}

async function handleProjectSubmit(event) {
    event.preventDefault();
    
    const projectIdInput = document.getElementById('project-id');
    const titleInput = document.getElementById('project-title');
    const technologiesInput = document.getElementById('project-technologies');
    const descriptionInput = document.getElementById('project-description');
    const linkInput = document.getElementById('project-link');
    const githubInput = document.getElementById('project-github');
    const imageInput = document.getElementById('project-image');
    const additionalImagesInput = document.getElementById('project-additional-images');
    const statusInput = document.getElementById('project-status');
    const orderInput = document.getElementById('project-order');
    const featuredInput = document.getElementById('project-featured');
    const submitBtn = event.target.querySelector('button[type="submit"]');
    
    const projectId = projectIdInput ? projectIdInput.value : null;
    const title = titleInput ? titleInput.value.trim() : '';
    const technologies = technologiesInput ? technologiesInput.value.trim() : '';
    const description = descriptionInput ? descriptionInput.value.trim() : '';
    const link = linkInput ? linkInput.value.trim() : '';
    const github = githubInput ? githubInput.value.trim() : '';
    const image = imageInput ? imageInput.value.trim() : '';
    const additionalImages = additionalImagesInput ? additionalImagesInput.value.trim() : '';
    const status = statusInput ? statusInput.value : 'published';
    const order = orderInput ? parseInt(orderInput.value) || 0 : 0;
    const featured = featuredInput ? featuredInput.checked : false;
    
    // Validation
    if (!title) {
        showToast('Le titre est requis', 'error');
        if (titleInput) titleInput.focus();
        return;
    }
    
    if (!technologies) {
        showToast('Les technologies sont requises', 'error');
        if (technologiesInput) technologiesInput.focus();
        return;
    }
    
    if (!description) {
        showToast('La description est requise', 'error');
        if (descriptionInput) descriptionInput.focus();
        return;
    }
    
    // Validation des URLs
    if (link && !link.match(/^https?:\/\/.+/)) {
        showToast('Format d\'URL de lien invalide', 'error');
        if (linkInput) linkInput.focus();
        return;
    }
    
    if (github && !github.match(/^https?:\/\/.+/)) {
        showToast('Format d\'URL GitHub invalide', 'error');
        if (githubInput) githubInput.focus();
        return;
    }
    
    // Désactiver le bouton pendant la requête
    const originalBtnText = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = projectId ? 'Mise à jour...' : 'Création...';
    }
    
    try {
        const url = projectId ? `${API_BASE}/projects/${projectId}` : `${API_BASE}/projects`;
        const method = projectId ? 'PUT' : 'POST';
        
        const requestData = {
            title: title,
            technologies: technologies,
            description: description,
            status: status,
            order: order,
            featured: featured
        };
        
        if (link) requestData.link = link;
        if (github) requestData.github_link = github;
        if (image) requestData.image = image;
        if (additionalImages) requestData.additional_images = additionalImages;
        
        const response = await fetch(url, {
            method: method,
            headers: getHeaders(),
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || (projectId ? 'Erreur lors de la mise à jour' : 'Erreur lors de la création'), 'error');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
            return;
        }
        
        showToast(projectId ? 'Projet mis à jour avec succès' : 'Projet créé avec succès', 'success');
        closeProjectModal();
        
        // Mettre à jour la liste localement
        if (projectId) {
            // Mise à jour
            const projectIndex = allProjectsData.findIndex(p => p._id === projectId);
            if (projectIndex !== -1) {
            allProjectsData[projectIndex] = {
                ...allProjectsData[projectIndex],
                title: title,
                technologies: technologies,
                description: description,
                link: link,
                github_link: github,
                image: image,
                additional_images: additionalImages,
                status: status,
                order: order,
                featured: featured
            };
            }
        } else {
            // Création
            const newProject = {
                _id: data.id,
                title: title,
                technologies: technologies,
                description: description,
                link: link,
                github_link: github,
                image: image,
                additional_images: additionalImages,
                status: status,
                order: order,
                featured: featured,
                views: 0,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            allProjectsData.push(newProject);
            // Trier par ordre
            allProjectsData.sort((a, b) => (a.order || 0) - (b.order || 0));
        }
        
        // Réafficher immédiatement
        displayProjects(allProjectsData);
        
    } catch (error) {
        console.error('❌ Erreur:', error);
        showToast(projectId ? 'Erreur lors de la mise à jour' : 'Erreur lors de la création', 'error');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    }
}

// Exposer la fonction globalement
window.viewProjectDetail = async function viewProjectDetail(projectId) {
    const project = allProjectsData.find(p => p._id === projectId);
    if (!project) {
        showToast('Projet non trouvé', 'error');
        return;
    }
    
    // Ouvrir la modale de détail
    const modal = document.getElementById('projectDetailModal');
    const modalTitle = document.getElementById('projectDetailTitle');
    const modalBody = document.getElementById('projectDetailBody');
    
    if (!modal || !modalTitle || !modalBody) {
        showToast('Erreur: Modale de détail introuvable', 'error');
        return;
    }
    
    // Afficher la modale
    modal.style.display = 'flex';
    modal.style.opacity = '1';
    modal.classList.add('open');
    
    // Construire le contenu détaillé
    const statusText = project.status === 'published' ? 'Publié' : 
                      project.status === 'draft' ? 'Brouillon' : 'Archivé';
    const statusColor = project.status === 'published' ? 'var(--green)' : 
                       project.status === 'draft' ? 'orange' : 'gray';
    
    const featuredBadge = project.featured 
        ? '<span style="background: var(--primary); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;"><i class="fas fa-star"></i> En vedette</span>' 
        : '';
    
    // Préparer les images (image principale + images supplémentaires si disponibles)
    let imagesHtml = '';
    const allImages = [];
    
    // Ajouter l'image principale
    if (project.image) {
        allImages.push({ url: project.image, isMain: true });
    }
    
    // Ajouter les images supplémentaires
    if (project.additional_images) {
        const additionalImages = typeof project.additional_images === 'string' 
            ? project.additional_images.split(',').map(img => img.trim()).filter(img => img)
            : Array.isArray(project.additional_images) 
            ? project.additional_images 
            : [];
        
        additionalImages.forEach(img => {
            if (img && img !== project.image) {
                allImages.push({ url: img, isMain: false });
            }
        });
    }
    
    if (allImages.length > 0) {
        imagesHtml = `
            <div style="margin-bottom: 2rem;">
                <h4 style="margin-bottom: 1rem; color: var(--white);">
                    <i class="fas fa-images"></i> Images du projet (${allImages.length})
                </h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                    ${allImages.map((img, index) => `
                        <div style="position: relative;">
                            <img src="${escapeHtml(img.url)}" 
                                 alt="${escapeHtml(project.title)} - Image ${index + 1}" 
                                 style="width: 100%; height: 200px; object-fit: cover; border-radius: 8px; border: 2px solid ${img.isMain ? 'var(--green)' : 'var(--gray)'}; cursor: pointer; transition: transform 0.2s;"
                                 onclick="window.open('${escapeHtml(img.url)}', '_blank')"
                                 onmouseover="this.style.transform='scale(1.05)'"
                                 onmouseout="this.style.transform='scale(1)'"
                                 onerror="this.src='https://via.placeholder.com/400x200?text=Image+non+disponible'">
                            ${img.isMain ? `
                                <div style="position: absolute; top: 0.5rem; right: 0.5rem; background: var(--green); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                                    <i class="fas fa-star"></i> Principale
                                </div>
                            ` : ''}
                            <div style="position: absolute; bottom: 0.5rem; left: 0.5rem; background: rgba(0,0,0,0.7); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                                Image ${index + 1}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Construire le HTML complet
    modalTitle.textContent = project.title || 'Détails du projet';
    modalBody.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
            <!-- En-tête avec badges -->
            <div>
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
                    <h2 style="margin: 0; color: var(--white);">${escapeHtml(project.title || 'Sans titre')}</h2>
                    <span style="background: ${statusColor}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">${statusText}</span>
                    ${featuredBadge}
                </div>
            </div>
            
            <!-- Images -->
            ${imagesHtml}
            
            <!-- Description complète -->
            <div>
                <h4 style="margin-bottom: 0.5rem; color: var(--white);">
                    <i class="fas fa-align-left"></i> Description
                </h4>
                <p style="color: var(--gray); line-height: 1.8; white-space: pre-wrap;">${escapeHtml(project.description || 'Aucune description disponible')}</p>
            </div>
            
            <!-- Technologies -->
            <div>
                <h4 style="margin-bottom: 0.5rem; color: var(--white);">
                    <i class="fas fa-code"></i> Technologies utilisées
                </h4>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${(project.technologies || '').split(',').map(tech => 
                        `<span style="background: var(--light-bg); color: var(--green); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.875rem; border: 1px solid var(--green);">${escapeHtml(tech.trim())}</span>`
                    ).join('')}
                </div>
            </div>
            
            <!-- Liens -->
            <div>
                <h4 style="margin-bottom: 0.5rem; color: var(--white);">
                    <i class="fas fa-link"></i> Liens
                </h4>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    ${project.link ? `
                        <a href="${escapeHtml(project.link)}" target="_blank" 
                           style="display: inline-flex; align-items: center; gap: 0.5rem; color: var(--green); text-decoration: none; padding: 0.5rem 1rem; background: var(--light-bg); border-radius: 8px; border: 1px solid var(--green); transition: all 0.2s;">
                            <i class="fas fa-external-link-alt"></i> Visiter le site
                        </a>
                    ` : ''}
                    ${project.github_link ? `
                        <a href="${escapeHtml(project.github_link)}" target="_blank" 
                           style="display: inline-flex; align-items: center; gap: 0.5rem; color: var(--green); text-decoration: none; padding: 0.5rem 1rem; background: var(--light-bg); border-radius: 8px; border: 1px solid var(--green); transition: all 0.2s;">
                            <i class="fab fa-github"></i> Voir sur GitHub
                        </a>
                    ` : ''}
                    ${!project.link && !project.github_link ? '<span style="color: var(--gray);">Aucun lien disponible</span>' : ''}
                </div>
            </div>
            
            <!-- Statistiques -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; padding: 1rem; background: var(--dark-bg); border-radius: 8px;">
                <div>
                    <div style="color: var(--gray); font-size: 0.875rem; margin-bottom: 0.25rem;">Ordre d'affichage</div>
                    <div style="color: var(--white); font-size: 1.25rem; font-weight: 600;">${project.order || 0}</div>
                </div>
                <div>
                    <div style="color: var(--gray); font-size: 0.875rem; margin-bottom: 0.25rem;">Nombre de vues</div>
                    <div style="color: var(--white); font-size: 1.25rem; font-weight: 600;">${(project.views || 0).toLocaleString('fr-FR')}</div>
                </div>
                ${project.created_at ? `
                    <div>
                        <div style="color: var(--gray); font-size: 0.875rem; margin-bottom: 0.25rem;">Date de création</div>
                        <div style="color: var(--white); font-size: 0.875rem;">${new Date(project.created_at).toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
};

// Exposer la fonction globalement
window.closeProjectDetailModal = function closeProjectDetailModal() {
    const modal = document.getElementById('projectDetailModal');
    if (modal) {
        modal.style.display = 'none';
        modal.style.opacity = '0';
        modal.classList.remove('open');
    }
};

function deleteProject(projectId, projectTitle) {
    const title = projectTitle || 'ce projet';
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le projet "${title}" ?\n\nCette action est irréversible.`)) {
        return;
    }
    
    fetch(`${API_BASE}/projects/${projectId}`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Projet supprimé avec succès', 'success');
            
            // Retirer de la liste localement
            allProjectsData = allProjectsData.filter(p => p._id !== projectId);
            displayProjects(allProjectsData); // Réafficher immédiatement
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    })
    .catch(error => {
        console.error('❌ Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    });
}

// ========== Services Management ==========
let allServicesData = [];

async function loadServices() {
    try {
        console.log('🔄 Chargement des services...');
        const response = await fetch(`${API_BASE}/services`);
        const data = await response.json();
        
        if (!response.ok || (data.error && data.error === 'Base de données non disponible')) {
            const servicesList = document.getElementById('services-list');
            if (servicesList) {
                servicesList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: var(--gray);">
                        <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                        <p>${data.message || 'La connexion à la base de données n\'est pas disponible.'}</p>
                    </div>
                `;
            }
            showToast('Impossible de charger les services : Base de données non disponible', 'error');
            return;
        }
        
        const services = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${services.length} service(s) chargé(s)`);
        
        allServicesData = services;
        displayServices(services);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des services:', error);
        showToast('Erreur lors du chargement des services', 'error');
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
        
        const description = service.description || '';
        const truncatedDesc = description.length > 150 ? description.substring(0, 150) + '...' : description;
        const iconDisplay = service.icon ? `<div style="margin-bottom: 0.5rem;"><i class="fas fa-image" style="color: var(--green);"></i> <span style="font-size: 0.85rem; color: var(--gray);">${escapeHtml(service.icon)}</span></div>` : '';
        
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start; gap: 1rem;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 0.5rem 0;">${escapeHtml(service.title || 'Sans titre')}</h3>
                    ${iconDisplay}
                    <p style="color: var(--gray); margin: 0.5rem 0; line-height: 1.5;">${escapeHtml(truncatedDesc)}</p>
                    <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.85rem; color: var(--gray);">
                        <span><strong>Ordre:</strong> ${service.order || 0}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-shrink: 0;">
                    <button class="btn btn-sm btn-primary" onclick="editService('${service._id}')" title="Modifier">
                        <i class="fas fa-edit"></i> Modifier
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteService('${service._id}', '${escapeHtml(service.title)}')" title="Supprimer">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>
                </div>
            </div>
        `;
        servicesList.appendChild(card);
    });
}

function initServicesSection() {
    loadServices();
    // Initialiser le formulaire de service
    const serviceForm = document.getElementById('service-form');
    if (serviceForm) {
        serviceForm.addEventListener('submit', handleServiceSubmit);
    }
}

// Exposer la fonction globalement
window.openServiceModal = function openServiceModal() {
    const modal = document.getElementById('serviceModal');
    const modalTitle = document.getElementById('serviceModalTitle');
    const serviceIdInput = document.getElementById('service-id');
    
    if (modal) {
        // Afficher la modale avec les styles nécessaires
        modal.style.display = 'flex';
        modal.style.opacity = '1';
        modal.classList.add('open');
        
        if (modalTitle) modalTitle.textContent = 'Nouveau service';
        if (serviceIdInput) serviceIdInput.value = '';
        
        // Réinitialiser le formulaire
        const form = document.getElementById('service-form');
        if (form) {
            form.reset();
            const orderInput = document.getElementById('service-order');
            if (orderInput) orderInput.value = '0';
        }
        
        // Focus sur le premier champ après un court délai pour l'animation
        setTimeout(() => {
            const titleInput = document.getElementById('service-title');
            if (titleInput) titleInput.focus();
        }, 100);
    } else {
        console.error('Modal serviceModal introuvable');
    }
};

// Exposer la fonction globalement
window.closeServiceModal = function closeServiceModal() {
    const modal = document.getElementById('serviceModal');
    if (modal) {
        modal.style.display = 'none';
        modal.style.opacity = '0';
        modal.classList.remove('open');
        const form = document.getElementById('service-form');
        if (form) {
            form.reset();
            const serviceIdInput = document.getElementById('service-id');
            if (serviceIdInput) serviceIdInput.value = '';
        }
    }
};

async function editService(serviceId) {
    const service = allServicesData.find(s => s._id === serviceId);
    if (!service) {
        showToast('Service non trouvé', 'error');
        return;
    }
    
    // Ouvrir la modale
    const modal = document.getElementById('serviceModal');
    const modalTitle = document.getElementById('serviceModalTitle');
    const serviceIdInput = document.getElementById('service-id');
    const titleInput = document.getElementById('service-title');
    const descriptionInput = document.getElementById('service-description');
    const iconInput = document.getElementById('service-icon');
    const orderInput = document.getElementById('service-order');
    
    if (modal) {
        // Afficher la modale avec les styles nécessaires
        modal.style.display = 'flex';
        modal.style.opacity = '1';
        modal.classList.add('open');
        
        if (modalTitle) modalTitle.textContent = 'Modifier le service';
        if (serviceIdInput) serviceIdInput.value = serviceId;
        if (titleInput) titleInput.value = service.title || '';
        if (descriptionInput) descriptionInput.value = service.description || '';
        if (iconInput) iconInput.value = service.icon || '';
        if (orderInput) orderInput.value = service.order || 0;
        
        // Focus sur le titre après un court délai
        setTimeout(() => {
            if (titleInput) titleInput.focus();
        }, 100);
    }
}

async function handleServiceSubmit(event) {
    event.preventDefault();
    
    const serviceIdInput = document.getElementById('service-id');
    const titleInput = document.getElementById('service-title');
    const descriptionInput = document.getElementById('service-description');
    const iconInput = document.getElementById('service-icon');
    const orderInput = document.getElementById('service-order');
    const submitBtn = event.target.querySelector('button[type="submit"]');
    
    const serviceId = serviceIdInput ? serviceIdInput.value : null;
    const title = titleInput ? titleInput.value.trim() : '';
    const description = descriptionInput ? descriptionInput.value.trim() : '';
    const icon = iconInput ? iconInput.value.trim() : '';
    const order = orderInput ? parseInt(orderInput.value) || 0 : 0;
    
    // Validation
    if (!title) {
        showToast('Le titre est requis', 'error');
        if (titleInput) titleInput.focus();
        return;
    }
    
    if (!description) {
        showToast('La description est requise', 'error');
        if (descriptionInput) descriptionInput.focus();
        return;
    }
    
    // Désactiver le bouton pendant la requête
    const originalBtnText = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = serviceId ? 'Mise à jour...' : 'Création...';
    }
    
    try {
        const url = serviceId ? `${API_BASE}/services/${serviceId}` : `${API_BASE}/services`;
        const method = serviceId ? 'PUT' : 'POST';
        
        const requestData = {
            title: title,
            description: description,
            order: order
        };
        
        if (icon) {
            requestData.icon = icon;
        }
        
        const response = await fetch(url, {
            method: method,
            headers: getHeaders(),
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || (serviceId ? 'Erreur lors de la mise à jour' : 'Erreur lors de la création'), 'error');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
            return;
        }
        
        showToast(serviceId ? 'Service mis à jour avec succès' : 'Service créé avec succès', 'success');
        closeServiceModal();
        
        // Mettre à jour la liste localement
        if (serviceId) {
            // Mise à jour
            const serviceIndex = allServicesData.findIndex(s => s._id === serviceId);
            if (serviceIndex !== -1) {
                allServicesData[serviceIndex] = {
                    ...allServicesData[serviceIndex],
                    title: title,
                    description: description,
                    icon: icon,
                    order: order
                };
            }
        } else {
            // Création
            const newService = {
                _id: data.id,
                title: title,
                description: description,
                icon: icon,
                order: order,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            allServicesData.push(newService);
            // Trier par ordre
            allServicesData.sort((a, b) => (a.order || 0) - (b.order || 0));
        }
        
        // Réafficher immédiatement
        displayServices(allServicesData);
        
    } catch (error) {
        console.error('❌ Erreur:', error);
        showToast(serviceId ? 'Erreur lors de la mise à jour' : 'Erreur lors de la création', 'error');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    }
}

function deleteService(serviceId, serviceTitle) {
    const title = serviceTitle || 'ce service';
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le service "${title}" ?\n\nCette action est irréversible.`)) {
        return;
    }
    
    fetch(`${API_BASE}/services/${serviceId}`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Service supprimé avec succès', 'success');
            
            // Retirer de la liste localement
            allServicesData = allServicesData.filter(s => s._id !== serviceId);
            displayServices(allServicesData); // Réafficher immédiatement
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    })
    .catch(error => {
        console.error('❌ Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    });
}

// ========== Contacts Management ==========
let allContacts = [];

async function loadContacts() {
    try {
        console.log('🔄 Chargement des contacts...');
        const response = await fetch(`${API_BASE}/contacts`, {
            headers: getHeaders()
        });
        const data = await response.json();
        
        const contactsList = document.getElementById('contacts-list');
        if (!contactsList) return;
        
        if (!response.ok || (data.error && data.error === 'Base de données non disponible')) {
            contactsList.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: var(--gray);">
                    <p style="font-size: 1.2rem; margin-bottom: 1rem;">⚠️ Base de données non disponible</p>
                    <p>${data.message || 'La connexion à la base de données n\'est pas disponible.'}</p>
                </div>
            `;
            showToast('Impossible de charger les contacts : Base de données non disponible', 'error');
            updateContactsCount([]);
            return;
        }
        
        const contacts = Array.isArray(data) ? data : (data.data || []);
        console.log(`✅ ${contacts.length} contact(s) chargé(s)`);
        
        allContacts = contacts;
        
        // Appliquer le filtre actuel
        const filter = document.getElementById('contacts-filter')?.value || 'all';
        let filtered = contacts;
        if (filter === 'unread') {
            filtered = contacts.filter(c => !c.read);
        } else if (filter === 'read') {
            filtered = contacts.filter(c => c.read);
        }
        
        displayContacts(filtered);
    } catch (error) {
        console.error('❌ Erreur lors du chargement des contacts:', error);
        showToast('Erreur lors du chargement des contacts', 'error');
        const contactsList = document.getElementById('contacts-list');
        if (contactsList) {
            contactsList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun message disponible.</p>';
        }
        updateContactsCount([]);
    }
}

function displayContacts(contacts) {
    const contactsList = document.getElementById('contacts-list');
    if (!contactsList) return;
    
    if (contacts.length === 0) {
        contactsList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun message disponible.</p>';
        updateContactsCount(); // Utiliser allContacts pour le compteur
        return;
    }
    
    // Mettre à jour le compteur avec tous les contacts
    updateContactsCount();
    
    contactsList.innerHTML = '';
    contacts.forEach(contact => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        
        // Style pour les messages non lus
        const isUnread = !contact.read;
        if (isUnread) {
            card.style.borderLeft = '4px solid var(--green)';
            card.style.backgroundColor = 'var(--dark-bg)';
        }
        
        const date = new Date(contact.created_at);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const readBadge = isUnread 
            ? '<span style="background: var(--green); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">NON LU</span>'
            : '<span style="background: var(--gray); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">LU</span>';
        
        card.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <h3 style="margin: 0; ${isUnread ? 'font-weight: bold;' : ''}">${escapeHtml(contact.subject || 'Sans sujet')}</h3>
                            ${readBadge}
                        </div>
                        <div style="color: var(--gray); font-size: 0.9rem; margin-top: 0.5rem;">
                            <p><strong>De:</strong> ${escapeHtml(contact.name)} (<a href="mailto:${contact.email}" style="color: var(--green);">${escapeHtml(contact.email)}</a>)</p>
                            <p><strong>Date:</strong> ${formattedDate}</p>
                        </div>
                        <div style="background: var(--dark-bg); padding: 1rem; border-radius: 8px; margin-top: 0.5rem; max-height: 200px; overflow-y: auto;">
                            <p style="color: var(--white); white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(contact.message || '')}</p>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    ${isUnread 
                        ? `<button class="btn btn-sm btn-success" onclick="markContactRead('${contact._id}', true)" title="Marquer comme lu">
                            <i class="fas fa-check"></i> Marquer comme lu
                        </button>`
                        : `<button class="btn btn-sm btn-secondary" onclick="markContactRead('${contact._id}', false)" title="Marquer comme non lu">
                            <i class="fas fa-envelope"></i> Marquer comme non lu
                        </button>`
                    }
                    <a href="mailto:${contact.email}?subject=Re: ${encodeURIComponent(contact.subject || '')}" class="btn btn-sm btn-primary" target="_blank">
                        <i class="fas fa-reply"></i> Répondre
                    </a>
                    <button class="btn btn-sm btn-danger" onclick="deleteContact('${contact._id}')" title="Supprimer">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>
                </div>
            </div>
        `;
        contactsList.appendChild(card);
    });
}

function updateContactsCount(contacts) {
    // Toujours utiliser allContacts pour le compteur total, pas les contacts filtrés
    const unreadCount = allContacts.filter(c => !c.read).length;
    const unreadCountEl = document.getElementById('unread-count');
    if (unreadCountEl) {
        unreadCountEl.textContent = unreadCount;
        unreadCountEl.style.color = unreadCount > 0 ? 'var(--green)' : 'var(--gray)';
        unreadCountEl.style.fontWeight = unreadCount > 0 ? 'bold' : 'normal';
    }
}

function filterContacts() {
    const filter = document.getElementById('contacts-filter').value;
    let filtered = allContacts;
    
    if (filter === 'unread') {
        filtered = allContacts.filter(c => !c.read);
    } else if (filter === 'read') {
        filtered = allContacts.filter(c => c.read);
    }
    
    displayContacts(filtered);
}

async function markContactRead(contactId, readStatus) {
    try {
        const response = await fetch(`${API_BASE}/contacts/${contactId}/read`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ read: readStatus })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Erreur lors de la mise à jour', 'error');
            return;
        }
        
        // Mettre à jour l'état local sans recharger toute la page
        const contactIndex = allContacts.findIndex(c => c._id === contactId);
        if (contactIndex !== -1) {
            allContacts[contactIndex].read = readStatus;
        }
        
        // Mettre à jour l'affichage immédiatement
        const filter = document.getElementById('contacts-filter')?.value || 'all';
        let filtered = allContacts;
        if (filter === 'unread') {
            filtered = allContacts.filter(c => !c.read);
        } else if (filter === 'read') {
            filtered = allContacts.filter(c => c.read);
        }
        
        displayContacts(filtered);
        
        showToast(readStatus ? 'Message marqué comme lu' : 'Message marqué comme non lu', 'success');
        
    } catch (error) {
        console.error('❌ Erreur lors de la mise à jour:', error);
        showToast('Erreur lors de la mise à jour', 'error');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Fonction pour activer/désactiver les notifications (à implémenter)
function toggleNotifications() {
    const toggleBtn = document.getElementById('notification-toggle');
    const isEnabled = toggleBtn.classList.contains('active');
    
    if (isEnabled) {
        toggleBtn.classList.remove('active');
        toggleBtn.innerHTML = '<i class="fas fa-bell-slash"></i>';
        toggleBtn.title = 'Activer les notifications';
        localStorage.setItem('notificationsEnabled', 'false');
        showToast('Notifications désactivées', 'info');
    } else {
        toggleBtn.classList.add('active');
        toggleBtn.innerHTML = '<i class="fas fa-bell"></i>';
        toggleBtn.title = 'Désactiver les notifications';
        localStorage.setItem('notificationsEnabled', 'true');
        showToast('Notifications activées', 'success');
    }
}

// Vérifier l'état des notifications au chargement
document.addEventListener('DOMContentLoaded', function() {
    const notificationsEnabled = localStorage.getItem('notificationsEnabled') !== 'false';
    const toggleBtn = document.getElementById('notification-toggle');
    if (toggleBtn) {
        if (notificationsEnabled) {
            toggleBtn.classList.add('active');
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-bell-slash"></i>';
        }
    }
});

function deleteContact(contactId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {
        fetch(`${API_BASE}/contacts/${contactId}`, {
            method: 'DELETE',
            headers: getHeaders()
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Message supprimé', 'success');
                loadContacts();
            } else {
                showToast(data.error || 'Erreur lors de la suppression', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur lors de la suppression', 'error');
        });
    }
}

// ========== Profile Management ==========
// Variable pour stocker les données du profil
let currentProfileData = null;

async function loadProfile() {
    try {
        console.log('🔄 Chargement du profil...');
        const response = await fetch(`${API_BASE}/admin/profile`, {
            headers: getHeaders()
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                showToast('Session expirée. Veuillez vous reconnecter.', 'error');
                setTimeout(() => window.location.href = '/admin/login', 2000);
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const profile = await response.json();
        console.log('✅ Profil chargé:', profile);
        
        // Stocker les données du profil
        currentProfileData = profile;
        currentAdminId = profile._id || profile.id || null;
        
        // Remplir le formulaire
        const usernameInput = document.getElementById('profile-username');
        const emailInput = document.getElementById('profile-email');
        const fullNameInput = document.getElementById('profile-full-name');
        
        if (usernameInput) usernameInput.value = profile.username || '';
        if (emailInput) emailInput.value = profile.email || '';
        if (fullNameInput) fullNameInput.value = profile.full_name || '';
        
        // Mettre à jour la barre supérieure
        updateTopBarUserInfo(profile.full_name || profile.username);
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement du profil:', error);
        showToast('Erreur lors du chargement du profil', 'error');
    }
}

async function updateProfile(event) {
    event.preventDefault();
    
    const emailInput = document.getElementById('profile-email');
    const fullNameInput = document.getElementById('profile-full-name');
    const submitBtn = event.target.querySelector('button[type="submit"]');
    
    const email = emailInput.value.trim();
    const fullName = fullNameInput.value.trim();
    
    // Validation
    if (email && !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        showToast('Format d\'email invalide', 'error');
        emailInput.focus();
        return;
    }
    
    // Désactiver le bouton pendant la requête
    const originalBtnText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Enregistrement...';
    
    try {
        const response = await fetch(`${API_BASE}/admin/profile`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({
                email: email,
                full_name: fullName
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Erreur lors de la mise à jour du profil', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
            return;
        }
        
        // Mise à jour visuelle immédiate (optimistic update)
        // Les valeurs sont déjà dans les champs, on confirme juste le succès
        emailInput.style.borderColor = 'var(--green)';
        fullNameInput.style.borderColor = 'var(--green)';
        
        // Retirer le style après 2 secondes
        setTimeout(() => {
            emailInput.style.borderColor = '';
            fullNameInput.style.borderColor = '';
        }, 2000);
        
        showToast('Profil mis à jour avec succès', 'success');
        
        // Mettre à jour le nom d'affichage dans la barre supérieure si nécessaire
        updateTopBarUserInfo(fullName);
        
    } catch (error) {
        console.error('❌ Erreur lors de la mise à jour du profil:', error);
        showToast('Erreur lors de la mise à jour du profil', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    }
}

function updateTopBarUserInfo(fullName) {
    // Mettre à jour le nom dans la barre supérieure
    const topBarName = document.getElementById('currentUsername') || document.querySelector('.chip-label');
    if (topBarName) {
        if (fullName) {
            topBarName.textContent = fullName;
            // Mettre à jour aussi currentProfileData
            if (currentProfileData) {
                currentProfileData.full_name = fullName;
            }
        } else if (currentProfileData && currentProfileData.username) {
            topBarName.textContent = currentProfileData.username;
        }
    }
}

async function changePassword(event) {
    event.preventDefault();
    
    const currentPasswordInput = document.getElementById('current-password');
    const newPasswordInput = document.getElementById('new-password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const submitBtn = event.target.querySelector('button[type="submit"]');
    
    const currentPassword = currentPasswordInput.value;
    const newPassword = newPasswordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    
    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
        showToast('Tous les champs sont requis', 'error');
        if (!currentPassword) currentPasswordInput.focus();
        else if (!newPassword) newPasswordInput.focus();
        else confirmPasswordInput.focus();
        return;
    }
    
    if (newPassword.length < 6) {
        showToast('Le nouveau mot de passe doit contenir au moins 6 caractères', 'error');
        newPasswordInput.focus();
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showToast('Les nouveaux mots de passe ne correspondent pas', 'error');
        confirmPasswordInput.focus();
        confirmPasswordInput.style.borderColor = 'var(--red)';
        setTimeout(() => {
            confirmPasswordInput.style.borderColor = '';
        }, 2000);
        return;
    }
    
    if (currentPassword === newPassword) {
        showToast('Le nouveau mot de passe doit être différent de l\'actuel', 'error');
        newPasswordInput.focus();
        return;
    }
    
    // Désactiver le bouton pendant la requête
    const originalBtnText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Changement en cours...';
    
    try {
        const response = await fetch(`${API_BASE}/admin/profile/password`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Erreur lors du changement de mot de passe', 'error');
            // Réactiver le bouton en cas d'erreur
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
            
            // Mettre en évidence le champ du mot de passe actuel en cas d'erreur
            if (data.error && data.error.toLowerCase().includes('actuel')) {
                currentPasswordInput.style.borderColor = 'var(--red)';
                currentPasswordInput.focus();
                setTimeout(() => {
                    currentPasswordInput.style.borderColor = '';
                }, 2000);
            }
            return;
        }
        
        // Succès - mise à jour visuelle immédiate
        showToast('Mot de passe changé avec succès', 'success');
        
        // Réinitialiser le formulaire avec un effet visuel
        resetPasswordForm();
        
        // Indicateur visuel de succès sur les champs
        newPasswordInput.style.borderColor = 'var(--green)';
        confirmPasswordInput.style.borderColor = 'var(--green)';
        setTimeout(() => {
            newPasswordInput.style.borderColor = '';
            confirmPasswordInput.style.borderColor = '';
        }, 2000);
        
    } catch (error) {
        console.error('❌ Erreur lors du changement de mot de passe:', error);
        showToast('Erreur lors du changement de mot de passe', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    }
}

function resetPasswordForm() {
    document.getElementById('password-form').reset();
}

async function loadLoginHistory() {
    try {
        console.log('🔄 Chargement de l\'historique de connexion...');
        const response = await fetch(`${API_BASE}/admin/profile/login-history?limit=50`, {
            headers: getHeaders()
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                showToast('Session expirée. Veuillez vous reconnecter.', 'error');
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const history = await response.json();
        console.log(`✅ ${history.length} entrée(s) d'historique chargée(s)`);
        
        displayLoginHistory(history);
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement de l\'historique:', error);
        showToast('Erreur lors du chargement de l\'historique', 'error');
    }
}

function displayLoginHistory(history) {
    const historyList = document.getElementById('login-history-list');
    if (!historyList) return;
    
    if (history.length === 0) {
        historyList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun historique disponible.</p>';
        return;
    }
    
    historyList.innerHTML = '';
    
    history.forEach(entry => {
        const item = document.createElement('div');
        item.className = 'admin-list-item';
        item.style.cssText = 'padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;';
        
        const successIcon = entry.success ? '✅' : '❌';
        const successText = entry.success ? 'Succès' : 'Échec';
        const successColor = entry.success ? 'var(--green)' : 'var(--red)';
        
        const date = new Date(entry.login_time);
        const formattedDate = date.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        item.innerHTML = `
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem;">${successIcon}</span>
                    <strong style="color: ${successColor};">${successText}</strong>
                    <span style="color: var(--gray); font-size: 0.9rem;">${formattedDate}</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--gray);">
                    <div><strong>IP:</strong> ${entry.ip_address || 'N/A'}</div>
                    <div style="margin-top: 0.25rem;"><strong>User-Agent:</strong> ${(entry.user_agent || 'N/A').substring(0, 80)}${entry.user_agent && entry.user_agent.length > 80 ? '...' : ''}</div>
                </div>
            </div>
        `;
        
        historyList.appendChild(item);
    });
}

// Initialiser le profil quand la section est affichée
function initProfileSection() {
    loadProfile();
    loadLoginHistory();
}

// ========== Admin Users Management ==========
let allAdminsData = [];

async function loadAdminUsers() {
    try {
        console.log('🔄 Chargement des administrateurs...');
        const response = await fetch(`${API_BASE}/admin/users`, {
            headers: getHeaders()
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                showToast('Session expirée. Veuillez vous reconnecter.', 'error');
                setTimeout(() => window.location.href = '/admin/login', 2000);
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const admins = await response.json();
        console.log(`✅ ${admins.length} administrateur(s) chargé(s)`);
        
        allAdminsData = admins;
        displayAdminUsers(admins);
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement des administrateurs:', error);
        showToast('Erreur lors du chargement des administrateurs', 'error');
        const adminsList = document.getElementById('admins-list');
        if (adminsList) {
            adminsList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun administrateur disponible.</p>';
        }
    }
}

function displayAdminUsers(admins) {
    const adminsList = document.getElementById('admins-list');
    if (!adminsList) return;
    
    // Utiliser la variable globale currentAdminId
    
    if (admins.length === 0) {
        adminsList.innerHTML = '<p style="color: var(--gray); text-align: center; padding: 2rem;">Aucun administrateur disponible.</p>';
        return;
    }
    
    adminsList.innerHTML = '';
    admins.forEach(admin => {
        const card = document.createElement('div');
        card.className = 'admin-card';
        
        const date = new Date(admin.created_at);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        const lastLogin = admin.last_login 
            ? new Date(admin.last_login).toLocaleDateString('fr-FR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            })
            : 'Jamais';
        
        // Utiliser currentAdminId ou currentProfileData._id pour identifier l'utilisateur actuel
        const adminIdToCompare = currentAdminId || (currentProfileData && (currentProfileData._id || currentProfileData.id));
        const isCurrentUser = admin._id === adminIdToCompare;
        
        card.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <h3 style="margin: 0;">${escapeHtml(admin.username || 'Sans nom')}</h3>
                            ${isCurrentUser ? '<span style="background: var(--green); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">VOUS</span>' : ''}
                        </div>
                        <div style="color: var(--gray); font-size: 0.9rem;">
                            ${admin.full_name ? `<p><strong>Nom complet:</strong> ${escapeHtml(admin.full_name)}</p>` : ''}
                            ${admin.email ? `<p><strong>Email:</strong> <a href="mailto:${admin.email}" style="color: var(--green);">${escapeHtml(admin.email)}</a></p>` : ''}
                            <p><strong>Créé le:</strong> ${formattedDate}</p>
                            <p><strong>Dernière connexion:</strong> ${lastLogin}</p>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    ${!isCurrentUser 
                        ? `<button class="btn btn-sm btn-primary" onclick="editAdmin('${admin._id}')" title="Modifier">
                            <i class="fas fa-edit"></i> Modifier
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteAdmin('${admin._id}', '${escapeHtml(admin.username)}')" title="Supprimer">
                            <i class="fas fa-trash"></i> Supprimer
                        </button>`
                        : '<span style="color: var(--gray); font-size: 0.85rem;">Utilisez la section Profil pour modifier vos informations</span>'
                    }
                </div>
            </div>
        `;
        adminsList.appendChild(card);
    });
}

async function createAdmin(event) {
    event.preventDefault();
    
    const usernameInput = document.getElementById('new-admin-username');
    const passwordInput = document.getElementById('new-admin-password');
    const emailInput = document.getElementById('new-admin-email');
    const fullNameInput = document.getElementById('new-admin-full-name');
    const submitBtn = event.target.querySelector('button[type="submit"]');
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    const email = emailInput.value.trim();
    const fullName = fullNameInput.value.trim();
    
    // Validation
    if (!username || username.length < 3) {
        showToast('Le nom d\'utilisateur doit contenir au moins 3 caractères', 'error');
        usernameInput.focus();
        return;
    }
    
    if (!password || password.length < 6) {
        showToast('Le mot de passe doit contenir au moins 6 caractères', 'error');
        passwordInput.focus();
        return;
    }
    
    if (email && !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        showToast('Format d\'email invalide', 'error');
        emailInput.focus();
        return;
    }
    
    // Désactiver le bouton pendant la requête
    const originalBtnText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Création...';
    
    try {
        const response = await fetch(`${API_BASE}/admin/users`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                username: username,
                password: password,
                email: email || null,
                full_name: fullName || null
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Erreur lors de la création de l\'administrateur', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
            return;
        }
        
        showToast('Administrateur créé avec succès', 'success');
        closeCreateAdminModal();
        
        // Ajouter le nouvel admin à la liste localement
        const newAdmin = {
            _id: data.id,
            username: username,
            email: email || null,
            full_name: fullName || null,
            created_at: new Date().toISOString(),
            last_login: null
        };
        allAdminsData.unshift(newAdmin); // Ajouter au début
        displayAdminUsers(allAdminsData); // Réafficher immédiatement
        
    } catch (error) {
        console.error('❌ Erreur lors de la création:', error);
        showToast('Erreur lors de la création de l\'administrateur', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    }
}

function openCreateAdminModal() {
    const modal = document.getElementById('create-admin-modal');
    if (modal) {
        modal.style.display = 'flex';
        // Réinitialiser le formulaire
        document.getElementById('create-admin-form').reset();
        document.getElementById('new-admin-username').focus();
    }
}

function closeCreateAdminModal() {
    const modal = document.getElementById('create-admin-modal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('create-admin-form').reset();
    }
}

function editAdmin(adminId) {
    const admin = allAdminsData.find(a => a._id === adminId);
    if (!admin) {
        showToast('Administrateur non trouvé', 'error');
        return;
    }
    
    // Pour l'instant, on utilise une modale simple avec prompt
    // Vous pouvez créer une modale dédiée plus tard
    const newEmail = prompt('Nouvel email (laissez vide pour ne pas modifier):', admin.email || '');
    const newFullName = prompt('Nouveau nom complet (laissez vide pour ne pas modifier):', admin.full_name || '');
    const newPassword = prompt('Nouveau mot de passe (laissez vide pour ne pas modifier, min. 6 caractères):', '');
    
    if (newEmail === null && newFullName === null && newPassword === null) {
        return; // Annulé
    }
    
    const updateData = {};
    if (newEmail !== null && newEmail !== admin.email) {
        updateData.email = newEmail;
    }
    if (newFullName !== null && newFullName !== admin.full_name) {
        updateData.full_name = newFullName;
    }
    if (newPassword && newPassword.length >= 6) {
        updateData.password = newPassword;
    } else if (newPassword && newPassword.length > 0) {
        showToast('Le mot de passe doit contenir au moins 6 caractères', 'error');
        return;
    }
    
    if (Object.keys(updateData).length === 0) {
        showToast('Aucune modification', 'info');
        return;
    }
    
    updateAdmin(adminId, updateData);
}

async function updateAdmin(adminId, updateData) {
    try {
        const response = await fetch(`${API_BASE}/admin/users/${adminId}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Erreur lors de la mise à jour', 'error');
            return;
        }
        
        showToast('Administrateur mis à jour avec succès', 'success');
        
        // Mettre à jour l'état local immédiatement
        const adminIndex = allAdminsData.findIndex(a => a._id === adminId);
        if (adminIndex !== -1) {
            if (updateData.email !== undefined) allAdminsData[adminIndex].email = updateData.email;
            if (updateData.full_name !== undefined) allAdminsData[adminIndex].full_name = updateData.full_name;
        }
        
        // Réafficher la liste immédiatement
        displayAdminUsers(allAdminsData);
        
    } catch (error) {
        console.error('❌ Erreur lors de la mise à jour:', error);
        showToast('Erreur lors de la mise à jour', 'error');
    }
}

function deleteAdmin(adminId, username) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer l'administrateur "${username}" ?\n\nCette action est irréversible.`)) {
        return;
    }
    
    fetch(`${API_BASE}/admin/users/${adminId}`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Administrateur supprimé avec succès', 'success');
            
            // Retirer de la liste localement
            allAdminsData = allAdminsData.filter(a => a._id !== adminId);
            displayAdminUsers(allAdminsData); // Réafficher immédiatement
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    });
}

