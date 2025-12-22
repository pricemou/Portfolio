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
function showSection(sectionName) {
    if (!sectionName) return;
    
    // Masquer toutes les sections
    const allSections = document.querySelectorAll('.content-section');
    allSections.forEach(section => {
        section.style.display = 'none';
        section.classList.remove('active-section');
    });
    
    // Afficher la section demandée
    const targetSection = document.getElementById(`section-${sectionName}`);
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.add('active-section');
    }
    
    // Mettre à jour le menu actif
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-section') === sectionName) {
            item.classList.add('active');
        }
    });
    
    // Mettre à jour le titre de la page
    const pageTitle = document.getElementById('current-page');
    if (pageTitle) {
        const activeItem = document.querySelector(`[data-section="${sectionName}"]`);
        pageTitle.textContent = activeItem ? (activeItem.getAttribute('aria-label') || sectionName) : 'Dashboard';
    }
    
    // Charger les données de la section si nécessaire
    if (sectionName === 'skills') initSkillsSection();
    else if (sectionName === 'partners') initPartnersSection();
    else if (sectionName === 'projects') initProjectsSection();
    else if (sectionName === 'services') initServicesSection();
    else if (sectionName === 'contacts') loadContacts();
    else if (sectionName === 'homepage') loadHomepageData();
}

// Initialiser la navigation
document.addEventListener('DOMContentLoaded', () => {
    // Gérer les clics sur les éléments du menu
    const menuItems = document.querySelectorAll('.menu-item[data-section]');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            if (section) {
                showSection(section);
            }
        });
    });
    
    // Charger les données initiales
    loadHomepageData();
    loadSkills();
    loadPartners();
    loadProjects();
    loadServices();
    loadContacts();
    
    // Vérifier l'état MongoDB
    checkMongoDBStatus();
});

// ========== Vérification MongoDB ==========
async function checkMongoDBStatus() {
    setTimeout(async () => {
        try {
            const response = await fetch(`${API_BASE}/admin/mongo-status`, {
                headers: getHeaders(),
                credentials: 'include'
            });
            
            if (response.ok) {
                const status = await response.json();
                if (status.connection_status !== 'connected') {
                    showMongoDBWarningBanner();
                }
            } else {
                // Fallback : tester une API simple
                const testResponse = await fetch(`${API_BASE}/skills`);
                if (!testResponse.ok) {
                    const data = await testResponse.json().catch(() => ({}));
                    if (data.error === 'MongoDB non disponible' || testResponse.status === 503) {
                        showMongoDBWarningBanner();
                    }
                }
            }
        } catch (error) {
            // Ignorer les erreurs silencieusement
        }
    }, 2000);
}

