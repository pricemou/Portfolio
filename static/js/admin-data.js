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
    
    // Masquer toutes les sections (stats/graphiques restent dans #section-dashboard uniquement)
    const allSections = document.querySelectorAll('.content-section');
    if (allSections.length === 0) {
        console.warn('Aucune section avec la classe content-section trouvée');
        return;
    }
    
    allSections.forEach(section => {
        section.classList.remove('active-section');
        section.style.display = 'none';
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
    
    // Charger les données de la section courante uniquement
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
        if (typeof load2FAStatus === 'function') {
            load2FAStatus();
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
    } else if (sectionName === 'career') {
        if (typeof loadCareerAdmin === 'function') {
            loadCareerAdmin();
        }
    } else if (sectionName === 'certifications') {
        if (typeof loadCertsAdmin === 'function') {
            loadCertsAdmin();
        }
    } else if (sectionName === 'legal') {
        if (typeof loadLegalPage === 'function') {
            loadLegalPage();
        }
    } else if (sectionName === 'media') {
        if (typeof loadMediaAdmin === 'function') {
            loadMediaAdmin();
        }
    } else if (sectionName === 'trash') {
        if (typeof loadTrashAdmin === 'function') {
            loadTrashAdmin();
        }
    } else if (sectionName === 'audit') {
        if (typeof loadAuditAdmin === 'function') {
            loadAuditAdmin();
        }
    }

    const searchInput = document.getElementById('admin-global-search');
    if (searchInput && searchInput.value.trim() && typeof filterActiveAdminSection === 'function') {
        setTimeout(() => filterActiveAdminSection(searchInput.value.trim().toLowerCase()), 120);
    }
}

// Initialiser la navigation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Section active depuis la route serveur (/admin/<section>)
    const sectionFromRoute = (document.body.dataset.activeSection || 'dashboard').trim();
    const validSections = [
        'dashboard', 'homepage', 'skills', 'partners',
        'projects', 'services', 'career', 'certifications',
        'contacts', 'media', 'trash', 'audit', 'legal',
        'profile', 'admins'
    ];
    const currentSection = validSections.includes(sectionFromRoute) ? sectionFromRoute : 'dashboard';

    // Afficher uniquement la section de la route + charger ses données
    showSection(currentSection);

    // Mettre à jour l'état actif du menu
    document.querySelectorAll('.menu-item[data-section]').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-section') === currentSection);
    });
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
            updateHomepagePreview();
        }
    } catch (error) {
        console.error('Erreur lors du chargement des données homepage:', error);
            showToast('Erreur lors du chargement des données. La base de données est peut-être indisponible.', 'error');
    }
}

function updateHomepagePreview() {
    const setText = (id, value, fallback) => {
        const el = document.getElementById(id);
        if (!el) return;
        const text = (value || '').trim();
        el.textContent = text || fallback;
    };

    const badge = document.getElementById('homepage-badge');
    const title1 = document.getElementById('homepage-title1');
    const title2 = document.getElementById('homepage-title2');
    const description = document.getElementById('homepage-description');
    const cta = document.getElementById('homepage-cta');

    setText('homepage-preview-badge', badge && badge.value, 'Badge');
    setText('homepage-preview-title1', title1 && title1.value, 'Titre ligne 1');
    setText('homepage-preview-title2', title2 && title2.value, 'Titre ligne 2');
    setText('homepage-preview-description', description && description.value, 'La description du hero apparaîtra ici.');
    setText('homepage-preview-cta', cta && cta.value, 'Me contacter');
}

