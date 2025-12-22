// ============================================
// Admin Data Management JavaScript
// ============================================

const API_BASE = '/api';

// Headers pour les requêtes API
// La session Flask gère l'authentification automatiquement via les cookies
const getHeaders = () => {
    return {
        'Content-Type': 'application/json'
    };
};

// Fonction pour gérer les erreurs 401 (session expirée)
async function handle401Error() {
    showToast('Session expirée. Veuillez vous reconnecter.', 'error');
    // Rediriger vers la page de login après 2 secondes
    setTimeout(() => {
        window.location.href = '/admin/login';
    }, 2000);
    return false;
}

// ========== Navigation entre sections ==========
document.addEventListener('DOMContentLoaded', function() {
    const menuItems = document.querySelectorAll('.menu-item[data-section]');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (this.getAttribute('href') && this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const section = this.getAttribute('data-section');
                showSection(section);
                
                // Mettre à jour l'état actif
                menuItems.forEach(mi => mi.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    // Charger les données au démarrage
    loadHomepageData();
    loadSkills();
    loadPartners();
    loadProjects();
    loadServices();
    loadContacts();
    
    // Démarrer la vérification périodique des nouveaux messages
    requestNotificationPermission();
    startContactsMonitoring();
    
    // Charger le profil si on accède à la section
    const profileSection = document.getElementById('section-profile');
    if (profileSection && profileSection.style.display !== 'none') {
        loadProfile();
        loadLoginHistory();
    }
});

function showSection(sectionName) {
    // Masquer toutes les sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
        section.classList.remove('active-section');
    });

    // Afficher la section demandée
    const targetSection = document.getElementById(`section-${sectionName}`);
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.add('active-section');
        document.getElementById('current-page').textContent = 
            document.querySelector(`[data-section="${sectionName}"]`).getAttribute('aria-label') || sectionName;
        
        // Charger les données si nécessaire
        if (sectionName === 'projects') {
            initProjectsSection();
        } else if (sectionName === 'services') {
            initServicesSection();
        } else if (sectionName === 'contacts') {
            loadContacts();
        } else if (sectionName === 'profile') {
            loadProfile();
            loadLoginHistory();
        } else if (sectionName === 'skills') {
            initSkillsSection();
        } else if (sectionName === 'partners') {
            initPartnersSection();
        }
    }
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
            document.getElementById('homepage-badge').value = data.badge || '';
            document.getElementById('homepage-title1').value = data.title_line1 || '';
            document.getElementById('homepage-title2').value = data.title_line2 || '';
            document.getElementById('homepage-description').value = data.description || '';
            document.getElementById('homepage-email').value = data.email || '';
            document.getElementById('homepage-cta').value = data.cta_text || '';
            document.getElementById('homepage-about-title').value = data.about_title || '';
            document.getElementById('homepage-about-name').value = data.about_name || '';
            document.getElementById('homepage-about-subtitle').value = data.about_subtitle || '';
            document.getElementById('homepage-about-description').value = data.about_description || '';
        }
    } catch (error) {
        console.error('Erreur lors du chargement des données homepage:', error);
        showToast('Erreur lors du chargement des données. MongoDB est peut-être indisponible.', 'error');
    }
}

document.getElementById('homepage-form').addEventListener('submit', async function(e) {
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
                // Clé admin invalide - demander à nouveau
                const retry = await handle401Error();
                if (retry) {
                    // Réessayer la requête avec la nouvelle clé
                    const retryResponse = await fetch(`${API_BASE}/homepage`, {
                        method: 'PUT',
                        headers: getHeaders(),
                        body: JSON.stringify(formData)
                    });
                    const retryResult = await retryResponse.json();
                    if (retryResponse.ok && retryResult.success) {
                        showToast('Données enregistrées avec succès !', 'success');
                    } else {
                        showToast(retryResult.error || 'Erreur lors de l\'enregistrement', 'error');
                    }
                }
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

// ========== Skills Management ==========
async function loadSkills() {
    try {
        const response = await fetch(`${API_BASE}/skills`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const skills = await response.json();
        
        // Vérifier que skills est un tableau
        if (!Array.isArray(skills)) {
            console.error('Les compétences ne sont pas un tableau:', skills);
            const skillsList = document.getElementById('skills-list');
            if (skillsList) {
                skillsList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            }
            return;
        }
        
        // Stocker toutes les données
        allSkillsData = skills;
        
        // Filtrer et afficher
        filterAndDisplaySkills();
    } catch (error) {
        console.error('Erreur lors du chargement des compétences:', error);
        showToast('Erreur lors du chargement des compétences. MongoDB est peut-être indisponible.', 'error');
        const skillsList = document.getElementById('skills-list');
        if (skillsList) {
            skillsList.innerHTML = '<p>Aucune compétence disponible.</p>';
        }
    }
}

function createSkillCard(skill) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <h3>${skill.title}</h3>
                <p>${skill.description}</p>
                <p><strong>Projets:</strong> ${skill.projects_count} | <strong>Ordre:</strong> ${skill.order}</p>
            </div>
            <div>
                <button class="btn btn-sm btn-primary" onclick="editSkill('${skill._id}')">Modifier</button>
                <button class="btn btn-sm btn-danger" onclick="deleteSkill('${skill._id}')">Supprimer</button>
            </div>
        </div>
    `;
    return card;
}

function openSkillModal(skillId = null) {
    const modal = document.getElementById('skillModal');
    const form = document.getElementById('skill-form');
    
    if (skillId) {
        document.getElementById('skillModalTitle').textContent = 'Modifier la compétence';
        // Charger les données de la compétence
        loadSkillData(skillId);
    } else {
        document.getElementById('skillModalTitle').textContent = 'Nouvelle compétence';
        form.reset();
        document.getElementById('skill-id').value = '';
    }
    
    modal.style.display = 'flex';
    // Forcer le reflow pour l'animation
    setTimeout(() => {
        modal.classList.add('open');
    }, 10);
    
    // Fermer en cliquant sur l'overlay
    modal.addEventListener('click', function closeOnOverlay(e) {
        if (e.target === modal) {
            closeSkillModal();
            modal.removeEventListener('click', closeOnOverlay);
        }
    });
}

function closeSkillModal() {
    const modal = document.getElementById('skillModal');
    modal.classList.remove('open');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

async function loadSkillData(skillId) {
    try {
        const response = await fetch(`${API_BASE}/skills`);
        const skills = await response.json();
        const skill = skills.find(s => s._id === skillId);
        
        if (skill) {
            document.getElementById('skill-id').value = skill._id;
            document.getElementById('skill-title').value = skill.title;
            document.getElementById('skill-icon').value = skill.icon;
            document.getElementById('skill-description').value = skill.description;
            document.getElementById('skill-projects').value = skill.projects_count;
            document.getElementById('skill-order').value = skill.order || 1;
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

document.getElementById('skill-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const skillId = document.getElementById('skill-id').value;
    const formData = {
        title: document.getElementById('skill-title').value,
        icon: document.getElementById('skill-icon').value,
        description: document.getElementById('skill-description').value,
        projects_count: parseInt(document.getElementById('skill-projects').value),
        order: parseInt(document.getElementById('skill-order').value)
    };

    try {
        let response;
        if (skillId) {
            response = await fetch(`${API_BASE}/skills/${skillId}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(formData)
            });
        } else {
            response = await fetch(`${API_BASE}/skills`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(formData)
            });
        }

        if (!response.ok) {
            const result = await response.json();
            if (response.status === 401) {
                const retry = await handle401Error();
                if (retry) {
                    // Réessayer la requête
                    e.target.dispatchEvent(new Event('submit'));
                    return;
                }
                return;
            }
            showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            showToast('Compétence enregistrée avec succès !', 'success');
            closeSkillModal();
            loadSkills();
        } else {
            showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de l\'enregistrement', 'error');
    }
});