function showMongoDBWarningBanner() {
    if (document.getElementById('mongodb-config-warning')) return;
    
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
    `;
    
    banner.innerHTML = `
        <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 2rem;">
            <div style="flex: 1;">
                <strong style="font-size: 1.2rem; display: block; margin-bottom: 0.5rem;">⚠️ URGENT : MongoDB non configuré</strong>
                <p style="margin: 0; font-size: 0.95rem; opacity: 0.95; line-height: 1.5;">
                    La variable <code style="background: rgba(255,255,255,0.25); padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold;">MONGO_URI</code> n'est pas définie en production.
                    Les données ne peuvent pas être chargées.
                </p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">
                    <strong>Solution :</strong> PythonAnywhere → Web → votre app → "Environment variables" → Ajoutez MONGO_URI → Redémarrez
                </p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">
                    📚 Guide : <code style="background: rgba(255,255,255,0.2); padding: 0.15rem 0.4rem; border-radius: 3px;">CONFIGURER_MONGO_URI.md</code>
                </p>
            </div>
            <button onclick="document.getElementById('mongodb-config-warning').remove(); const mainContent = document.querySelector('.main-content'); if(mainContent) mainContent.style.paddingTop = '0';" 
                    style="background: rgba(255,255,255,0.25); border: 2px solid rgba(255,255,255,0.4); 
                           color: white; padding: 0.6rem 1.2rem; border-radius: 5px; cursor: pointer; font-weight: bold;">
                ✕ Fermer
            </button>
        </div>
    `;
    
    document.body.insertBefore(banner, document.body.firstChild);
    
    // Ajuster le padding du contenu principal
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.style.paddingTop = '120px';
    }
}

// ========== Homepage Management ==========
async function loadHomepageData() {
    try {
        const response = await fetch(`${API_BASE}/homepage`);
        if (response.ok) {
            const data = await response.json();
            if (data.badge) document.getElementById('homepage-badge').value = data.badge || '';
            if (data.title_line1) document.getElementById('homepage-title1').value = data.title_line1 || '';
            if (data.title_line2) document.getElementById('homepage-title2').value = data.title_line2 || '';
            if (data.description) document.getElementById('homepage-description').value = data.description || '';
            if (data.email) document.getElementById('homepage-email').value = data.email || '';
            if (data.cta_text) document.getElementById('homepage-cta').value = data.cta_text || '';
            if (data.about_title) document.getElementById('homepage-about-title').value = data.about_title || '';
            if (data.about_name) document.getElementById('homepage-about-name').value = data.about_name || '';
            if (data.about_subtitle) document.getElementById('homepage-about-subtitle').value = data.about_subtitle || '';
            if (data.about_description) document.getElementById('homepage-about-description').value = data.about_description || '';
        }
    } catch (error) {
        console.error('Erreur lors du chargement de la homepage:', error);
    }
}

// ========== Skills Management ==========
let allSkillsData = [];

async function loadSkills() {
    try {
        const response = await fetch(`${API_BASE}/skills`);
        
        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: 'Erreur serveur', message: `Erreur HTTP ${response.status}` };
            }
            
            const skillsList = document.getElementById('skills-list');
            if (skillsList) {
                skillsList.innerHTML = `
                    <div style="padding: 2rem; text-align: center; background: rgba(220, 53, 69, 0.1); border: 2px solid #dc3545; border-radius: 8px;">
                        <p style="font-size: 1.3rem; margin-bottom: 1rem; color: #dc3545; font-weight: bold;">⚠️ Base de données non disponible</p>
                        <p style="color: var(--gray); margin-bottom: 1rem;">${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                        <p style="color: var(--gray); font-size: 0.9rem;">
                            Configurez <code style="background: rgba(0,0,0,0.2); padding: 0.2rem 0.4rem; border-radius: 3px;">MONGO_URI</code> dans les variables d'environnement.
                        </p>
                    </div>
                `;
            }
            showMongoDBWarningBanner();
            return;
        }
        
        const data = await response.json();
        allSkillsData = Array.isArray(data) ? data : [];
        displaySkills(allSkillsData);
    } catch (error) {
        console.error('Erreur lors du chargement des compétences:', error);
    }
}

function displaySkills(skills) {
    const skillsList = document.getElementById('skills-list');
    if (!skillsList) return;
    
    if (skills.length === 0) {
        skillsList.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 2rem;">Aucune compétence trouvée.</p>';
        return;
    }
    
    skillsList.innerHTML = skills.map(skill => `
        <div class="admin-card" style="margin-bottom: 1rem;">
            <h3>${skill.title || 'Sans titre'}</h3>
            <p>${skill.description || ''}</p>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="btn btn-secondary btn-sm" onclick="editSkill('${skill._id}')">Modifier</button>
                <button class="btn btn-danger btn-sm" onclick="deleteSkill('${skill._id}')">Supprimer</button>
            </div>
        </div>
    `).join('');
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
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette compétence ?')) return;
    console.log('Supprimer compétence:', skillId);
    if (typeof window.showToast === 'function') {
        window.showToast('Fonctionnalité à implémenter', 'info');
    }
}

// ========== Partners Management ==========
let allPartnersData = [];

async function loadPartners() {
    try {
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
                    <div style="padding: 2rem; text-align: center; background: rgba(220, 53, 69, 0.1); border: 2px solid #dc3545; border-radius: 8px;">
                        <p style="font-size: 1.3rem; margin-bottom: 1rem; color: #dc3545; font-weight: bold;">⚠️ Base de données non disponible</p>
                        <p style="color: var(--gray); margin-bottom: 1rem;">${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            showMongoDBWarningBanner();
            return;
        }
        
        const data = await response.json();
        allPartnersData = Array.isArray(data) ? data : [];
        displayPartners(allPartnersData);
    } catch (error) {
        console.error('Erreur lors du chargement des partenaires:', error);
    }
}

function displayPartners(partners) {
    const partnersList = document.getElementById('partners-list');
    if (!partnersList) return;
    
    if (partners.length === 0) {
        partnersList.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 2rem;">Aucun partenaire trouvé.</p>';
        return;
    }
    
    partnersList.innerHTML = partners.map(partner => `
        <div class="admin-card" style="margin-bottom: 1rem;">
            <h3>${partner.name || 'Sans nom'}</h3>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="btn btn-secondary btn-sm" onclick="editPartner('${partner._id}')">Modifier</button>
                <button class="btn btn-danger btn-sm" onclick="deletePartner('${partner._id}')">Supprimer</button>
            </div>
        </div>
    `).join('');
}

function initPartnersSection() {
    loadPartners();
}

function editPartner(partnerId) {
    console.log('Modifier partenaire:', partnerId);
}

function deletePartner(partnerId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce partenaire ?')) return;
    console.log('Supprimer partenaire:', partnerId);
}

// ========== Projects Management ==========
let allProjectsData = [];

async function loadProjects() {
    try {
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
                    <div style="padding: 2rem; text-align: center; background: rgba(220, 53, 69, 0.1); border: 2px solid #dc3545; border-radius: 8px;">
                        <p style="font-size: 1.3rem; margin-bottom: 1rem; color: #dc3545; font-weight: bold;">⚠️ Base de données non disponible</p>
                        <p style="color: var(--gray); margin-bottom: 1rem;">${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            showMongoDBWarningBanner();
            return;
        }
        
        const data = await response.json();
        allProjectsData = Array.isArray(data) ? data : [];
        displayProjects(allProjectsData);
    } catch (error) {
        console.error('Erreur lors du chargement des projets:', error);
    }
}

function displayProjects(projects) {
    const projectsList = document.getElementById('projects-list');
    if (!projectsList) return;
    
    if (projects.length === 0) {
        projectsList.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 2rem;">Aucun projet trouvé.</p>';
        return;
    }
    
    projectsList.innerHTML = projects.map(project => `
        <div class="admin-card" style="margin-bottom: 1rem;">
            <h3>${project.title || 'Sans titre'}</h3>
            <p>${project.description || ''}</p>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="btn btn-secondary btn-sm" onclick="editProject('${project._id}')">Modifier</button>
                <button class="btn btn-danger btn-sm" onclick="deleteProject('${project._id}')">Supprimer</button>
            </div>
        </div>
    `).join('');
}

function initProjectsSection() {
    loadProjects();
}

function editProject(projectId) {
    console.log('Modifier projet:', projectId);
}

function deleteProject(projectId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce projet ?')) return;
    console.log('Supprimer projet:', projectId);
}

// ========== Services Management ==========
let allServicesData = [];

async function loadServices() {
    try {
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
                    <div style="padding: 2rem; text-align: center; background: rgba(220, 53, 69, 0.1); border: 2px solid #dc3545; border-radius: 8px;">
                        <p style="font-size: 1.3rem; margin-bottom: 1rem; color: #dc3545; font-weight: bold;">⚠️ Base de données non disponible</p>
                        <p style="color: var(--gray); margin-bottom: 1rem;">${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                    </div>
                `;
            }
            showMongoDBWarningBanner();
            return;
        }
        
        const data = await response.json();
        allServicesData = Array.isArray(data) ? data : [];
        displayServices(allServicesData);
    } catch (error) {
        console.error('Erreur lors du chargement des services:', error);
    }
}

