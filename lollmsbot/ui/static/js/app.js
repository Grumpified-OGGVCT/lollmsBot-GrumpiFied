// LollmsBot Web UI - Main Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initSettings();
    initSecurityUI();
    initModals();
    
    console.log('LollmsBot UI initialized');
});

// Settings Management
function initSettings() {
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettings = document.getElementById('close-settings');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    const saveSettings = document.getElementById('save-settings');
    
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
    
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
    
    if (saveSettings) {
        saveSettings.addEventListener('click', function() {
            // Save settings logic would go here
            console.log('Settings saved');
            settingsModal.classList.remove('active');
        });
    }
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        if (content.dataset.tabContent === tabName) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// Security UI Management
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
        
        const events24hEl = document.getElementById('events-24h');
        if (events24hEl) {
            events24hEl.textContent = data.events_24h || 0;
        }
        
        const quarantineEl = document.getElementById('quarantine-status');
        if (quarantineEl) {
            quarantineEl.textContent = data.quarantine_active ? '⚠️ Yes' : '✅ No';
            quarantineEl.style.color = data.quarantine_active ? '#ef4444' : '#10b981';
        }
        
        // Update protection status
        updateProtectionStatus('api-key-protection', data.api_key_protection);
        updateProtectionStatus('skill-scanning', data.skill_scanning);
        updateProtectionStatus('container-protection', data.container_protection);
        
    } catch (error) {
        console.error('Failed to load security status:', error);
        const statusEl = document.getElementById('guardian-status');
        if (statusEl) {
            statusEl.textContent = '❌ Error';
        }
    }
}

function updateProtectionStatus(elementId, enabled) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = enabled ? '✅' : '❌';
    }
}

async function showAuditLog() {
    const modal = document.getElementById('audit-log-modal');
    const content = document.getElementById('audit-log-content');
    
    if (!modal || !content) return;
    
    modal.classList.add('active');
    content.innerHTML = '<p>Loading audit log...</p>';
    
    try {
        const response = await fetch('/ui-api/security/audit?limit=50');
        const data = await response.json();
        
        if (data.events && data.events.length > 0) {
            content.innerHTML = data.events.map(event => `
                <div class="audit-event">
                    <div class="audit-event-header">
                        <span class="audit-event-type">
                            <span class="audit-event-level ${event.threat_level}">${event.threat_level}</span>
                            ${event.event_type}
                        </span>
                        <span class="audit-event-time">${new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="audit-event-description">${event.description}</div>
                    <div class="audit-event-source">Source: ${event.source}</div>
                </div>
            `).join('');
        } else {
            content.innerHTML = '<p>No audit events found.</p>';
        }
    } catch (error) {
        console.error('Failed to load audit log:', error);
        content.innerHTML = '<p>Failed to load audit log.</p>';
    }
}

async function showSkillScans() {
    const modal = document.getElementById('skill-scans-modal');
    const content = document.getElementById('skill-scans-content');
    
    if (!modal || !content) return;
    
    modal.classList.add('active');
    content.innerHTML = '<p>Loading skill scans...</p>';
    
    try {
        const response = await fetch('/ui-api/security/skills');
        const data = await response.json();
        
        if (!data.available) {
            content.innerHTML = '<p>Skill scanning not available or no skills scanned yet.</p>';
            return;
        }
        
        if (data.scanned && data.scanned.length > 0) {
            content.innerHTML = data.scanned.map(skill => `
                <div class="skill-scan-item">
                    <div class="skill-scan-header">
                        <span class="skill-scan-name">${skill.name}</span>
                        <span class="skill-scan-badge ${skill.is_safe ? 'safe' : 'unsafe'}">
                            ${skill.is_safe ? '✅ Safe' : '⚠️ Unsafe'}
                        </span>
                    </div>
                    ${!skill.is_safe && skill.threats && skill.threats.length > 0 ? `
                        <div class="skill-scan-threats">
                            <strong>Threats Detected:</strong>
                            <ul>
                                ${skill.threats.map(threat => `<li>${threat}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } else {
            content.innerHTML = '<p>No skills have been scanned yet.</p>';
        }
    } catch (error) {
        console.error('Failed to load skill scans:', error);
        content.innerHTML = '<p>Failed to load skill scans.</p>';
    }
}

// Modal Management
function initModals() {
    // Audit Log Modal
    const auditLogModal = document.getElementById('audit-log-modal');
    const closeAuditLog = document.getElementById('close-audit-log');
    const closeAuditLogBtn = document.getElementById('close-audit-log-btn');
    
    if (closeAuditLog) {
        closeAuditLog.addEventListener('click', () => {
            auditLogModal.classList.remove('active');
        });
    }
    
    if (closeAuditLogBtn) {
        closeAuditLogBtn.addEventListener('click', () => {
            auditLogModal.classList.remove('active');
        });
    }
    
    // Skill Scans Modal
    const skillScansModal = document.getElementById('skill-scans-modal');
    const closeSkillScans = document.getElementById('close-skill-scans');
    const closeSkillScansBtn = document.getElementById('close-skill-scans-btn');
    
    if (closeSkillScans) {
        closeSkillScans.addEventListener('click', () => {
            skillScansModal.classList.remove('active');
        });
    }
    
    if (closeSkillScansBtn) {
        closeSkillScansBtn.addEventListener('click', () => {
            skillScansModal.classList.remove('active');
        });
    }
    
    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });
}

// Export for other modules
window.LollmsUI = {
    loadSecurityStatus,
    showAuditLog,
    showSkillScans,
    switchTab
};