async function editSkill(skillId) {
    openSkillModal(skillId);
}

async function deleteSkill(skillId) {
    showConfirmModal(
        'Supprimer la compétence',
        'Êtes-vous sûr de vouloir supprimer cette compétence ? Cette action est irréversible.',
        () => {
            performDeleteSkill(skillId);
        }
    );
}

async function performDeleteSkill(skillId) {

    try {
        const response = await fetch(`${API_BASE}/skills/${skillId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });

        if (!response.ok) {
            const result = await response.json();
            if (response.status === 401) {
                await handle401Error();
                return;
            }
            showToast(result.error || 'Erreur lors de la suppression', 'error');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            showToast('Compétence supprimée avec succès !', 'success');
            loadSkills();
        } else {
            showToast(result.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
}

// ========== Partners Management ==========
async function loadPartners() {
    try {
        const response = await fetch(`${API_BASE}/partners`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const partners = await response.json();
        
        // Vérifier que partners est un tableau
        if (!Array.isArray(partners)) {
            console.error('Les partenaires ne sont pas un tableau:', partners);
            const partnersList = document.getElementById('partners-list');
            if (partnersList) {
                partnersList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            }
            return;
        }
        
        // Stocker toutes les données
        allPartnersData = partners;
        
        // Filtrer et afficher
        filterAndDisplayPartners();
    } catch (error) {
        console.error('Erreur lors du chargement des partenaires:', error);
        showToast('Erreur lors du chargement des partenaires. MongoDB est peut-être indisponible.', 'error');
        const partnersList = document.getElementById('partners-list');
        if (partnersList) {
            partnersList.innerHTML = '<p>Aucun partenaire disponible.</p>';
        }
    }
}

function createPartnerCard(partner) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <img src="/static/${partner.image}" alt="${partner.name}" style="width: 60px; height: auto;">
                <div>
                    <h3>${partner.name}</h3>
                    <p><strong>Ordre:</strong> ${partner.order}</p>
                </div>
            </div>
            <div>
                <button class="btn btn-sm btn-primary" onclick="editPartner('${partner._id}')">Modifier</button>
                <button class="btn btn-sm btn-danger" onclick="deletePartner('${partner._id}')">Supprimer</button>
            </div>
        </div>
    `;
    return card;
}

function openPartnerModal(partnerId = null) {
    const modal = document.getElementById('partnerModal');
    
    if (partnerId) {
        document.getElementById('partnerModalTitle').textContent = 'Modifier le partenaire';
        loadPartnerData(partnerId);
    } else {
        document.getElementById('partnerModalTitle').textContent = 'Nouveau partenaire';
        document.getElementById('partner-form').reset();
        document.getElementById('partner-id').value = '';
    }
    
    modal.style.display = 'flex';
    // Forcer le reflow pour l'animation
    setTimeout(() => {
        modal.classList.add('open');
    }, 10);
    
    // Fermer en cliquant sur l'overlay
    modal.addEventListener('click', function closeOnOverlay(e) {
        if (e.target === modal) {
            closePartnerModal();
            modal.removeEventListener('click', closeOnOverlay);
        }
    });
}

function closePartnerModal() {
    const modal = document.getElementById('partnerModal');
    modal.classList.remove('open');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

async function loadPartnerData(partnerId) {
    try {
        const response = await fetch(`${API_BASE}/partners`);
        const partners = await response.json();
        const partner = partners.find(p => p._id === partnerId);
        
        if (partner) {
            document.getElementById('partner-id').value = partner._id;
            document.getElementById('partner-name').value = partner.name;
            document.getElementById('partner-image').value = partner.image;
            document.getElementById('partner-order').value = partner.order || 1;
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

document.getElementById('partner-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const partnerId = document.getElementById('partner-id').value;
    const formData = {
        name: document.getElementById('partner-name').value,
        image: document.getElementById('partner-image').value,
        order: parseInt(document.getElementById('partner-order').value)
    };

    try {
        let response;
        if (partnerId) {
            response = await fetch(`${API_BASE}/partners/${partnerId}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(formData)
            });
        } else {
            response = await fetch(`${API_BASE}/partners`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(formData)
            });
        }

        if (!response.ok) {
            const result = await response.json();
            if (response.status === 401) {
                const retry = await handle401Error();
                if (retry) {
                    // Réessayer la requête
                    e.target.dispatchEvent(new Event('submit'));
                    return;
                }
                return;
            }
            showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            showToast('Partenaire enregistré avec succès !', 'success');
            closePartnerModal();
            loadPartners();
        } else {
            showToast(result.error || 'Erreur lors de l\'enregistrement', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de l\'enregistrement', 'error');
    }
});

async function editPartner(partnerId) {
    openPartnerModal(partnerId);
}

async function deletePartner(partnerId) {
    showConfirmModal(
        'Supprimer le partenaire',
        'Êtes-vous sûr de vouloir supprimer ce partenaire ? Cette action est irréversible.',
        () => {
            performDeletePartner(partnerId);
        }
    );
}

async function performDeletePartner(partnerId) {

    try {
        const response = await fetch(`${API_BASE}/partners/${partnerId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });

        if (!response.ok) {
            const result = await response.json();
            if (response.status === 401) {
                await handle401Error();
                return;
            }
            showToast(result.error || 'Erreur lors de la suppression', 'error');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            showToast('Partenaire supprimé avec succès !', 'success');
            loadPartners();
        } else {
            showToast(result.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
}

// ========== Projects Management ==========
async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE}/projects`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const projects = await response.json();
        
        // Vérifier que projects est un tableau
        if (!Array.isArray(projects)) {
            console.error('Les projets ne sont pas un tableau:', projects);
            const projectsList = document.getElementById('projects-list');
            if (projectsList) {
                projectsList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            }
            return;
        }
        
        // Stocker toutes les données
        allProjectsData = projects;
        
        // Filtrer et afficher
        filterAndDisplayProjects();
    } catch (error) {
        console.error('Erreur lors du chargement des projets:', error);
        showToast('Erreur lors du chargement des projets. MongoDB est peut-être indisponible.', 'error');
        const projectsList = document.getElementById('projects-list');
        if (projectsList) {
            projectsList.innerHTML = '<p>Aucun projet disponible.</p>';
        }
    }
}

function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    const statusBadge = project.status === 'published' ? '<span style="color: var(--green);">● Publié</span>' : 
                       project.status === 'draft' ? '<span style="color: orange;">● Brouillon</span>' : 
                       '<span style="color: gray;">● Archivé</span>';
    const featuredBadge = project.featured ? '<span style="color: gold;">⭐ En vedette</span>' : '';
    
    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <h3>${project.title || 'Sans titre'}</h3>
                <p style="color: var(--gray); margin: 0.5rem 0;"><strong>Technologies:</strong> ${project.technologies || 'N/A'}</p>
                <p style="color: var(--gray); margin: 0.5rem 0;">${project.description ? project.description.substring(0, 100) + '...' : ''}</p>
                <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.9rem;">
                    ${statusBadge}
                    ${featuredBadge}
                    <span><strong>Ordre:</strong> ${project.order || 0}</span>
                </div>
            </div>
            <div style="display: flex; gap: 0.5rem; margin-left: 1rem;">
                <button class="btn btn-sm btn-primary" onclick="editProject('${project._id}')">Modifier</button>
                <button class="btn btn-sm btn-danger" onclick="deleteProject('${project._id}')">Supprimer</button>
            </div>
        </div>
    `;
    return card;
}

function openProjectModal(projectId = null) {
    const modal = document.getElementById('projectModal');
    if (!modal) return;
    
    if (projectId) {
        document.getElementById('projectModalTitle').textContent = 'Modifier le projet';
        loadProjectData(projectId);
    } else {
        document.getElementById('projectModalTitle').textContent = 'Nouveau projet';
        document.getElementById('project-form').reset();
        document.getElementById('project-id').value = '';
        document.getElementById('project-status').value = 'published';
        document.getElementById('project-order').value = '0';
        document.getElementById('project-featured').checked = false;
    }
    
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.classList.add('open');
    }, 10);
    
    modal.addEventListener('click', function closeOnOverlay(e) {
        if (e.target === modal) {
            closeProjectModal();
            modal.removeEventListener('click', closeOnOverlay);
        }
    });
}

function closeProjectModal() {
    const modal = document.getElementById('projectModal');
    if (!modal) return;
    modal.classList.remove('open');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

async function loadProjectData(projectId) {
    try {
        const response = await fetch(`${API_BASE}/projects`);
        const projects = await response.json();
        const project = projects.find(p => p._id === projectId);
        
        if (project) {
            document.getElementById('project-id').value = project._id;
            document.getElementById('project-title').value = project.title || '';
            document.getElementById('project-technologies').value = project.technologies || '';
            document.getElementById('project-description').value = project.description || '';
            document.getElementById('project-link').value = project.link || '';
            document.getElementById('project-github').value = project.github_link || '';
            document.getElementById('project-image').value = project.image || '';
            document.getElementById('project-status').value = project.status || 'published';
            document.getElementById('project-order').value = project.order || 0;
            document.getElementById('project-featured').checked = project.featured || false;
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Attacher l'événement submit au formulaire de projet
document.addEventListener('DOMContentLoaded', function() {
    const projectForm = document.getElementById('project-form');
    if (projectForm) {
        projectForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const projectId = document.getElementById('project-id').value;
            const formData = {
                title: document.getElementById('project-title').value,
                technologies: document.getElementById('project-technologies').value,
                description: document.getElementById('project-description').value,
                link: document.getElementById('project-link').value,
                github_link: document.getElementById('project-github').value,
                image: document.getElementById('project-image').value,
                status: document.getElementById('project-status').value,
                order: parseInt(document.getElementById('project-order').value) || 0,
                featured: document.getElementById('project-featured').checked
            };

            try {
                let response;
                if (projectId) {
                    response = await fetch(`${API_BASE}/projects/${projectId}`, {
                        method: 'PUT',
                        headers: getHeaders(),
                        body: JSON.stringify(formData)
                    });
                } else {
                    response = await fetch(`${API_BASE}/projects`, {
                        method: 'POST',
                        headers: getHeaders(),
                        body: JSON.stringify(formData)
                    });
                }

                if (!response.ok) {
                    const result = await response.json();
                    if (response.status === 401) {
                        await handle401Error();
                        return;
                    }
                    throw new Error(result.error || 'Erreur lors de l\'enregistrement');
                }

                const result = await response.json();
                showToast(projectId ? 'Projet mis à jour avec succès' : 'Projet créé avec succès', 'success');
                closeProjectModal();
                loadProjects();
            } catch (error) {
                console.error('Erreur:', error);
                showToast(error.message || 'Erreur lors de l\'enregistrement du projet', 'error');
            }
        });
    }
});

function editProject(projectId) {
    openProjectModal(projectId);
}

function deleteProject(projectId) {
    showConfirmModal(
        'Supprimer le projet',
        'Êtes-vous sûr de vouloir supprimer ce projet ? Cette action est irréversible.',
        () => {
            performDeleteProject(projectId);
        }
    );
}

function performDeleteProject(projectId) {
    
    fetch(`${API_BASE}/projects/${projectId}`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                handle401Error();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Erreur lors de la suppression');
                });
            }
        }
        return response.json();
    })
    .then(data => {
        showToast('Projet supprimé avec succès', 'success');
        loadProjects();
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors de la suppression du projet', 'error');
    });
}

// ========== Services Management ==========
async function loadServices() {
    try {
        const response = await fetch(`${API_BASE}/services`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const services = await response.json();
        
        // Vérifier que services est un tableau
        if (!Array.isArray(services)) {
            console.error('Les services ne sont pas un tableau:', services);
            const servicesList = document.getElementById('services-list');
            if (servicesList) {
                servicesList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            }
            return;
        }
        
        // Stocker toutes les données
        allServicesData = services;
        
        // Filtrer et afficher
        filterAndDisplayServices();
    } catch (error) {
        console.error('Erreur lors du chargement des services:', error);
        showToast('Erreur lors du chargement des services. MongoDB est peut-être indisponible.', 'error');
        const servicesList = document.getElementById('services-list');
        if (servicesList) {
            servicesList.innerHTML = '<p>Aucun service disponible.</p>';
        }
    }
}

function createServiceCard(service) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    
    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1; display: flex; align-items: center; gap: 1rem;">
                ${service.icon ? `<img src="/static/${service.icon}" alt="${service.title}" style="width: 48px; height: 48px;">` : '<div style="width: 48px; height: 48px; background: var(--dark-bg); border-radius: 8px;"></div>'}
                <div>
                    <h3>${service.title || 'Sans titre'}</h3>
                    <p style="color: var(--gray); margin: 0.5rem 0;">${service.description ? service.description.substring(0, 150) + '...' : ''}</p>
                    <span style="font-size: 0.9rem; color: var(--gray);"><strong>Ordre:</strong> ${service.order || 0}</span>
                </div>
            </div>
            <div style="display: flex; gap: 0.5rem; margin-left: 1rem;">
                <button class="btn btn-sm btn-primary" onclick="editService('${service._id}')">Modifier</button>
                <button class="btn btn-sm btn-danger" onclick="deleteService('${service._id}')">Supprimer</button>
            </div>
        </div>
    `;
    return card;
}

function openServiceModal(serviceId = null) {
    const modal = document.getElementById('serviceModal');
    if (!modal) return;
    
    if (serviceId) {
        document.getElementById('serviceModalTitle').textContent = 'Modifier le service';
        loadServiceData(serviceId);
    } else {
        document.getElementById('serviceModalTitle').textContent = 'Nouveau service';
        document.getElementById('service-form').reset();
        document.getElementById('service-id').value = '';
        document.getElementById('service-order').value = '0';
    }
    
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.classList.add('open');
    }, 10);
    
    modal.addEventListener('click', function closeOnOverlay(e) {
        if (e.target === modal) {
            closeServiceModal();
            modal.removeEventListener('click', closeOnOverlay);
        }
    });
}

function closeServiceModal() {
    const modal = document.getElementById('serviceModal');
    if (!modal) return;
    modal.classList.remove('open');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

async function loadServiceData(serviceId) {
    try {
        const response = await fetch(`${API_BASE}/services`);
        const services = await response.json();
        const service = services.find(s => s._id === serviceId);
        
        if (service) {
            document.getElementById('service-id').value = service._id;
            document.getElementById('service-title').value = service.title || '';
            document.getElementById('service-description').value = service.description || '';
            document.getElementById('service-icon').value = service.icon || '';
            document.getElementById('service-order').value = service.order || 0;
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Attacher l'événement submit au formulaire de service
document.addEventListener('DOMContentLoaded', function() {
    const serviceForm = document.getElementById('service-form');
    if (serviceForm) {
        serviceForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const serviceId = document.getElementById('service-id').value;
        const formData = {
            title: document.getElementById('service-title').value,
            description: document.getElementById('service-description').value,
            icon: document.getElementById('service-icon').value,
            order: parseInt(document.getElementById('service-order').value) || 0
        };

        try {
            let response;
            if (serviceId) {
                response = await fetch(`${API_BASE}/services/${serviceId}`, {
                    method: 'PUT',
                    headers: getHeaders(),
                    body: JSON.stringify(formData)
                });
            } else {
                response = await fetch(`${API_BASE}/services`, {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(formData)
                });
            }

            if (!response.ok) {
                const result = await response.json();
                if (response.status === 401) {
                    await handle401Error();
                    return;
                }
                throw new Error(result.error || 'Erreur lors de l\'enregistrement');
            }

            const result = await response.json();
            showToast(serviceId ? 'Service mis à jour avec succès' : 'Service créé avec succès', 'success');
            closeServiceModal();
            loadServices();
        } catch (error) {
            console.error('Erreur:', error);
            showToast(error.message || 'Erreur lors de l\'enregistrement du service', 'error');
            }
        });
    }
});

function editService(serviceId) {
    openServiceModal(serviceId);
}

function deleteService(serviceId) {
    showConfirmModal(
        'Supprimer le service',
        'Êtes-vous sûr de vouloir supprimer ce service ? Cette action est irréversible.',
        () => {
            performDeleteService(serviceId);
        }
    );
}

function performDeleteService(serviceId) {
    
    fetch(`${API_BASE}/services/${serviceId}`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                handle401Error();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Erreur lors de la suppression');
                });
            }
        }
        return response.json();
    })
    .then(data => {
        showToast('Service supprimé avec succès', 'success');
        loadServices();
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors de la suppression du service', 'error');
    });
}

// ========== Contacts Management ==========
let allContacts = []; // Stocker tous les contacts pour le filtrage
let contactsCheckInterval = null; // Intervalle pour vérifier les nouveaux messages
let lastContactCheck = null; // Dernière vérification
let notificationPermission = false; // Permission pour les notifications navigateur

async function loadContacts() {
    try {
        const response = await fetch(`${API_BASE}/contacts`, {
            headers: getHeaders()
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const contacts = await response.json();
        
        const contactsList = document.getElementById('contacts-list');
        if (!contactsList) return;
        
        // Vérifier que contacts est un tableau
        if (!Array.isArray(contacts)) {
            console.error('Les contacts ne sont pas un tableau:', contacts);
            contactsList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            return;
        }
        
        // Stocker tous les contacts
        allContacts = contacts;
        
        // Mettre à jour le compteur
        updateContactsCount();
        
        // Appliquer le filtre actuel
        filterContacts();
    } catch (error) {
        console.error('Erreur lors du chargement des contacts:', error);
        showToast('Erreur lors du chargement des messages. MongoDB est peut-être indisponible.', 'error');
        const contactsList = document.getElementById('contacts-list');
        if (contactsList) {
            contactsList.innerHTML = '<p>Aucun message disponible.</p>';
        }
    }
}

function filterContacts() {
    const filterSelect = document.getElementById('contacts-filter');
    const filterValue = filterSelect ? filterSelect.value : 'all';
    const contactsList = document.getElementById('contacts-list');
    
    if (!contactsList) return;
    
    contactsList.innerHTML = '';
    
    // Filtrer les contacts selon la sélection
    let filteredContacts = allContacts;
    if (filterValue === 'unread') {
        filteredContacts = allContacts.filter(c => !c.read);
    } else if (filterValue === 'read') {
        filteredContacts = allContacts.filter(c => c.read);
    }
    
    if (filteredContacts.length === 0) {
        if (filterValue === 'all') {
            contactsList.innerHTML = '<p>Aucun message de contact reçu.</p>';
        } else if (filterValue === 'unread') {
            contactsList.innerHTML = '<p>Aucun message non lu.</p>';
        } else {
            contactsList.innerHTML = '<p>Aucun message lu.</p>';
        }
        return;
    }

    filteredContacts.forEach(contact => {
        const contactCard = createContactCard(contact);
        contactsList.appendChild(contactCard);
    });
}

function updateContactsCount() {
    const unreadCount = allContacts.filter(c => !c.read).length;
    const totalCount = allContacts.length;
    const unreadCountEl = document.getElementById('unread-count');
    
    if (unreadCountEl) {
        unreadCountEl.textContent = `${unreadCount} / ${totalCount}`;
        
        // Mettre à jour le badge dans le menu si nécessaire
        const contactsMenuBtn = document.querySelector('[data-section="contacts"]');
        if (contactsMenuBtn) {
            // Retirer l'ancien badge
            const oldBadge = contactsMenuBtn.querySelector('.badge');
            if (oldBadge) oldBadge.remove();
            
            // Ajouter un badge si il y a des messages non lus
            if (unreadCount > 0) {
                const badge = document.createElement('span');
                badge.className = 'badge';
                badge.textContent = unreadCount;
                badge.style.cssText = 'position: absolute; top: -5px; right: -5px; background: var(--green, #4DBA87); color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: bold;';
                contactsMenuBtn.style.position = 'relative';
                contactsMenuBtn.appendChild(badge);
            }
        }
    }
}

function createContactCard(contact) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    card.style.borderLeft = contact.read ? '4px solid var(--gray, #8B8B8B)' : '4px solid var(--green, #4DBA87)';
    
    const date = new Date(contact.created_at);
    const formattedDate = date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const readBadge = contact.read 
        ? '<span style="color: var(--gray); font-size: 0.85rem;">● Lu</span>' 
        : '<span style="color: var(--green); font-size: 0.85rem; font-weight: bold;">● Non lu</span>';
    
    card.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                        <h3 style="margin: 0;">${contact.subject || 'Sans sujet'}</h3>
                        ${readBadge}
                    </div>
                    <div style="color: var(--gray); font-size: 0.9rem; margin-bottom: 0.5rem;">
                        <p style="margin: 0.25rem 0;"><strong>De:</strong> ${contact.name} (<a href="mailto:${contact.email}" style="color: var(--green);">${contact.email}</a>)</p>
                        <p style="margin: 0.25rem 0;"><strong>Date:</strong> ${formattedDate}</p>
                    </div>
                    <div style="background: var(--dark-bg, #25262A); padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        <p style="color: var(--white, #FFFFFF); white-space: pre-wrap; margin: 0;">${contact.message || ''}</p>
                    </div>
                </div>
            </div>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="btn btn-sm ${contact.read ? 'btn-secondary' : 'btn-primary'}" onclick="toggleContactRead('${contact._id}', ${!contact.read})">
                    ${contact.read ? '<i class="fas fa-envelope"></i> Marquer non lu' : '<i class="fas fa-envelope-open"></i> Marquer lu'}
                </button>
                <a href="mailto:${contact.email}?subject=Re: ${encodeURIComponent(contact.subject)}" class="btn btn-sm btn-primary">
                    <i class="fas fa-reply"></i> Répondre
                </a>
                <button class="btn btn-sm btn-danger" onclick="deleteContact('${contact._id}')">
                    <i class="fas fa-trash"></i> Supprimer
                </button>
            </div>
        </div>
    `;
    return card;
}

async function toggleContactRead(contactId, readStatus) {
    try {
        const response = await fetch(`${API_BASE}/contacts/${contactId}/read`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ read: readStatus })
        });

        if (!response.ok) {
            const result = await response.json();
            if (response.status === 401) {
                await handle401Error();
                return;
            }
            throw new Error(result.error || 'Erreur lors de la mise à jour');
        }

        showToast(readStatus ? 'Message marqué comme lu' : 'Message marqué comme non lu', 'success');
        
        // Mettre à jour localement pour éviter un rechargement complet
        const contact = allContacts.find(c => c._id === contactId);
        if (contact) {
            contact.read = readStatus;
            updateContactsCount();
            filterContacts();
        } else {
            loadContacts();
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors de la mise à jour', 'error');
    }
}

function deleteContact(contactId) {
    showConfirmModal(
        'Supprimer le message',
        'Êtes-vous sûr de vouloir supprimer ce message de contact ? Cette action est irréversible.',
        () => {
            performDeleteContact(contactId);
        }
    );
}

function performDeleteContact(contactId) {
    
    fetch(`${API_BASE}/contacts/${contactId}`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                handle401Error();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Erreur lors de la suppression');
                });
            }
        }
        return response.json();
    })
    .then(data => {
        showToast('Message supprimé avec succès', 'success');
        
        // Retirer le contact de la liste locale
        allContacts = allContacts.filter(c => c._id !== contactId);
        updateContactsCount();
        filterContacts();
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors de la suppression du message', 'error');
    });
}

