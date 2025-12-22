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
        
        const skillsList = document.getElementById('skills-list');
        skillsList.innerHTML = '';
        
        // Vérifier que skills est un tableau
        if (!Array.isArray(skills)) {
            console.error('Les compétences ne sont pas un tableau:', skills);
            skillsList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            return;
        }
        
        if (skills.length === 0) {
            skillsList.innerHTML = '<p>Aucune compétence enregistrée.</p>';
            return;
        }

        skills.forEach(skill => {
            const skillCard = createSkillCard(skill);
            skillsList.appendChild(skillCard);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des compétences:', error);
        showToast('Erreur lors du chargement des compétences. MongoDB est peut-être indisponible.', 'error');
        document.getElementById('skills-list').innerHTML = '<p>Aucune compétence disponible.</p>';
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
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette compétence ?')) {
        return;
    }

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
        
        const partnersList = document.getElementById('partners-list');
        partnersList.innerHTML = '';
        
        // Vérifier que partners est un tableau
        if (!Array.isArray(partners)) {
            console.error('Les partenaires ne sont pas un tableau:', partners);
            partnersList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            return;
        }
        
        if (partners.length === 0) {
            partnersList.innerHTML = '<p>Aucun partenaire enregistré.</p>';
            return;
        }

        partners.forEach(partner => {
            const partnerCard = createPartnerCard(partner);
            partnersList.appendChild(partnerCard);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des partenaires:', error);
        showToast('Erreur lors du chargement des partenaires. MongoDB est peut-être indisponible.', 'error');
        document.getElementById('partners-list').innerHTML = '<p>Aucun partenaire disponible.</p>';
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
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce partenaire ?')) {
        return;
    }

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
        
        const projectsList = document.getElementById('projects-list');
        if (!projectsList) return;
        
        projectsList.innerHTML = '';
        
        // Vérifier que projects est un tableau
        if (!Array.isArray(projects)) {
            console.error('Les projets ne sont pas un tableau:', projects);
            projectsList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            return;
        }
        
        if (projects.length === 0) {
            projectsList.innerHTML = '<p>Aucun projet enregistré.</p>';
            return;
        }

        projects.forEach(project => {
            const projectCard = createProjectCard(project);
            projectsList.appendChild(projectCard);
        });
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
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce projet ?')) {
        return;
    }
    
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
        
        const servicesList = document.getElementById('services-list');
        if (!servicesList) return;
        
        servicesList.innerHTML = '';
        
        // Vérifier que services est un tableau
        if (!Array.isArray(services)) {
            console.error('Les services ne sont pas un tableau:', services);
            servicesList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            return;
        }
        
        if (services.length === 0) {
            servicesList.innerHTML = '<p>Aucun service enregistré.</p>';
            return;
        }

        services.forEach(service => {
            const serviceCard = createServiceCard(service);
            servicesList.appendChild(serviceCard);
        });
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
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce service ?')) {
        return;
    }
    
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
        
        contactsList.innerHTML = '';
        
        // Vérifier que contacts est un tableau
        if (!Array.isArray(contacts)) {
            console.error('Les contacts ne sont pas un tableau:', contacts);
            contactsList.innerHTML = '<p>Erreur: Format de données invalide.</p>';
            return;
        }
        
        if (contacts.length === 0) {
            contactsList.innerHTML = '<p>Aucun message de contact reçu.</p>';
            return;
        }

        contacts.forEach(contact => {
            const contactCard = createContactCard(contact);
            contactsList.appendChild(contactCard);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des contacts:', error);
        showToast('Erreur lors du chargement des messages. MongoDB est peut-être indisponible.', 'error');
        const contactsList = document.getElementById('contacts-list');
        if (contactsList) {
            contactsList.innerHTML = '<p>Aucun message disponible.</p>';
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
        loadContacts();
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors de la mise à jour', 'error');
    }
}

function deleteContact(contactId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {
        return;
    }
    
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
        loadContacts();
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

