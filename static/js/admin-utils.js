// ============================================
// Admin Utilities - Confirmation, Pagination, Search, Export
// ============================================

// ========== Modal de Confirmation Personnalisée ==========
function showConfirmModal(title, message, onConfirm, onCancel = null) {
    // Créer la modale si elle n'existe pas
    let modal = document.getElementById('confirm-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'confirm-modal';
        modal.className = 'confirm-modal';
        modal.innerHTML = `
            <div class="confirm-modal-content">
                <div class="confirm-modal-header">
                    <h3 id="confirm-modal-title"></h3>
                    <button class="confirm-modal-close" onclick="closeConfirmModal()">&times;</button>
                </div>
                <div class="confirm-modal-body">
                    <p id="confirm-modal-message"></p>
                </div>
                <div class="confirm-modal-footer">
                    <button class="btn btn-secondary" id="confirm-modal-cancel">Annuler</button>
                    <button class="btn btn-danger" id="confirm-modal-confirm">Confirmer</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Styles pour la modale
        const style = document.createElement('style');
        style.textContent = `
            .confirm-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                z-index: 10000;
                align-items: center;
                justify-content: center;
            }
            .confirm-modal.show {
                display: flex;
            }
            .confirm-modal-content {
                background: var(--light-bg, #2D2E32);
                border-radius: 12px;
                padding: 0;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                animation: modalSlideIn 0.3s ease-out;
            }
            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            .confirm-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.5rem;
                border-bottom: 1px solid var(--dark-bg, #25262A);
            }
            .confirm-modal-header h3 {
                margin: 0;
                color: var(--white, #FFFFFF);
            }
            .confirm-modal-close {
                background: none;
                border: none;
                color: var(--gray, #777777);
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: all 0.2s;
            }
            .confirm-modal-close:hover {
                background: var(--dark-bg, #25262A);
                color: var(--white, #FFFFFF);
            }
            .confirm-modal-body {
                padding: 1.5rem;
                color: var(--white, #FFFFFF);
            }
            .confirm-modal-footer {
                display: flex;
                gap: 0.5rem;
                justify-content: flex-end;
                padding: 1rem 1.5rem;
                border-top: 1px solid var(--dark-bg, #25262A);
            }
        `;
        document.head.appendChild(style);
    }
    
    // Remplir le contenu
    document.getElementById('confirm-modal-title').textContent = title;
    document.getElementById('confirm-modal-message').textContent = message;
    
    // Gérer les événements
    const confirmBtn = document.getElementById('confirm-modal-confirm');
    const cancelBtn = document.getElementById('confirm-modal-cancel');
    
    // Retirer les anciens listeners
    const newConfirmBtn = confirmBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    newConfirmBtn.onclick = () => {
        closeConfirmModal();
        if (onConfirm) onConfirm();
    };
    
    newCancelBtn.onclick = () => {
        closeConfirmModal();
        if (onCancel) onCancel();
    };
    
    // Fermer au clic sur l'overlay
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeConfirmModal();
            if (onCancel) onCancel();
        }
    };
    
    // Afficher la modale
    modal.classList.add('show');
}

function closeConfirmModal() {
    const modal = document.getElementById('confirm-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// ========== Pagination ==========
function createPagination(currentPage, totalPages, onPageChange, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHTML = '<div class="pagination">';
    
    // Bouton Précédent
    if (currentPage > 1) {
        paginationHTML += `<button class="pagination-btn" onclick="${onPageChange}(${currentPage - 1})">‹ Précédent</button>`;
    } else {
        paginationHTML += `<button class="pagination-btn" disabled>‹ Précédent</button>`;
    }
    
    // Numéros de page
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        paginationHTML += `<button class="pagination-btn" onclick="${onPageChange}(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHTML += `<button class="pagination-btn pagination-btn-active">${i}</button>`;
        } else {
            paginationHTML += `<button class="pagination-btn" onclick="${onPageChange}(${i})">${i}</button>`;
        }
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="pagination-btn" onclick="${onPageChange}(${totalPages})">${totalPages}</button>`;
    }
    
    // Bouton Suivant
    if (currentPage < totalPages) {
        paginationHTML += `<button class="pagination-btn" onclick="${onPageChange}(${currentPage + 1})">Suivant ›</button>`;
    } else {
        paginationHTML += `<button class="pagination-btn" disabled>Suivant ›</button>`;
    }
    
    paginationHTML += '</div>';
    
    container.innerHTML = paginationHTML;
}

// Styles pour la pagination
const paginationStyles = `
    .pagination {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        justify-content: center;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    .pagination-btn {
        padding: 0.5rem 1rem;
        border: 1px solid var(--border-color, #3a3b3f);
        background: var(--card-bg, #2D2E32);
        color: var(--text-color, #FFFFFF);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.9rem;
    }
    .pagination-btn:hover:not(:disabled) {
        background: var(--green, #4DBA87);
        border-color: var(--green, #4DBA87);
        color: white;
    }
    .pagination-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .pagination-btn-active {
        background: var(--green, #4DBA87) !important;
        border-color: var(--green, #4DBA87) !important;
        color: white !important;
    }
    .pagination-ellipsis {
        padding: 0.5rem;
        color: var(--gray, #777777);
    }
`;

// Ajouter les styles si pas déjà présents
if (!document.getElementById('pagination-styles')) {
    const style = document.createElement('style');
    style.id = 'pagination-styles';
    style.textContent = paginationStyles;
    document.head.appendChild(style);
}

// ========== Recherche/Filtres ==========
function createSearchBar(placeholder, onSearch, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="search-container">
            <input type="text" 
                   class="search-input" 
                   placeholder="${placeholder}" 
                   id="${containerId}-input"
                   oninput="debounceSearch('${containerId}-input', ${onSearch})">
            <i class="fas fa-search search-icon"></i>
        </div>
    `;
}

// Debounce pour la recherche
let searchTimeout = null;
function debounceSearch(inputId, callback) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        callback(input.value);
    }, 300);
}

// Styles pour la recherche
const searchStyles = `
    .search-container {
        position: relative;
        margin-bottom: 1rem;
    }
    .search-input {
        width: 100%;
        padding: 0.75rem 1rem 0.75rem 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: var(--dark-bg, #25262A);
        color: var(--white, #FFFFFF);
        border-radius: 8px;
        font-size: 0.9rem;
        font-family: 'Roboto Mono', monospace;
        transition: all 0.3s ease;
    }
    .search-input:hover {
        border-color: rgba(255, 255, 255, 0.2);
    }
    .search-input:focus {
        outline: none;
        border-color: var(--green, #4DBA87);
        box-shadow: 0 0 0 3px rgba(77, 186, 135, 0.15);
        background: var(--light-bg, #2D2E32);
    }
    .search-input::placeholder {
        color: var(--gray, #777777);
        opacity: 0.7;
    }
    .search-icon {
        position: absolute;
        left: 0.75rem;
        top: 50%;
        transform: translateY(-50%);
        color: var(--gray, #777777);
        pointer-events: none;
    }
`;

if (!document.getElementById('search-styles')) {
    const style = document.createElement('style');
    style.id = 'search-styles';
    style.textContent = searchStyles;
    document.head.appendChild(style);
}

// ========== Export des données ==========
function exportToJSON(data, filename) {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function exportToCSV(data, filename) {
    if (!data || data.length === 0) {
        alert('Aucune donnée à exporter');
        return;
    }
    
    // Obtenir les clés (colonnes)
    const keys = Object.keys(data[0]);
    
    // Créer l'en-tête CSV
    let csv = keys.join(',') + '\n';
    
    // Ajouter les lignes
    data.forEach(row => {
        const values = keys.map(key => {
            const value = row[key] || '';
            // Échapper les virgules et guillemets
            if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
                return `"${value.replace(/"/g, '""')}"`;
            }
            return value;
        });
        csv += values.join(',') + '\n';
    });
    
    // Télécharger
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function createExportButtons(onExportJSON, onExportCSV, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="export-buttons">
            <button class="btn btn-secondary btn-sm" onclick="${onExportJSON}">
                <i class="fas fa-file-code"></i> Exporter JSON
            </button>
            <button class="btn btn-secondary btn-sm" onclick="${onExportCSV}">
                <i class="fas fa-file-csv"></i> Exporter CSV
            </button>
        </div>
    `;
}

// Styles pour les boutons d'export
const exportStyles = `
    .export-buttons {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
`;

if (!document.getElementById('export-styles')) {
    const style = document.createElement('style');
    style.id = 'export-styles';
    style.textContent = exportStyles;
    document.head.appendChild(style);
}