// ========== Toast Notifications ==========
function showToast(message, type = 'info') {
    // Créer ou réutiliser le conteneur de toast
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // Animation d'apparition
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Supprimer après 3 secondes
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== Notifications en temps réel ==========
function requestNotificationPermission() {
    // Demander la permission pour les notifications navigateur
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            notificationPermission = permission === 'granted';
            if (notificationPermission) {
                console.log('Permission de notification accordée');
            }
        });
    } else if ('Notification' in window && Notification.permission === 'granted') {
        notificationPermission = true;
    }
}

function showBrowserNotification(title, message, icon = null) {
    if (!notificationPermission || !('Notification' in window)) {
        return;
    }
    
    try {
        const notification = new Notification(title, {
            body: message,
            icon: icon || '/static/images/favicon.ico',
            badge: '/static/images/favicon.ico',
            tag: 'new-contact', // Évite les doublons
            requireInteraction: false
        });
        
        // Fermer automatiquement après 5 secondes
        setTimeout(() => {
            notification.close();
        }, 5000);
        
        // Action au clic
        notification.onclick = function() {
            window.focus();
            // Aller à la section contacts si on est sur la page admin
            if (window.location.pathname.includes('/admin')) {
                const contactsSection = document.querySelector('[data-section="contacts"]');
                if (contactsSection) {
                    contactsSection.click();
                }
            }
            notification.close();
        };
    } catch (error) {
        console.error('Erreur lors de l\'affichage de la notification:', error);
    }
}

