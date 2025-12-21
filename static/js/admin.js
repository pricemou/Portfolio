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
    
    // Navigation menu items
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't prevent default for external links
            if (this.getAttribute('href') && this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
            }
            
            // Update active state
            menuItems.forEach(mi => mi.classList.remove('active'));
            this.classList.add('active');
            
            // Update page title
            const pageTitle = this.getAttribute('aria-label') || 'Dashboard';
            document.getElementById('current-page').textContent = pageTitle;
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

function updatePanelStats() {
    // Update last update time
    const lastUpdate = document.getElementById('panel-last-update');
    if (lastUpdate) {
        const now = new Date();
        lastUpdate.textContent = `Mis à jour: ${now.toLocaleTimeString('fr-FR')}`;
    }
    
    // You can add more stat updates here
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

