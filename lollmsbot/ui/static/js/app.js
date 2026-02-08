// LollmsBot Web UI - Main Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initSettings();
    initSecurityUI();
    initModals();
    initNavigation();
    
    // Default to Chat view
    // switchView('view-chat'); // Already set active in HTML
    
    console.log('LollmsBot UI initialized');
});

// Navigation System (View-Based)
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Get view ID from data attribute
            // closest handles clicks on icon/span inside button
            const targetView = e.currentTarget.dataset.view;
            if (targetView) {
                switchView(targetView);
            }
        });
    });
}

function switchView(viewId) {
    console.log(`Switching to view: ${viewId}`);

    // 1. Update Navigation Buttons
    document.querySelectorAll('.nav-item').forEach(btn => {
        if (btn.dataset.view === viewId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // 2. Hide all Views
    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // 3. Show Target View
    const targetPanel = document.getElementById(viewId);
    if (targetPanel) {
        targetPanel.classList.add('active');
    } else {
        console.error(`Target view not found: ${viewId}`);
        return;
    }

    // 4. Trigger Module-Specific Logic (Lazy Load)
    if (viewId === 'view-hobby') {
        // Initialize Hobby if exists
        // Assuming hobby dashboard renders itself into #hobby-dashboard-mount
        if (window.hobbyDashboard) {
             // In new view model, 'open()' might just mean 'refresh data'
             // because the view is already visible via CSS.
             if (window.hobbyDashboard.onViewActive) {
                window.hobbyDashboard.onViewActive(); 
             } else {
                 // Fallback if hobby dashboard logic still expects overlay
                 // We might need to refactor hobby-dashboard.js next
             }
        }
    } else if (viewId === 'view-security') {
        loadSecurityStatus();
    }
}


// Settings Management (Modal)
function initSettings() {
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettings = document.getElementById('close-settings');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    const saveSettings = document.getElementById('save-settings');
    
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            settingsModal.classList.add('active');
            loadSecurityStatus();
        });
    }
    
    if (closeSettings) {
        closeSettings.addEventListener('click', function() {
            settingsModal.classList.remove('active');
        });
    }
    
    if (closeSettingsBtn) {
        closeSettingsBtn.addEventListener('click', function() {
            settingsModal.classList.remove('active');
        });
    }
    
    // Tab switching inside Settings Modal
    const tabBtns = document.querySelectorAll('.modal-tabs .tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active from all tabs
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.modal-body .tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            const target = this.dataset.tab;
            const content = document.querySelector(`.tab-content[data-tab-content="${target}"]`);
            if (content) content.classList.add('active');
        });
    });
}


// Security UI Connectors
function initSecurityUI() {
    const viewAuditLogBtn = document.getElementById('view-audit-log');
    const viewSkillScansBtn = document.getElementById('view-skill-scans');
    
    if (viewAuditLogBtn) {
        viewAuditLogBtn.addEventListener('click', showAuditLog);
    }
    
    if (viewSkillScansBtn) {
        viewSkillScansBtn.addEventListener('click', showSkillScans);
    }
}

async function loadSecurityStatus() {
    try {
        const response = await fetch('/ui-api/security/status');
        const data = await response.json();
        
        // Update status display
        const statusEl = document.getElementById('guardian-status');
        if (statusEl) {
            statusEl.textContent = data.status === 'active' ? '✅ Active' : '❌ Inactive';
        }
        
        // ... (Rest of logic same as before) ...
        
        updateProtectionStatus('api-key-protection', data.api_key_protection);
        updateProtectionStatus('skill-scanning', data.skill_scanning);
        updateProtectionStatus('container-protection', data.container_protection);
        
    } catch (error) {
        console.warn('Failed to load security status (API might be offline)');
    }
}

function updateProtectionStatus(elementId, enabled) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = enabled ? '✅' : '❌';
    }
}

// Modal Logic for Audit/Skills
function initModals() {
    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });
    
    // Specific close handlers
    document.getElementById('close-audit-log')?.addEventListener('click', () => {
        document.getElementById('audit-log-modal').classList.remove('active');
    });
     document.getElementById('close-skill-scans')?.addEventListener('click', () => {
        document.getElementById('skill-scans-modal').classList.remove('active');
    });
}

// Export for other modules
window.LollmsUI = {
    loadSecurityStatus,
    showAuditLog: () => document.getElementById('audit-log-modal').classList.add('active'), // Simplified
    showSkillScans: () => document.getElementById('skill-scans-modal').classList.add('active'),
    switchView
};