async function checkNewContacts() {
    try {
        const response = await fetch(`${API_BASE}/contacts?read=false`, {
            headers: getHeaders()
        });
        
        if (!response.ok) {
            return; // Ignorer les erreurs silencieusement
        }
        
        const unreadContacts = await response.json();
        
        if (!Array.isArray(unreadContacts)) {
            return;
        }
        
        // Si c'est la première vérification, juste stocker le nombre
        if (lastContactCheck === null) {
            lastContactCheck = unreadContacts.length;
            return;
        }
        
        // Vérifier s'il y a de nouveaux messages
        const currentUnreadCount = unreadContacts.length;
        const newMessagesCount = currentUnreadCount - lastContactCheck;
        
        if (newMessagesCount > 0) {
            // Il y a de nouveaux messages !
            const latestContact = unreadContacts[0]; // Le plus récent
            
            // Notification toast
            showToast(
                `Nouveau message reçu de ${latestContact.name}: ${latestContact.subject || 'Sans sujet'}`,
                'success'
            );
            
            // Notification navigateur
            showBrowserNotification(
                'Nouveau message de contact',
                `${latestContact.name}: ${latestContact.subject || 'Nouveau message'}`,
                null
            );
            
            // Mettre à jour le titre de la page avec un indicateur
            updatePageTitle(newMessagesCount);
            
            // Recharger la liste si on est sur la section contacts
            const contactsSection = document.getElementById('section-contacts');
            if (contactsSection && contactsSection.style.display !== 'none') {
                loadContacts();
            } else {
                // Mettre à jour juste le compteur
                updateContactsCountFromAPI();
            }
        }
        
        lastContactCheck = currentUnreadCount;
    } catch (error) {
        // Ignorer les erreurs silencieusement pour ne pas polluer la console
        console.debug('Erreur lors de la vérification des nouveaux messages:', error);
    }
}