// Attacher l'événement submit au formulaire homepage
document.addEventListener('DOMContentLoaded', function() {
    const homepageForm = document.getElementById('homepage-form');
    if (homepageForm) {
        homepageForm.addEventListener('input', updateHomepagePreview);
        updateHomepagePreview();

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
    const renderList = (skill) => `
        <div class="admin-card">
            <div class="admin-card-row">
                <div class="admin-card-main">
                    <h3>${skill.title || 'Sans titre'}</h3>
                    <p>${skill.description || ''}</p>
                    <div class="admin-card-meta">
                        <span><strong>Projets:</strong> ${skill.projects_count || 0}</span>
                        <span><strong>Ordre:</strong> ${skill.order || 0}</span>
                    </div>
                </div>
                <div class="admin-card-actions">
                    <button class="btn btn-sm btn-ghost" onclick="editSkill('${skill._id}')"><i class="fas fa-edit"></i> Modifier</button>
                    <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteSkill('${skill._id}')"><i class="fas fa-trash"></i> Supprimer</button>
                </div>
            </div>
        </div>
    `;
    const renderGrid = (skill) => {
        const initial = (skill.title || 'C').trim().charAt(0).toUpperCase();
        return `
            <article class="admin-grid-card">
                <div class="admin-grid-card-icon">${initial}</div>
                <h3 class="admin-grid-card-title">${skill.title || 'Sans titre'}</h3>
                <p class="admin-grid-card-text">${skill.description || ''}</p>
                <div class="admin-card-meta">
                    <span>${skill.projects_count || 0} projets</span>
                    <span>Ordre ${skill.order || 0}</span>
                </div>
                <div class="admin-card-actions">
                    <button class="btn btn-sm btn-ghost" onclick="editSkill('${skill._id}')"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteSkill('${skill._id}')"><i class="fas fa-trash"></i></button>
                </div>
            </article>
        `;
    };
    setAdminListItems('skills', skills, {
        listId: 'skills-list',
        paginationId: 'skills-pagination',
        countId: 'skills-count-label',
        listBtnId: 'skills-view-list',
        gridBtnId: 'skills-view-grid',
        emptyHtml: '<p class="admin-empty">Aucune compétence disponible.</p>',
        countLabel: (n) => (n === 1 ? '1 compétence' : `${n} compétences`),
        renderList,
        renderGrid,
    });
}

function initSkillsSection() {
    loadSkills();
    const skillForm = document.getElementById('skill-form');
    if (skillForm && !skillForm.dataset.bound) {
        skillForm.addEventListener('submit', handleSkillSubmit);
        skillForm.dataset.bound = '1';
    }
}

function openModalEl(modal) {
    if (!modal) return;
    modal.classList.remove('is-closing');
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    // Force reflow so enter transition plays
    void modal.offsetWidth;
    requestAnimationFrame(() => {
        modal.classList.add('open');
        modal.style.opacity = '1';
    });
}

function closeModalEl(modal) {
    if (!modal) return;
    modal.classList.remove('open');
    modal.classList.add('is-closing');
    modal.style.opacity = '0';
    modal.setAttribute('aria-hidden', 'true');
    window.setTimeout(() => {
        if (!modal.classList.contains('open')) {
            modal.style.display = 'none';
            modal.classList.remove('is-closing');
        }
    }, 240);
}

window.openModalEl = openModalEl;
window.closeModalEl = closeModalEl;

window.openSkillModal = function openSkillModal() {
    const modal = document.getElementById('skillModal');
    const modalTitle = document.getElementById('skillModalTitle');
    const skillIdInput = document.getElementById('skill-id');
    const form = document.getElementById('skill-form');
    openModalEl(modal);
    if (modalTitle) modalTitle.textContent = 'Nouvelle compétence';
    if (skillIdInput) skillIdInput.value = '';
    if (form) {
        form.reset();
        const orderInput = document.getElementById('skill-order');
        const projectsInput = document.getElementById('skill-projects');
        if (orderInput) orderInput.value = '1';
        if (projectsInput) projectsInput.value = '0';
    }
    setTimeout(() => document.getElementById('skill-title')?.focus(), 100);
};

window.closeSkillModal = function closeSkillModal() {
    const modal = document.getElementById('skillModal');
    closeModalEl(modal);
    const form = document.getElementById('skill-form');
    if (form) form.reset();
    const skillIdInput = document.getElementById('skill-id');
    if (skillIdInput) skillIdInput.value = '';
};

window.editSkill = function editSkill(skillId) {
    const skill = allSkillsData.find(s => String(s._id) === String(skillId));
    if (!skill) {
        showToast('Compétence non trouvée', 'error');
        return;
    }
    const modal = document.getElementById('skillModal');
    openModalEl(modal);
    const modalTitle = document.getElementById('skillModalTitle');
    if (modalTitle) modalTitle.textContent = 'Modifier la compétence';
    const setVal = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.value = value ?? '';
    };
    setVal('skill-id', skillId);
    setVal('skill-title', skill.title || '');
    setVal('skill-icon', skill.icon || '');
    setVal('skill-description', skill.description || '');
    setVal('skill-projects', skill.projects_count ?? 0);
    setVal('skill-order', skill.order ?? 0);
    setTimeout(() => document.getElementById('skill-title')?.focus(), 100);
};

async function handleSkillSubmit(event) {
    event.preventDefault();
    const skillId = document.getElementById('skill-id')?.value?.trim();
    const payload = {
        title: document.getElementById('skill-title')?.value?.trim() || '',
        icon: document.getElementById('skill-icon')?.value?.trim() || '',
        description: document.getElementById('skill-description')?.value?.trim() || '',
        projects_count: parseInt(document.getElementById('skill-projects')?.value || '0', 10) || 0,
        order: parseInt(document.getElementById('skill-order')?.value || '0', 10) || 0,
    };
    if (!payload.title || !payload.description) {
        showToast('Titre et description requis', 'error');
        return;
    }
    try {
        const url = skillId ? `${API_BASE}/skills/${skillId}` : `${API_BASE}/skills`;
        const method = skillId ? 'PUT' : 'POST';
        const response = await fetch(url, {
            method,
            headers: getHeaders(),
            credentials: 'same-origin',
            body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok && data.success !== false) {
            showToast(skillId ? 'Compétence mise à jour' : 'Compétence créée', 'success');
            closeSkillModal();
            loadSkills();
        } else {
            showToast(data.error || 'Erreur lors de l’enregistrement', 'error');
        }
    } catch (error) {
        console.error('Erreur skill submit:', error);
        showToast('Erreur lors de l’enregistrement', 'error');
    }
}

window.deleteSkill = async function deleteSkill(skillId) {
    const ok = await adminConfirm({
        title: 'Supprimer cette compétence ?',
        message: 'Elle disparaîtra de la page d’accueil et des sections associées.',
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!ok) return;
    try {
        const response = await fetch(`${API_BASE}/skills/${skillId}`, {
            method: 'DELETE',
            headers: getHeaders(),
            credentials: 'same-origin',
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok && data.success) {
            showToast('Compétence supprimée', 'success');
            loadSkills();
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
};

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

function partnerImageSrc(partner) {
    const img = partner.image || partner.logo || '';
    if (!img) return '';
    if (/^https?:\/\//i.test(img) || img.startsWith('/')) return img;
    return `/static/${img.replace(/^\//, '')}`;
}

function displayPartners(partners) {
    const renderList = (partner) => {
        const src = partnerImageSrc(partner);
        return `
            <div class="admin-card">
                <div class="admin-card-row">
                    <div class="admin-card-main admin-card-main--media">
                        ${src ? `<img class="admin-list-thumb" src="${src}" alt="" loading="lazy">` : '<div class="admin-list-thumb admin-list-thumb--empty"><i class="fas fa-handshake"></i></div>'}
                        <div>
                            <h3>${partner.name || 'Sans nom'}</h3>
                            <div class="admin-card-meta">
                                <span>${partner.period || '—'}</span>
                                <span><strong>Ordre:</strong> ${partner.order || 0}</span>
                            </div>
                        </div>
                    </div>
                    <div class="admin-card-actions">
                        <button class="btn btn-sm btn-ghost" onclick="editPartner('${partner._id}')"><i class="fas fa-edit"></i> Modifier</button>
                        <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deletePartner('${partner._id}')"><i class="fas fa-trash"></i> Supprimer</button>
                    </div>
                </div>
            </div>
        `;
    };
    const renderGrid = (partner) => {
        const src = partnerImageSrc(partner);
        return `
            <article class="admin-grid-card">
                <div class="admin-grid-card-media">
                    ${src ? `<img src="${src}" alt="" loading="lazy">` : '<div class="admin-grid-fallback"><i class="fas fa-handshake"></i></div>'}
                </div>
                <h3 class="admin-grid-card-title">${partner.name || 'Sans nom'}</h3>
                <div class="admin-card-meta">
                    <span>${partner.period || '—'}</span>
                    <span>Ordre ${partner.order || 0}</span>
                </div>
                <div class="admin-card-actions">
                    <button class="btn btn-sm btn-ghost" onclick="editPartner('${partner._id}')"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deletePartner('${partner._id}')"><i class="fas fa-trash"></i></button>
                </div>
            </article>
        `;
    };
    setAdminListItems('partners', partners, {
        listId: 'partners-list',
        paginationId: 'partners-pagination',
        countId: 'partners-count-label',
        listBtnId: 'partners-view-list',
        gridBtnId: 'partners-view-grid',
        emptyHtml: '<p class="admin-empty">Aucun partenaire disponible.</p>',
        countLabel: (n) => (n === 1 ? '1 partenaire' : `${n} partenaires`),
        renderList,
        renderGrid,
    });
}

function bindPartnerImageUpload() {
    const fileInput = document.getElementById('partner-image-file');
    const urlInput = document.getElementById('partner-image-url');
    if (fileInput && !fileInput.dataset.bound) {
        fileInput.addEventListener('change', () => {
            const file = fileInput.files?.[0];
            if (file) {
                const hidden = document.getElementById('partner-image');
                if (hidden) hidden.value = '';
                if (urlInput) urlInput.value = '';
            }
            renderPartnerImagePreview();
        });
        fileInput.dataset.bound = '1';
    }
    if (urlInput && !urlInput.dataset.bound) {
        urlInput.addEventListener('input', () => {
            const hidden = document.getElementById('partner-image');
            const fileInputEl = document.getElementById('partner-image-file');
            if (fileInputEl) fileInputEl.value = '';
            if (hidden) hidden.value = urlInput.value.trim();
            renderPartnerImagePreview();
        });
        urlInput.dataset.bound = '1';
    }
}

function resetPartnerImageFields() {
    const hidden = document.getElementById('partner-image');
    const fileInput = document.getElementById('partner-image-file');
    const urlInput = document.getElementById('partner-image-url');
    if (hidden) hidden.value = '';
    if (fileInput) fileInput.value = '';
    if (urlInput) urlInput.value = '';
    renderPartnerImagePreview();
}

function renderPartnerImagePreview() {
    const box = document.getElementById('partner-image-preview');
    const hidden = document.getElementById('partner-image');
    const fileInput = document.getElementById('partner-image-file');
    if (!box) return;
    box.innerHTML = '';
    const file = fileInput?.files?.[0];
    if (file) {
        const url = URL.createObjectURL(file);
        box.innerHTML = `
            <div class="project-upload-thumb">
                <img src="${url}" alt="Aperçu partenaire">
                <button type="button" title="Retirer" aria-label="Retirer" onclick="clearPartnerImage()">&times;</button>
            </div>`;
        return;
    }
    const path = hidden?.value?.trim();
    if (path) {
        const src = /^https?:\/\//i.test(path) || path.startsWith('/')
            ? path
            : `/static/${path.replace(/^\//, '')}`;
        box.innerHTML = `
            <div class="project-upload-thumb">
                <img src="${escapeHtml(src)}" alt="Image partenaire">
                <button type="button" title="Retirer" aria-label="Retirer" onclick="clearPartnerImage()">&times;</button>
            </div>`;
    }
}

window.clearPartnerImage = function clearPartnerImage() {
    resetPartnerImageFields();
};

function initPartnersSection() {
    loadPartners();
    bindPartnerImageUpload();
    const partnerForm = document.getElementById('partner-form');
    if (partnerForm && !partnerForm.dataset.bound) {
        partnerForm.addEventListener('submit', handlePartnerSubmit);
        partnerForm.dataset.bound = '1';
    }
}

window.openPartnerModal = function openPartnerModal() {
    const modal = document.getElementById('partnerModal');
    const modalTitle = document.getElementById('partnerModalTitle');
    const partnerIdInput = document.getElementById('partner-id');
    const form = document.getElementById('partner-form');
    openModalEl(modal);
    if (modalTitle) modalTitle.textContent = 'Nouveau partenaire';
    if (partnerIdInput) partnerIdInput.value = '';
    if (form) {
        form.reset();
        const orderInput = document.getElementById('partner-order');
        if (orderInput) orderInput.value = '1';
    }
    resetPartnerImageFields();
    bindPartnerImageUpload();
    setTimeout(() => document.getElementById('partner-name')?.focus(), 100);
};

window.closePartnerModal = function closePartnerModal() {
    const modal = document.getElementById('partnerModal');
    closeModalEl(modal);
    const form = document.getElementById('partner-form');
    if (form) form.reset();
    const partnerIdInput = document.getElementById('partner-id');
    if (partnerIdInput) partnerIdInput.value = '';
    resetPartnerImageFields();
};

window.editPartner = function editPartner(partnerId) {
    const partner = allPartnersData.find(p => String(p._id) === String(partnerId));
    if (!partner) {
        showToast('Partenaire non trouvé', 'error');
        return;
    }
    const modal = document.getElementById('partnerModal');
    openModalEl(modal);
    const modalTitle = document.getElementById('partnerModalTitle');
    if (modalTitle) modalTitle.textContent = 'Modifier le partenaire';
    const setVal = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.value = value ?? '';
    };
    const image = partner.image || partner.logo || '';
    setVal('partner-id', partnerId);
    setVal('partner-name', partner.name || '');
    setVal('partner-image', image);
    setVal('partner-image-url', image);
    setVal('partner-order', partner.order ?? 0);
    const fileInput = document.getElementById('partner-image-file');
    if (fileInput) fileInput.value = '';
    bindPartnerImageUpload();
    renderPartnerImagePreview();
    setTimeout(() => document.getElementById('partner-name')?.focus(), 100);
};

async function handlePartnerSubmit(event) {
    event.preventDefault();
    const partnerId = document.getElementById('partner-id')?.value?.trim();
    const name = document.getElementById('partner-name')?.value?.trim() || '';
    const hidden = document.getElementById('partner-image');
    const urlInput = document.getElementById('partner-image-url');
    const fileInput = document.getElementById('partner-image-file');
    let image = (hidden?.value || urlInput?.value || '').trim();

    if (!name) {
        showToast('Nom requis', 'error');
        return;
    }

    try {
        const file = fileInput?.files?.[0];
        if (file) {
            image = await uploadProjectMediaFile(file);
            if (hidden) hidden.value = image;
            if (urlInput) urlInput.value = image;
            if (fileInput) fileInput.value = '';
            renderPartnerImagePreview();
        }

        if (!image) {
            showToast('Image requise (fichier ou URL)', 'error');
            return;
        }

        const payload = {
            name,
            image,
            logo: image,
            order: parseInt(document.getElementById('partner-order')?.value || '0', 10) || 0,
        };
        const url = partnerId ? `${API_BASE}/partners/${partnerId}` : `${API_BASE}/partners`;
        const method = partnerId ? 'PUT' : 'POST';
        const response = await fetch(url, {
            method,
            headers: getHeaders(),
            credentials: 'same-origin',
            body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok && data.success !== false) {
            showToast(partnerId ? 'Partenaire mis à jour' : 'Partenaire créé', 'success');
            closePartnerModal();
            loadPartners();
        } else {
            showToast(data.error || 'Erreur lors de l’enregistrement', 'error');
        }
    } catch (error) {
        console.error('Erreur partner submit:', error);
        showToast(error.message || 'Erreur lors de l’enregistrement', 'error');
    }
}

window.deletePartner = async function deletePartner(partnerId) {
    if (!partnerId) {
        showToast('ID partenaire invalide', 'error');
        return;
    }
    const confirmed = await adminConfirm({
        title: 'Supprimer ce partenaire ?',
        message: 'Il sera retiré de la section références du site.',
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!confirmed) return;
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
};

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

function projectCoverSrc(project) {
    const img = project.image || project.cover || project.thumbnail || '';
    if (!img) return '';
    if (/^https?:\/\//i.test(img) || img.startsWith('/')) return img;
    return `/static/${img.replace(/^\//, '')}`;
}

function displayProjects(projects) {
    const statusBadge = (project) => (
        project.status === 'published'
            ? '<span class="admin-badge">Publié</span>'
            : project.status === 'draft'
            ? '<span class="admin-badge admin-badge--draft">Brouillon</span>'
            : '<span class="admin-badge admin-badge--archived">Archivé</span>'
    );
    const renderList = (project) => {
        const description = project.description || '';
        const truncatedDesc = description.length > 100 ? description.substring(0, 100) + '...' : description;
        const links = [];
        if (project.link) links.push(`<a href="${escapeHtml(project.link)}" target="_blank" rel="noopener"><i class="fas fa-external-link-alt"></i> Site</a>`);
        if (project.github_link) links.push(`<a href="${escapeHtml(project.github_link)}" target="_blank" rel="noopener"><i class="fab fa-github"></i> GitHub</a>`);
        const cover = projectCoverSrc(project);
        return `
            <div class="admin-card">
                <div class="admin-card-row">
                    <div class="admin-card-main admin-card-main--media">
                        ${cover ? `<img class="admin-list-thumb" src="${cover}" alt="" loading="lazy">` : '<div class="admin-list-thumb admin-list-thumb--empty"><i class="fas fa-folder"></i></div>'}
                        <div>
                            <div class="admin-card-title-row">
                                <h3>${escapeHtml(project.title || 'Sans titre')}</h3>
                                ${statusBadge(project)}
                                ${project.featured ? '<span class="admin-badge admin-badge--featured"><i class="fas fa-star"></i> Vedette</span>' : ''}
                            </div>
                            <p><strong>Technologies:</strong> ${escapeHtml(project.technologies || 'N/A')}</p>
                            <p>${escapeHtml(truncatedDesc)}</p>
                            ${links.length ? `<div class="admin-card-links">${links.join('')}</div>` : ''}
                            <div class="admin-card-meta">
                                <span><strong>Ordre:</strong> ${project.order || 0}</span>
                                ${project.views !== undefined ? `<span><strong>Vues:</strong> ${project.views || 0}</span>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="admin-card-actions">
                        <button class="btn btn-sm btn-ghost" onclick="viewProjectDetail('${project._id}')"><i class="fas fa-eye"></i> Détail</button>
                        <button class="btn btn-sm btn-ghost" onclick="editProject('${project._id}')"><i class="fas fa-edit"></i> Modifier</button>
                        <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteProject('${project._id}', '${escapeHtml(project.title)}')"><i class="fas fa-trash"></i> Supprimer</button>
                    </div>
                </div>
            </div>
        `;
    };
    const renderGrid = (project) => {
        const cover = projectCoverSrc(project);
        const description = project.description || '';
        const truncatedDesc = description.length > 90 ? description.substring(0, 90) + '...' : description;
        return `
            <article class="admin-grid-card">
                <div class="admin-grid-card-media">
                    ${cover ? `<img src="${cover}" alt="" loading="lazy">` : '<div class="admin-grid-fallback"><i class="fas fa-folder"></i></div>'}
                    ${project.featured ? '<span class="admin-badge admin-badge--featured admin-grid-badge"><i class="fas fa-star"></i></span>' : ''}
                </div>
                <div class="admin-card-title-row">
                    <h3 class="admin-grid-card-title">${escapeHtml(project.title || 'Sans titre')}</h3>
                    ${statusBadge(project)}
                </div>
                <p class="admin-grid-card-text">${escapeHtml(truncatedDesc)}</p>
                <div class="admin-card-actions">
                    <button class="btn btn-sm btn-ghost" onclick="viewProjectDetail('${project._id}')"><i class="fas fa-eye"></i></button>
                    <button class="btn btn-sm btn-ghost" onclick="editProject('${project._id}')"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteProject('${project._id}', '${escapeHtml(project.title)}')"><i class="fas fa-trash"></i></button>
                </div>
            </article>
        `;
    };
    setAdminListItems('projects', projects, {
        listId: 'projects-list',
        paginationId: 'projects-pagination',
        countId: 'projects-count-label',
        listBtnId: 'projects-view-list',
        gridBtnId: 'projects-view-grid',
        emptyHtml: '<p class="admin-empty">Aucun projet disponible.</p>',
        countLabel: (n) => (n === 1 ? '1 projet' : `${n} projets`),
        renderList,
        renderGrid,
    });
}

function initProjectsSection() {
    loadProjects();
    const projectForm = document.getElementById('project-form');
    if (projectForm && !projectForm.dataset.bound) {
        projectForm.addEventListener('submit', handleProjectSubmit);
        projectForm.dataset.bound = '1';
    }
    const mainFile = document.getElementById('project-image-file');
    const extraFiles = document.getElementById('project-additional-files');
    if (mainFile && !mainFile.dataset.bound) {
        mainFile.addEventListener('change', () => renderProjectMainPreview());
        mainFile.dataset.bound = '1';
    }
    if (extraFiles && !extraFiles.dataset.bound) {
        extraFiles.addEventListener('change', () => renderProjectAdditionalPreview());
        extraFiles.dataset.bound = '1';
    }
}

function projectMediaSrc(path) {
    if (!path) return '';
    const p = String(path).trim();
    if (!p) return '';
    if (p.startsWith('http://') || p.startsWith('https://') || p.startsWith('/')) return p;
    return `/static/${p}`;
}

function parseAdditionalImages(value) {
    if (!value) return [];
    if (Array.isArray(value)) return value.map(v => String(v).trim()).filter(Boolean);
    return String(value).split(',').map(v => v.trim()).filter(Boolean);
}

function resetProjectImageFields() {
    const mainHidden = document.getElementById('project-image');
    const extraHidden = document.getElementById('project-additional-images');
    const mainFile = document.getElementById('project-image-file');
    const extraFiles = document.getElementById('project-additional-files');
    if (mainHidden) mainHidden.value = '';
    if (extraHidden) extraHidden.value = '';
    if (mainFile) mainFile.value = '';
    if (extraFiles) extraFiles.value = '';
    renderProjectMainPreview();
    renderProjectAdditionalPreview();
}

function renderProjectMainPreview() {
    const box = document.getElementById('project-image-preview');
    const hidden = document.getElementById('project-image');
    const fileInput = document.getElementById('project-image-file');
    if (!box) return;
    box.innerHTML = '';
    const file = fileInput?.files?.[0];
    if (file) {
        const url = URL.createObjectURL(file);
        box.innerHTML = `
            <div class="project-upload-thumb">
                <img src="${url}" alt="Aperçu image principale">
                <button type="button" title="Retirer" aria-label="Retirer" onclick="clearProjectMainImage()">&times;</button>
            </div>`;
        return;
    }
    const path = hidden?.value?.trim();
    if (path) {
        box.innerHTML = `
            <div class="project-upload-thumb">
                <img src="${escapeHtml(projectMediaSrc(path))}" alt="Image principale">
                <button type="button" title="Retirer" aria-label="Retirer" onclick="clearProjectMainImage()">&times;</button>
            </div>`;
    }
}

window.clearProjectMainImage = function clearProjectMainImage() {
    const hidden = document.getElementById('project-image');
    const fileInput = document.getElementById('project-image-file');
    if (hidden) hidden.value = '';
    if (fileInput) fileInput.value = '';
    renderProjectMainPreview();
};

function renderProjectAdditionalPreview() {
    const box = document.getElementById('project-additional-preview');
    const hidden = document.getElementById('project-additional-images');
    const fileInput = document.getElementById('project-additional-files');
    if (!box) return;
    const existing = parseAdditionalImages(hidden?.value);
    const pending = Array.from(fileInput?.files || []);
    box.innerHTML = '';

    existing.forEach((path, index) => {
        const thumb = document.createElement('div');
        thumb.className = 'project-upload-thumb';
        thumb.innerHTML = `
            <img src="${escapeHtml(projectMediaSrc(path))}" alt="Image ${index + 1}">
            <button type="button" title="Retirer" aria-label="Retirer">&times;</button>`;
        thumb.querySelector('button').addEventListener('click', () => {
            existing.splice(index, 1);
            if (hidden) hidden.value = existing.join(', ');
            renderProjectAdditionalPreview();
        });
        box.appendChild(thumb);
    });

    pending.forEach((file, index) => {
        const url = URL.createObjectURL(file);
        const thumb = document.createElement('div');
        thumb.className = 'project-upload-thumb';
        thumb.innerHTML = `
            <img src="${url}" alt="${escapeHtml(file.name)}">
            <button type="button" title="Retirer" aria-label="Retirer">&times;</button>`;
        thumb.querySelector('button').addEventListener('click', () => {
            const dt = new DataTransfer();
            pending.forEach((f, i) => {
                if (i !== index) dt.items.add(f);
            });
            if (fileInput) fileInput.files = dt.files;
            renderProjectAdditionalPreview();
        });
        box.appendChild(thumb);
    });
}

async function uploadProjectMediaFile(file) {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('alt_text', file.name || 'project');
    const res = await fetch('/api/media', { method: 'POST', credentials: 'include', body: fd });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        if (res.status === 413) {
            throw new Error(`Fichier trop volumineux (max 8 Mo) : ${file.name}`);
        }
        throw new Error(data.error || `Échec upload (${file.name})`);
    }
    return data.asset?.path || '';
}

// Exposer la fonction globalement
window.openProjectModal = function openProjectModal() {
    const modal = document.getElementById('projectModal');
    const modalTitle = document.getElementById('projectModalTitle');
    const projectIdInput = document.getElementById('project-id');
    
    if (modal) {
        modal.style.display = 'flex';
        modal.style.opacity = '1';
        modal.classList.add('open');
        
        if (modalTitle) modalTitle.textContent = 'Nouveau projet';
        if (projectIdInput) projectIdInput.value = '';
        
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
        resetProjectImageFields();
        
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
        resetProjectImageFields();
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
    const mainFileInput = document.getElementById('project-image-file');
    const extraFilesInput = document.getElementById('project-additional-files');
    const statusInput = document.getElementById('project-status');
    const orderInput = document.getElementById('project-order');
    const featuredInput = document.getElementById('project-featured');
    
    if (modal) {
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
        if (mainFileInput) mainFileInput.value = '';
        if (extraFilesInput) extraFilesInput.value = '';
        if (imageInput) imageInput.value = project.image || '';
        if (additionalImagesInput) {
            const additionalImages = parseAdditionalImages(project.additional_images || '');
            additionalImagesInput.value = additionalImages.join(', ');
        }
        renderProjectMainPreview();
        renderProjectAdditionalPreview();
        if (statusInput) statusInput.value = project.status || 'published';
        if (orderInput) orderInput.value = project.order || 0;
        if (featuredInput) featuredInput.checked = project.featured || false;
        
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
    const mainFileInput = document.getElementById('project-image-file');
    const extraFilesInput = document.getElementById('project-additional-files');
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
    let image = imageInput ? imageInput.value.trim() : '';
    let additionalImages = additionalImagesInput ? additionalImagesInput.value.trim() : '';
    const status = statusInput ? statusInput.value : 'published';
    const order = orderInput ? parseInt(orderInput.value) || 0 : 0;
    const featured = featuredInput ? featuredInput.checked : false;
    
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
    
    const originalBtnText = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Téléversement...';
    }
    
    try {
        const mainFile = mainFileInput?.files?.[0];
        if (mainFile) {
            image = await uploadProjectMediaFile(mainFile);
            if (imageInput) imageInput.value = image;
        }

        const extraFiles = Array.from(extraFilesInput?.files || []);
        if (extraFiles.length) {
            const uploaded = [];
            for (const file of extraFiles) {
                uploaded.push(await uploadProjectMediaFile(file));
            }
            const merged = [...parseAdditionalImages(additionalImages), ...uploaded.filter(Boolean)];
            additionalImages = merged.join(', ');
            if (additionalImagesInput) additionalImagesInput.value = additionalImages;
            if (extraFilesInput) extraFilesInput.value = '';
        }

        if (submitBtn) submitBtn.textContent = projectId ? 'Mise à jour...' : 'Création...';

        const url = projectId ? `${API_BASE}/projects/${projectId}` : `${API_BASE}/projects`;
        const method = projectId ? 'PUT' : 'POST';
        
        const requestData = {
            title: title,
            technologies: technologies,
            description: description,
            status: status,
            order: order,
            featured: featured,
            image: image || '',
            additional_images: additionalImages || '',
        };
        
        if (link) requestData.link = link;
        if (github) requestData.github_link = github;
        
        const response = await fetch(url, {
            method: method,
            headers: getHeaders(),
            credentials: 'include',
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            const errMsg = data.error || data.message || (projectId ? 'Erreur lors de la mise à jour' : 'Erreur lors de la création');
            console.error('Projet API', response.status, errMsg, requestData);
            showToast(errMsg, 'error');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
            return;
        }
        
        showToast(projectId ? 'Projet mis à jour avec succès' : 'Projet créé avec succès', 'success');
        closeProjectModal();
        
        if (projectId) {
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
    
    if (project.image) {
        allImages.push({ url: projectMediaSrc(project.image), isMain: true });
    }
    
    if (project.additional_images) {
        parseAdditionalImages(project.additional_images).forEach(img => {
            if (img && img !== project.image) {
                allImages.push({ url: projectMediaSrc(img), isMain: false });
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
                                 onerror="this.style.opacity='0.3'">
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

async function deleteProject(projectId, projectTitle) {
    const title = projectTitle || 'ce projet';
    const confirmed = await adminConfirm({
        title: 'Supprimer ce projet ?',
        message: `« ${title} » sera retiré du portfolio.\nCette action est irréversible.`,
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}`, {
            method: 'DELETE',
            headers: getHeaders(),
            credentials: 'include',
        });
        const data = await response.json().catch(() => ({}));
        if (data.success) {
            showToast('Projet supprimé avec succès', 'success');
            allProjectsData = allProjectsData.filter(p => p._id !== projectId);
            displayProjects(allProjectsData);
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('❌ Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
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
    const renderList = (service) => {
        const description = service.description || '';
        const truncatedDesc = description.length > 150 ? description.substring(0, 150) + '...' : description;
        return `
            <div class="admin-card">
                <div class="admin-card-row">
                    <div class="admin-card-main">
                        <h3>${escapeHtml(service.title || 'Sans titre')}</h3>
                        ${service.icon ? `<div class="admin-card-meta"><span><i class="fas fa-image" style="color:var(--green)"></i> ${escapeHtml(service.icon)}</span></div>` : ''}
                        <p>${escapeHtml(truncatedDesc)}</p>
                        <div class="admin-card-meta"><span><strong>Ordre:</strong> ${service.order || 0}</span></div>
                    </div>
                    <div class="admin-card-actions">
                        <button class="btn btn-sm btn-ghost" onclick="editService('${service._id}')"><i class="fas fa-edit"></i> Modifier</button>
                        <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteService('${service._id}', '${escapeHtml(service.title)}')"><i class="fas fa-trash"></i> Supprimer</button>
                    </div>
                </div>
            </div>
        `;
    };
    const renderGrid = (service) => {
        const description = service.description || '';
        const truncatedDesc = description.length > 100 ? description.substring(0, 100) + '...' : description;
        const initial = (service.title || 'S').trim().charAt(0).toUpperCase();
        return `
            <article class="admin-grid-card">
                <div class="admin-grid-card-icon">${initial}</div>
                <h3 class="admin-grid-card-title">${escapeHtml(service.title || 'Sans titre')}</h3>
                <p class="admin-grid-card-text">${escapeHtml(truncatedDesc)}</p>
                <div class="admin-card-meta"><span>Ordre ${service.order || 0}</span></div>
                <div class="admin-card-actions">
                    <button class="btn btn-sm btn-ghost" onclick="editService('${service._id}')"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteService('${service._id}', '${escapeHtml(service.title)}')"><i class="fas fa-trash"></i></button>
                </div>
            </article>
        `;
    };
    setAdminListItems('services', services, {
        listId: 'services-list',
        paginationId: 'services-pagination',
        countId: 'services-count-label',
        listBtnId: 'services-view-list',
        gridBtnId: 'services-view-grid',
        emptyHtml: '<p class="admin-empty">Aucun service disponible.</p>',
        countLabel: (n) => (n === 1 ? '1 service' : `${n} services`),
        renderList,
        renderGrid,
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

async function deleteService(serviceId, serviceTitle) {
    const title = serviceTitle || 'ce service';
    const confirmed = await adminConfirm({
        title: 'Supprimer ce service ?',
        message: `« ${title} » sera retiré de la page services.\nCette action est irréversible.`,
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_BASE}/services/${serviceId}`, {
            method: 'DELETE',
            headers: getHeaders(),
            credentials: 'include',
        });
        const data = await response.json().catch(() => ({}));
        if (data.success) {
            showToast('Service supprimé avec succès', 'success');
            allServicesData = allServicesData.filter(s => s._id !== serviceId);
            displayServices(allServicesData);
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('❌ Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
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
            contactsList.innerHTML = '<p class="admin-empty">Aucun message disponible.</p>';
        }
        updateContactsCount([]);
    }
}

function displayContacts(contacts) {
    updateContactsCount();
    const formatDate = (value) => {
        const date = new Date(value);
        return date.toLocaleDateString('fr-FR', {
            day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    };
    const actions = (contact, isUnread) => `
        ${isUnread
            ? `<button type="button" class="btn btn-ghost btn-sm" onclick="markContactRead('${contact._id}', true)"><i class="fas fa-check"></i> Marquer lu</button>`
            : `<button type="button" class="btn btn-ghost btn-sm" onclick="markContactRead('${contact._id}', false)"><i class="fas fa-envelope"></i> Non lu</button>`}
        <a href="mailto:${contact.email}?subject=Re: ${encodeURIComponent(contact.subject || '')}" class="btn btn-ghost btn-sm" target="_blank" rel="noopener"><i class="fas fa-reply"></i> Répondre</a>
        <button type="button" class="btn btn-ghost btn-sm btn-danger-ghost" onclick="deleteContact('${contact._id}')"><i class="fas fa-trash"></i> Supprimer</button>
    `;
    const renderList = (contact) => {
        const isUnread = !contact.read;
        const initial = (contact.name || contact.email || '?').trim().charAt(0).toUpperCase();
        return `
            <article class="contact-item${isUnread ? ' is-unread' : ''}">
                <div class="contact-item-avatar" aria-hidden="true">${escapeHtml(initial)}</div>
                <div class="contact-item-body">
                    <div class="contact-item-top">
                        <div class="contact-item-heading">
                            <h3 class="contact-item-subject">${escapeHtml(contact.subject || 'Sans sujet')}</h3>
                            ${isUnread ? '<span class="contact-dot" title="Non lu"></span>' : ''}
                        </div>
                        <time class="contact-item-date">${formatDate(contact.created_at)}</time>
                    </div>
                    <p class="contact-item-from">
                        <span>${escapeHtml(contact.name || 'Anonyme')}</span>
                        <a href="mailto:${escapeHtml(contact.email)}">${escapeHtml(contact.email || '')}</a>
                    </p>
                    <p class="contact-item-preview">${escapeHtml((contact.message || '').trim()) || '—'}</p>
                    <div class="contact-item-actions">${actions(contact, isUnread)}</div>
                </div>
            </article>
        `;
    };
    const renderGrid = (contact) => {
        const isUnread = !contact.read;
        const initial = (contact.name || contact.email || '?').trim().charAt(0).toUpperCase();
        const preview = ((contact.message || '').trim()).slice(0, 120);
        return `
            <article class="admin-grid-card contact-grid-card${isUnread ? ' is-unread' : ''}">
                <div class="admin-grid-card-icon">${escapeHtml(initial)}</div>
                <div class="admin-card-title-row">
                    <h3 class="admin-grid-card-title">${escapeHtml(contact.subject || 'Sans sujet')}</h3>
                    ${isUnread ? '<span class="contact-dot" title="Non lu"></span>' : ''}
                </div>
                <p class="admin-grid-card-text">${escapeHtml(contact.name || 'Anonyme')}</p>
                <p class="admin-grid-card-text">${escapeHtml(preview) || '—'}</p>
                <div class="admin-card-meta"><span>${formatDate(contact.created_at)}</span></div>
                <div class="admin-card-actions">${actions(contact, isUnread)}</div>
            </article>
        `;
    };
    setAdminListItems('contacts', contacts, {
        listId: 'contacts-list',
        paginationId: 'contacts-pagination',
        countId: 'contacts-view-count',
        listBtnId: 'contacts-view-list',
        gridBtnId: 'contacts-view-grid',
        listClass: 'admin-list contacts-list',
        gridClass: 'contacts-list admin-items-grid',
        emptyHtml: '<p class="admin-empty">Aucun message disponible.</p>',
        countLabel: (n) => (n === 1 ? '1 message' : `${n} messages`),
        perPage: 8,
        renderList,
        renderGrid,
    });
}

function updateContactsCount(contacts) {
    // Toujours utiliser allContacts pour le compteur total, pas les contacts filtrés
    const unreadCount = allContacts.filter(c => !c.read).length;
    const unreadCountEl = document.getElementById('unread-count');
    if (unreadCountEl) {
        unreadCountEl.textContent = unreadCount;
        unreadCountEl.classList.toggle('has-unread', unreadCount > 0);
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

async function deleteContact(contactId) {
    const confirmed = await adminConfirm({
        title: 'Supprimer ce message ?',
        message: 'Le message sera retiré de la boîte de réception.',
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!confirmed) return;
    try {
        const response = await fetch(`${API_BASE}/contacts/${contactId}`, {
            method: 'DELETE',
            headers: getHeaders(),
            credentials: 'include',
        });
        const data = await response.json().catch(() => ({}));
        if (data.success) {
            showToast('Message supprimé', 'success');
            loadContacts();
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
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
            credentials: 'include',
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
    const adminIdToCompare = currentAdminId || (currentProfileData && (currentProfileData._id || currentProfileData.id));
    const fmt = (value, withTime = false) => {
        if (!value) return 'Jamais';
        return new Date(value).toLocaleDateString('fr-FR', withTime
            ? { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }
            : { year: 'numeric', month: 'long', day: 'numeric' });
    };
    const actions = (admin, isCurrentUser) => (
        `<button class="btn btn-sm btn-ghost" onclick="editAdmin('${admin._id}')"><i class="fas fa-edit"></i> Modifier</button>`
        + (!isCurrentUser
            ? ` <button class="btn btn-sm btn-ghost btn-danger-ghost" onclick="deleteAdmin('${admin._id}', '${escapeHtml(admin.username)}')"><i class="fas fa-trash"></i> Supprimer</button>`
            : '')
    );
    const renderList = (admin) => {
        const isCurrentUser = admin._id === adminIdToCompare;
        return `
            <div class="admin-card">
                <div class="admin-card-row">
                    <div class="admin-card-main">
                        <div class="admin-card-title-row">
                            <h3>${escapeHtml(admin.username || 'Sans nom')}</h3>
                            ${isCurrentUser ? '<span class="admin-badge">Vous</span>' : ''}
                        </div>
                        <div class="admin-card-meta">
                            ${admin.full_name ? `<span>${escapeHtml(admin.full_name)}</span>` : ''}
                            ${admin.email ? `<span><a href="mailto:${admin.email}" style="color:var(--green)">${escapeHtml(admin.email)}</a></span>` : ''}
                            <span>Créé le ${fmt(admin.created_at)}</span>
                            <span>Dernière connexion : ${fmt(admin.last_login, true)}</span>
                        </div>
                    </div>
                    <div class="admin-card-actions">${actions(admin, isCurrentUser)}</div>
                </div>
            </div>
        `;
    };
    const renderGrid = (admin) => {
        const isCurrentUser = admin._id === adminIdToCompare;
        const initial = (admin.username || 'A').trim().charAt(0).toUpperCase();
        return `
            <article class="admin-grid-card">
                <div class="admin-grid-card-icon">${escapeHtml(initial)}</div>
                <div class="admin-card-title-row">
                    <h3 class="admin-grid-card-title">${escapeHtml(admin.username || 'Sans nom')}</h3>
                    ${isCurrentUser ? '<span class="admin-badge">Vous</span>' : ''}
                </div>
                <p class="admin-grid-card-text">${escapeHtml(admin.full_name || admin.email || '—')}</p>
                <div class="admin-card-meta"><span>${fmt(admin.last_login, true)}</span></div>
                <div class="admin-card-actions">${actions(admin, isCurrentUser)}</div>
            </article>
        `;
    };
    setAdminListItems('admins', admins, {
        listId: 'admins-list',
        paginationId: 'admins-pagination',
        countId: 'admins-count-label',
        listBtnId: 'admins-view-list',
        gridBtnId: 'admins-view-grid',
        emptyHtml: '<p class="admin-empty">Aucun administrateur disponible.</p>',
        countLabel: (n) => (n === 1 ? '1 administrateur' : `${n} administrateurs`),
        renderList,
        renderGrid,
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
    
    if (!email || !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        showToast('Un email valide est requis pour la connexion', 'error');
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

    const modal = document.getElementById('edit-admin-modal');
    const idInput = document.getElementById('edit-admin-id');
    const emailInput = document.getElementById('edit-admin-email');
    const nameInput = document.getElementById('edit-admin-full-name');
    const passwordInput = document.getElementById('edit-admin-password');
    const currentPasswordInput = document.getElementById('edit-admin-current-password');
    const usernameEl = document.getElementById('edit-admin-username');

    if (!modal || !idInput || !emailInput || !nameInput || !passwordInput) {
        showToast('Modale d’édition indisponible', 'error');
        return;
    }

    idInput.value = adminId;
    emailInput.value = admin.email || '';
    nameInput.value = admin.full_name || '';
    passwordInput.value = '';
    if (currentPasswordInput) currentPasswordInput.value = '';
    if (usernameEl) {
        usernameEl.textContent = `@${admin.username || 'admin'}`;
    }

    if (typeof openModalEl === 'function') {
        openModalEl(modal);
    } else {
        modal.style.display = 'flex';
        requestAnimationFrame(() => modal.classList.add('open'));
    }
    window.setTimeout(() => emailInput.focus(), 60);
}

function closeEditAdminModal() {
    const modal = document.getElementById('edit-admin-modal');
    if (!modal) return;
    if (typeof closeModalEl === 'function') {
        closeModalEl(modal);
    } else {
        modal.classList.remove('open');
        modal.style.display = 'none';
    }
    const form = document.getElementById('edit-admin-form');
    if (form) form.reset();
    const idInput = document.getElementById('edit-admin-id');
    if (idInput) idInput.value = '';
}

function saveEditAdmin(event) {
    event.preventDefault();

    const adminId = document.getElementById('edit-admin-id')?.value;
    const admin = allAdminsData.find(a => a._id === adminId);
    if (!adminId || !admin) {
        showToast('Administrateur non trouvé', 'error');
        return;
    }

    const newEmail = (document.getElementById('edit-admin-email')?.value || '').trim();
    const newFullName = (document.getElementById('edit-admin-full-name')?.value || '').trim();
    const currentPassword = document.getElementById('edit-admin-current-password')?.value || '';
    const newPassword = document.getElementById('edit-admin-password')?.value || '';

    const updateData = {};
    if (newEmail !== (admin.email || '')) {
        updateData.email = newEmail;
    }
    if (newFullName !== (admin.full_name || '')) {
        updateData.full_name = newFullName;
    }
    if (newPassword) {
        if (!currentPassword) {
            showToast('Saisissez l’ancien mot de passe pour en définir un nouveau', 'error');
            document.getElementById('edit-admin-current-password')?.focus();
            return;
        }
        if (newPassword.length < 6) {
            showToast('Le mot de passe doit contenir au moins 6 caractères', 'error');
            document.getElementById('edit-admin-password')?.focus();
            return;
        }
        updateData.current_password = currentPassword;
        updateData.password = newPassword;
    } else if (currentPassword) {
        showToast('Indiquez aussi le nouveau mot de passe', 'error');
        document.getElementById('edit-admin-password')?.focus();
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
            credentials: 'include',
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            showToast(data.error || 'Erreur lors de la mise à jour', 'error');
            if (data.error && String(data.error).toLowerCase().includes('ancien')) {
                document.getElementById('edit-admin-current-password')?.focus();
            }
            return;
        }
        
        closeEditAdminModal();
        showToast(
            data.message || (updateData.password ? 'Mot de passe mis à jour avec succès' : 'Administrateur mis à jour avec succès'),
            'success'
        );
        
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

async function deleteAdmin(adminId, username) {
    const confirmed = await adminConfirm({
        title: 'Supprimer cet administrateur ?',
        message: `Le compte « ${username} » sera définitivement supprimé.\nCette action est irréversible.`,
        confirmLabel: 'Supprimer',
        danger: true,
    });
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_BASE}/admin/users/${adminId}`, {
            method: 'DELETE',
            headers: getHeaders(),
            credentials: 'include',
        });
        const data = await response.json().catch(() => ({}));
        if (data.success) {
            showToast('Administrateur supprimé avec succès', 'success');
            allAdminsData = allAdminsData.filter(a => a._id !== adminId);
            displayAdminUsers(allAdminsData);
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
}

// Exposer toutes les fonctions utilisées par les onclick inline de l'admin
Object.assign(window, {
    showSection,
    loadHomepageData,
    loadSkills,
    loadPartners,
    loadProjects,
    loadServices,
    loadContacts,
    toggleNotifications,
    loadProfile,
    resetPasswordForm,
    loadLoginHistory,
    loadAdminUsers,
    editProject,
    deleteProject,
    editService,
    deleteService,
    markContactRead,
    deleteContact,
    updateProfile,
    changePassword,
    createAdmin,
    openCreateAdminModal,
    closeCreateAdminModal,
    editAdmin,
    closeEditAdminModal,
    saveEditAdmin,
    deleteAdmin,
});
// Déjà assignés via window.xxx = function ... — garantir la présence
[
    'openSkillModal', 'closeSkillModal', 'editSkill', 'deleteSkill',
    'openPartnerModal', 'closePartnerModal', 'editPartner', 'deletePartner',
    'openProjectModal', 'closeProjectModal', 'viewProjectDetail', 'closeProjectDetailModal',
    'openServiceModal', 'closeServiceModal',
].forEach((name) => {
    if (typeof window[name] !== 'function') {
        console.error(`Handler admin manquant: ${name}`);
    }
});