function displayServices(services) {
    const servicesList = document.getElementById('services-list');
    if (!servicesList) return;
    
    if (services.length === 0) {
        servicesList.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 2rem;">Aucun service trouvé.</p>';
        return;
    }
    
    servicesList.innerHTML = services.map(service => `
        <div class="admin-card" style="margin-bottom: 1rem;">
            <h3>${service.title || 'Sans titre'}</h3>
            <p>${service.description || ''}</p>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="btn btn-secondary btn-sm" onclick="editService('${service._id}')">Modifier</button>
                <button class="btn btn-danger btn-sm" onclick="deleteService('${service._id}')">Supprimer</button>
            </div>
        </div>
    `).join('');
}

function initServicesSection() {
    loadServices();
}

function editService(serviceId) {
    console.log('Modifier service:', serviceId);
}

function deleteService(serviceId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce service ?')) return;
    console.log('Supprimer service:', serviceId);
}

// ========== Contacts Management ==========
let allContacts = [];

async function loadContacts() {
    try {
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
                <div style="padding: 2rem; text-align: center; background: rgba(220, 53, 69, 0.1); border: 2px solid #dc3545; border-radius: 8px;">
                    <p style="font-size: 1.3rem; margin-bottom: 1rem; color: #dc3545; font-weight: bold;">⚠️ Base de données non disponible</p>
                    <p style="color: var(--gray); margin-bottom: 1rem;">${errorData.message || 'La connexion à MongoDB n\'est pas configurée.'}</p>
                </div>
            `;
            showMongoDBWarningBanner();
            return;
        }
        
        const data = await response.json();
        allContacts = Array.isArray(data) ? data : [];
        displayContacts(allContacts);
    } catch (error) {
        console.error('Erreur lors du chargement des contacts:', error);
    }
}

function displayContacts(contacts) {
    const contactsList = document.getElementById('contacts-list');
    if (!contactsList) return;
    
    if (contacts.length === 0) {
        contactsList.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 2rem;">Aucun message de contact trouvé.</p>';
        return;
    }
    
    contactsList.innerHTML = contacts.map(contact => `
        <div class="admin-card" style="margin-bottom: 1rem;">
            <h3>${contact.name || 'Sans nom'} - ${contact.email || 'Sans email'}</h3>
            <p>${contact.message || ''}</p>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="btn btn-secondary btn-sm" onclick="markContactRead('${contact._id}')">Marquer comme lu</button>
                <button class="btn btn-danger btn-sm" onclick="deleteContact('${contact._id}')">Supprimer</button>
            </div>
        </div>
    `).join('');
}

function markContactRead(contactId) {
    console.log('Marquer contact comme lu:', contactId);
}

function deleteContact(contactId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) return;
    console.log('Supprimer contact:', contactId);
}