async function updateContactsCountFromAPI() {
    try {
        const response = await fetch(`${API_BASE}/contacts`, {
            headers: getHeaders()
        });
        
        if (!response.ok) return;
        
        const contacts = await response.json();
        if (Array.isArray(contacts)) {
            allContacts = contacts;
            updateContactsCount();
        }
    } catch (error) {
        // Ignorer silencieusement
    }
}

function updatePageTitle(unreadCount) {
    const baseTitle = document.title.replace(/^\(\d+\)\s*/, ''); // Retirer l'ancien compteur
    if (unreadCount > 0) {
        document.title = `(${unreadCount}) ${baseTitle}`;
    } else {
        document.title = baseTitle;
    }
}

function startContactsMonitoring() {
    // Vérifier toutes les 30 secondes
    if (contactsCheckInterval) {
        clearInterval(contactsCheckInterval);
    }
    
    contactsCheckInterval = setInterval(() => {
        checkNewContacts();
    }, 30000); // 30 secondes
    
    // Vérifier immédiatement après 5 secondes
    setTimeout(() => {
        checkNewContacts();
    }, 5000);
    
    // Mettre à jour l'icône du bouton
    updateNotificationButton();
}

function stopContactsMonitoring() {
    if (contactsCheckInterval) {
        clearInterval(contactsCheckInterval);
        contactsCheckInterval = null;
    }
}

