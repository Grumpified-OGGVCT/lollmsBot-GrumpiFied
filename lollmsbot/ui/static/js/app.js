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
    content.textContent = 'Loading audit log...';
    
    try {
        const response = await fetch('/ui-api/security/audit?limit=50');
        const data = await response.json();
        
        if (data.events && data.events.length > 0) {
            // Clear previous content before rendering events
            content.innerHTML = '';

            data.events.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'audit-event';

                const headerDiv = document.createElement('div');
                headerDiv.className = 'audit-event-header';

                const typeSpan = document.createElement('span');
                typeSpan.className = 'audit-event-type';

                const levelSpan = document.createElement('span');
                levelSpan.className = 'audit-event-level ' + (event.threat_level || '');
                levelSpan.textContent = event.threat_level || '';

                const eventTypeText = document.createTextNode(' ' + (event.event_type || ''));

                const timeSpan = document.createElement('span');
                timeSpan.className = 'audit-event-time';
                timeSpan.textContent = new Date(event.timestamp).toLocaleString();

                typeSpan.appendChild(levelSpan);
                typeSpan.appendChild(eventTypeText);

                headerDiv.appendChild(typeSpan);
                headerDiv.appendChild(timeSpan);

                const descriptionDiv = document.createElement('div');
                descriptionDiv.className = 'audit-event-description';
                descriptionDiv.textContent = event.description || '';

                const sourceDiv = document.createElement('div');
                sourceDiv.className = 'audit-event-source';
                sourceDiv.textContent = 'Source: ' + (event.source || 'unknown');

                eventDiv.appendChild(headerDiv);
                eventDiv.appendChild(descriptionDiv);
                eventDiv.appendChild(sourceDiv);

                content.appendChild(eventDiv);
            });
        } else {
            content.textContent = 'No audit events found.';
        }
    } catch (error) {
        console.error('Failed to load audit log:', error);
        content.textContent = 'Failed to load audit log.';
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
            // Clear existing content and safely build the DOM tree
            content.innerHTML = '';
            
            data.scanned.forEach(skill => {
                const item = document.createElement('div');
                item.className = 'skill-scan-item';

                const header = document.createElement('div');
                header.className = 'skill-scan-header';

                const nameSpan = document.createElement('span');
                nameSpan.className = 'skill-scan-name';
                nameSpan.textContent = skill.name || '';

                const badgeSpan = document.createElement('span');
                badgeSpan.className = 'skill-scan-badge ' + (skill.is_safe ? 'safe' : 'unsafe');
                badgeSpan.textContent = skill.is_safe ? '✅ Safe' : '⚠️ Unsafe';

                header.appendChild(nameSpan);
                header.appendChild(badgeSpan);
                item.appendChild(header);

                if (!skill.is_safe && Array.isArray(skill.threats) && skill.threats.length > 0) {
                    const threatsContainer = document.createElement('div');
                    threatsContainer.className = 'skill-scan-threats';

                    const strongEl = document.createElement('strong');
                    strongEl.textContent = 'Threats Detected:';
                    threatsContainer.appendChild(strongEl);

                    const ul = document.createElement('ul');
                    skill.threats.forEach(threat => {
                        const li = document.createElement('li');
                        li.textContent = threat || '';
                        ul.appendChild(li);
                    });
                    threatsContainer.appendChild(ul);
                    item.appendChild(threatsContainer);
                }

                content.appendChild(item);
            });
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