function toggleNotifications() {
    const isMonitoring = contactsCheckInterval !== null;
    
    if (isMonitoring) {
        stopContactsMonitoring();
        showToast('Notifications désactivées', 'info');
    } else {
        startContactsMonitoring();
        requestNotificationPermission();
        showToast('Notifications activées', 'success');
    }
    
    updateNotificationButton();
}

function updateNotificationButton() {
    const btn = document.getElementById('notification-toggle');
    if (!btn) return;
    
    const isMonitoring = contactsCheckInterval !== null;
    const icon = btn.querySelector('i');
    
    if (isMonitoring) {
        btn.classList.add('btn-primary');
        btn.classList.remove('btn-secondary');
        btn.title = 'Notifications activées - Cliquer pour désactiver';
        if (icon) {
            icon.className = 'fas fa-bell';
        }
    } else {
        btn.classList.add('btn-secondary');
        btn.classList.remove('btn-primary');
        btn.title = 'Notifications désactivées - Cliquer pour activer';
        if (icon) {
            icon.className = 'fas fa-bell-slash';
        }
    }
}

// Arrêter la surveillance quand on quitte la page
window.addEventListener('beforeunload', () => {
    stopContactsMonitoring();
});

// ========== Gestion du Profil Admin ==========
async function loadProfile() {
    try {
        const response = await fetch(`${API_BASE}/admin/profile`, {
            headers: getHeaders()
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                await handle401Error();
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const profile = await response.json();
        
        // Remplir le formulaire
        document.getElementById('profile-username').value = profile.username || '';
        document.getElementById('profile-email').value = profile.email || '';
        document.getElementById('profile-full-name').value = profile.full_name || '';
    } catch (error) {
        console.error('Erreur lors du chargement du profil:', error);
        showToast('Erreur lors du chargement du profil', 'error');
    }
}

async function updateProfile(event) {
    event.preventDefault();
    
    const email = document.getElementById('profile-email').value.trim();
    const fullName = document.getElementById('profile-full-name').value.trim();
    
    try {
        const response = await fetch(`${API_BASE}/admin/profile`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({
                email: email,
                full_name: fullName
            })
        });
        
        if (!response.ok) {
            const result = await response.json();
            if (response.status === 401) {
                await handle401Error();
                return;
            }
            throw new Error(result.error || 'Erreur lors de la mise à jour');
        }
        
        const result = await response.json();
        showToast(result.message || 'Profil mis à jour avec succès', 'success');
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors de la mise à jour du profil', 'error');
    }
}

async function changePassword(event) {
    event.preventDefault();
    
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // Validation côté client
    if (newPassword !== confirmPassword) {
        showToast('Les mots de passe ne correspondent pas', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showToast('Le mot de passe doit contenir au moins 6 caractères', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/change-password`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword
            })
        });
        
        if (!response.ok) {
            const result = await response.json();
            if (response.status === 401) {
                await handle401Error();
                return;
            }
            throw new Error(result.error || 'Erreur lors du changement de mot de passe');
        }
        
        const result = await response.json();
        showToast(result.message || 'Mot de passe changé avec succès', 'success');
        resetPasswordForm();
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors du changement de mot de passe', 'error');
    }
}

function resetPasswordForm() {
    document.getElementById('password-form').reset();
}

async function loadLoginHistory() {
    try {
        const response = await fetch(`${API_BASE}/admin/login-history?limit=50`, {
            headers: getHeaders()
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                await handle401Error();
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const history = data.history || [];
        
        const historyList = document.getElementById('login-history-list');
        if (!historyList) return;
        
        historyList.innerHTML = '';
        
        if (history.length === 0) {
            historyList.innerHTML = '<p>Aucune connexion enregistrée.</p>';
            return;
        }
        
        history.forEach(entry => {
            const entryCard = createLoginHistoryCard(entry);
            historyList.appendChild(entryCard);
        });
    } catch (error) {
        console.error('Erreur lors du chargement de l\'historique:', error);
        showToast('Erreur lors du chargement de l\'historique', 'error');
        const historyList = document.getElementById('login-history-list');
        if (historyList) {
            historyList.innerHTML = '<p>Erreur lors du chargement de l\'historique.</p>';
        }
    }
}

function createLoginHistoryCard(entry) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    card.style.borderLeft = entry.success ? '4px solid var(--green, #4DBA87)' : '4px solid var(--red, #e74c3c)';
    
    const date = new Date(entry.login_time);
    const formattedDate = date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const statusBadge = entry.success 
        ? '<span style="color: var(--green); font-size: 0.85rem;">● Succès</span>' 
        : '<span style="color: var(--red); font-size: 0.85rem;">● Échec</span>';
    
    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                    <strong>${formattedDate}</strong>
                    ${statusBadge}
                </div>
                <div style="color: var(--gray); font-size: 0.9rem;">
                    <p style="margin: 0.25rem 0;"><strong>IP:</strong> ${entry.ip_address || 'N/A'}</p>
                    <p style="margin: 0.25rem 0;"><strong>Navigateur:</strong> ${entry.user_agent ? entry.user_agent.substring(0, 100) : 'N/A'}</p>
                </div>
            </div>
        </div>
    `;
    return card;
}

// ========== Variables globales pour pagination et recherche ==========
let currentSkillsPage = 1;
let skillsPerPage = 10;
let skillsSearchTerm = '';
let allSkillsData = [];

let currentPartnersPage = 1;
let partnersPerPage = 10;
let partnersSearchTerm = '';
let allPartnersData = [];

let currentProjectsPage = 1;
let projectsPerPage = 10;
let projectsSearchTerm = '';
let allProjectsData = [];

let currentServicesPage = 1;
let servicesPerPage = 10;
let servicesSearchTerm = '';
let allServicesData = [];

// ========== Initialisation des sections avec recherche et export ==========
function initSkillsSection() {
    createSearchBar('Rechercher une compétence...', (term) => {
        skillsSearchTerm = term.toLowerCase();
        currentSkillsPage = 1;
        filterAndDisplaySkills();
    }, 'skills-search-container');
    
    createExportButtons(
        () => exportSkillsJSON(),
        () => exportSkillsCSV(),
        'skills-export-container'
    );
    
    loadSkills();
}

function initPartnersSection() {
    createSearchBar('Rechercher un partenaire...', (term) => {
        partnersSearchTerm = term.toLowerCase();
        currentPartnersPage = 1;
        filterAndDisplayPartners();
    }, 'partners-search-container');
    
    createExportButtons(
        () => exportPartnersJSON(),
        () => exportPartnersCSV(),
        'partners-export-container'
    );
    
    loadPartners();
}

function initProjectsSection() {
    createSearchBar('Rechercher un projet...', (term) => {
        projectsSearchTerm = term.toLowerCase();
        currentProjectsPage = 1;
        filterAndDisplayProjects();
    }, 'projects-search-container');
    
    createExportButtons(
        () => exportProjectsJSON(),
        () => exportProjectsCSV(),
        'projects-export-container'
    );
    
    loadProjects();
}

function initServicesSection() {
    createSearchBar('Rechercher un service...', (term) => {
        servicesSearchTerm = term.toLowerCase();
        currentServicesPage = 1;
        filterAndDisplayServices();
    }, 'services-search-container');
    
    createExportButtons(
        () => exportServicesJSON(),
        () => exportServicesCSV(),
        'services-export-container'
    );
    
    loadServices();
}

// ========== Fonctions de filtrage et pagination pour Skills ==========
function filterAndDisplaySkills() {
    const skillsList = document.getElementById('skills-list');
    if (!skillsList) return;
    
    let filtered = allSkillsData;
    if (skillsSearchTerm) {
        filtered = allSkillsData.filter(skill => 
            (skill.title && skill.title.toLowerCase().includes(skillsSearchTerm)) ||
            (skill.description && skill.description.toLowerCase().includes(skillsSearchTerm))
        );
    }
    
    const totalPages = Math.ceil(filtered.length / skillsPerPage);
    const startIndex = (currentSkillsPage - 1) * skillsPerPage;
    const endIndex = startIndex + skillsPerPage;
    const paginatedSkills = filtered.slice(startIndex, endIndex);
    
    skillsList.innerHTML = '';
    
    if (paginatedSkills.length === 0) {
        skillsList.innerHTML = '<p>Aucune compétence trouvée.</p>';
    } else {
        paginatedSkills.forEach(skill => {
            const skillCard = createSkillCard(skill);
            skillsList.appendChild(skillCard);
        });
    }
    
    createPagination(currentSkillsPage, totalPages, (page) => {
        currentSkillsPage = page;
        filterAndDisplaySkills();
    }, 'skills-pagination');
}

function exportSkillsJSON() {
    exportToJSON(allSkillsData, `competences_${new Date().toISOString().split('T')[0]}.json`);
    showToast('Export JSON réussi', 'success');
}

function exportSkillsCSV() {
    const csvData = allSkillsData.map(skill => ({
        'Titre': skill.title || '',
        'Description': skill.description || '',
        'Icône': skill.icon || '',
        'Nombre de projets': skill.projects_count || 0,
        'Ordre': skill.order || 0
    }));
    exportToCSV(csvData, `competences_${new Date().toISOString().split('T')[0]}.csv`);
    showToast('Export CSV réussi', 'success');
}

// ========== Fonctions de filtrage et pagination pour Partners ==========
function filterAndDisplayPartners() {
    const partnersList = document.getElementById('partners-list');
    if (!partnersList) return;
    
    let filtered = allPartnersData;
    if (partnersSearchTerm) {
        filtered = allPartnersData.filter(partner => 
            (partner.name && partner.name.toLowerCase().includes(partnersSearchTerm))
        );
    }
    
    const totalPages = Math.ceil(filtered.length / partnersPerPage);
    const startIndex = (currentPartnersPage - 1) * partnersPerPage;
    const endIndex = startIndex + partnersPerPage;
    const paginatedPartners = filtered.slice(startIndex, endIndex);
    
    partnersList.innerHTML = '';
    
    if (paginatedPartners.length === 0) {
        partnersList.innerHTML = '<p>Aucun partenaire trouvé.</p>';
    } else {
        paginatedPartners.forEach(partner => {
            const partnerCard = createPartnerCard(partner);
            partnersList.appendChild(partnerCard);
        });
    }
    
    createPagination(currentPartnersPage, totalPages, (page) => {
        currentPartnersPage = page;
        filterAndDisplayPartners();
    }, 'partners-pagination');
}

function exportPartnersJSON() {
    exportToJSON(allPartnersData, `partenaires_${new Date().toISOString().split('T')[0]}.json`);
    showToast('Export JSON réussi', 'success');
}

function exportPartnersCSV() {
    const csvData = allPartnersData.map(partner => ({
        'Nom': partner.name || '',
        'Image': partner.image || ''
    }));
    exportToCSV(csvData, `partenaires_${new Date().toISOString().split('T')[0]}.csv`);
    showToast('Export CSV réussi', 'success');
}

// ========== Fonctions de filtrage et pagination pour Projects ==========
function filterAndDisplayProjects() {
    const projectsList = document.getElementById('projects-list');
    if (!projectsList) return;
    
    let filtered = allProjectsData;
    if (projectsSearchTerm) {
        filtered = allProjectsData.filter(project => 
            (project.title && project.title.toLowerCase().includes(projectsSearchTerm)) ||
            (project.description && project.description.toLowerCase().includes(projectsSearchTerm)) ||
            (project.technologies && project.technologies.toLowerCase().includes(projectsSearchTerm))
        );
    }
    
    const totalPages = Math.ceil(filtered.length / projectsPerPage);
    const startIndex = (currentProjectsPage - 1) * projectsPerPage;
    const endIndex = startIndex + projectsPerPage;
    const paginatedProjects = filtered.slice(startIndex, endIndex);
    
    projectsList.innerHTML = '';
    
    if (paginatedProjects.length === 0) {
        projectsList.innerHTML = '<p>Aucun projet trouvé.</p>';
    } else {
        paginatedProjects.forEach(project => {
            const projectCard = createProjectCard(project);
            projectsList.appendChild(projectCard);
        });
    }
    
    createPagination(currentProjectsPage, totalPages, (page) => {
        currentProjectsPage = page;
        filterAndDisplayProjects();
    }, 'projects-pagination');
}

function exportProjectsJSON() {
    exportToJSON(allProjectsData, `projets_${new Date().toISOString().split('T')[0]}.json`);
    showToast('Export JSON réussi', 'success');
}

function exportProjectsCSV() {
    const csvData = allProjectsData.map(project => ({
        'Titre': project.title || '',
        'Description': project.description || '',
        'Technologies': project.technologies || '',
        'Lien': project.link || '',
        'GitHub': project.github_link || '',
        'Statut': project.status || '',
        'Ordre': project.order || 0
    }));
    exportToCSV(csvData, `projets_${new Date().toISOString().split('T')[0]}.csv`);
    showToast('Export CSV réussi', 'success');
}

// ========== Fonctions de filtrage et pagination pour Services ==========
function filterAndDisplayServices() {
    const servicesList = document.getElementById('services-list');
    if (!servicesList) return;
    
    let filtered = allServicesData;
    if (servicesSearchTerm) {
        filtered = allServicesData.filter(service => 
            (service.title && service.title.toLowerCase().includes(servicesSearchTerm)) ||
            (service.description && service.description.toLowerCase().includes(servicesSearchTerm))
        );
    }
    
    const totalPages = Math.ceil(filtered.length / servicesPerPage);
    const startIndex = (currentServicesPage - 1) * servicesPerPage;
    const endIndex = startIndex + servicesPerPage;
    const paginatedServices = filtered.slice(startIndex, endIndex);
    
    servicesList.innerHTML = '';
    
    if (paginatedServices.length === 0) {
        servicesList.innerHTML = '<p>Aucun service trouvé.</p>';
    } else {
        paginatedServices.forEach(service => {
            const serviceCard = createServiceCard(service);
            servicesList.appendChild(serviceCard);
        });
    }
    
    createPagination(currentServicesPage, totalPages, (page) => {
        currentServicesPage = page;
        filterAndDisplayServices();
    }, 'services-pagination');
}

function exportServicesJSON() {
    exportToJSON(allServicesData, `services_${new Date().toISOString().split('T')[0]}.json`);
    showToast('Export JSON réussi', 'success');
}

function exportServicesCSV() {
    const csvData = allServicesData.map(service => ({
        'Titre': service.title || '',
        'Description': service.description || '',
        'Icône': service.icon || '',
        'Ordre': service.order || 0
    }));
    exportToCSV(csvData, `services_${new Date().toISOString().split('T')[0]}.csv`);
    showToast('Export CSV réussi', 'success');
}

