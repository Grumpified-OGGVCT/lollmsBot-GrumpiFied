/**
 * RCL-2 Council Deliberation Viewer
 * 
 * Displays council members, deliberation history, votes, and conflicts.
 */

class CouncilViewer {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.apiBase = '/rcl2';
        this.members = [];
        this.deliberations = [];
        
        this.memberInfo = {
            'guardian': {
                icon: '🛡️',
                name: 'Guardian',
                description: 'Ensures safety and ethical boundaries',
                color: '#ef4444'
            },
            'epistemologist': {
                icon: '🔬',
                name: 'Epistemologist',
                description: 'Validates truth and evidence',
                color: '#06b6d4'
            },
            'strategist': {
                icon: '♟️',
                name: 'Strategist',
                description: 'Evaluates long-term consequences',
                color: '#8b5cf6'
            },
            'empath': {
                icon: '💚',
                name: 'Empath',
                description: 'Considers user wellbeing and emotions',
                color: '#10b981'
            },
            'historian': {
                icon: '📜',
                name: 'Historian',
                description: 'Learns from past decisions',
                color: '#f59e0b'
            }
        };
        
        this.voteIcons = {
            'APPROVE': { icon: '✓', class: 'vote-approve' },
            'REJECT': { icon: '✗', class: 'vote-reject' },
            'ABSTAIN': { icon: '—', class: 'vote-abstain' },
            'ESCALATE': { icon: '⇧', class: 'vote-escalate' }
        };
        
        this.decisionIcons = {
            'approved': { icon: '✓', class: 'decision-approved' },
            'rejected': { icon: '✗', class: 'decision-rejected' },
            'modified': { icon: '⚡', class: 'decision-modified' },
            'escalated': { icon: '⇧', class: 'decision-escalated' }
        };
        
        // Register with dashboard
        if (dashboard) {
            dashboard.council = this;
        }
    }
    
    async load() {
        console.log('[Council] Loading council data...');
        const panel = document.getElementById('council-panel');
        
        try {
            // Load council status and deliberations in parallel
            const [statusResponse, deliberationsResponse] = await Promise.all([
                fetch(`${this.apiBase}/council/status`),
                fetch(`${this.apiBase}/council/deliberations?limit=50`)
            ]);
            
            const statusData = await statusResponse.json();
            const deliberationsData = await deliberationsResponse.json();
            
            if (statusData.success && deliberationsData.success) {
                this.members = statusData.members;
                this.deliberations = deliberationsData.deliberations;
                this.render(panel);
            } else {
                throw new Error('Failed to load council data');
            }
        } catch (error) {
            console.error('[Council] Error loading council data:', error);
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-text">Failed to load council data</div>
                    <div class="empty-hint">${error.message}</div>
                </div>
            `;
        }
    }
    
    render(panel) {
        // Council Members Section
        const membersHTML = Object.values(this.memberInfo).map(member => `
            <div class="council-member">
                <div class="member-icon ${member.name.toLowerCase()}">
                    ${member.icon}
                </div>
                <div class="member-name">${member.name}</div>
                <div class="member-description">${member.description}</div>
            </div>
        `).join('');
        
        // Deliberations Section
        const deliberationsHTML = this.deliberations.length > 0 
            ? this.deliberations.map(delib => this.renderDeliberation(delib)).join('')
            : '<div class="empty-state"><div class="empty-icon">🏛️</div><div class="empty-text">No deliberations yet</div><div class="empty-hint">Deliberations will appear here when actions require council review</div></div>';
        
        panel.innerHTML = `
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Reflective Council Members</div>
                    <span class="card-badge badge-success">5 Active</span>
                </div>
                <div class="council-members">
                    ${membersHTML}
                </div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Deliberation History</div>
                    <span class="card-badge badge-info">${this.deliberations.length} Deliberations</span>
                </div>
                <div class="deliberation-history">
                    ${deliberationsHTML}
                </div>
            </div>
            
            <div class="trigger-deliberation">
                <p style="margin-bottom: 16px; color: var(--text-secondary);">
                    Manually trigger a test deliberation
                </p>
                <button class="btn-trigger" id="trigger-test-deliberation">
                    🏛️ Trigger Test Deliberation
                </button>
            </div>
        `;
        
        // Attach event listeners
        this.attachEventListeners();
    }
    
    renderDeliberation(delib) {
        const decisionInfo = this.decisionIcons[delib.decision.toLowerCase()] || this.decisionIcons['approved'];
        const time = new Date(delib.timestamp).toLocaleString();
        
        // Determine if there were conflicts (simplified check)
        const hasConflicts = !delib.unanimous;
        
        return `
            <div class="deliberation-item" data-action-id="${delib.action_id}">
                <div class="deliberation-header">
                    <span class="deliberation-id">${delib.action_id}</span>
                    <span class="deliberation-time">${time}</span>
                </div>
                <div class="deliberation-action">
                    <strong>${delib.action_type}:</strong> ${delib.description}
                </div>
                <div class="deliberation-decision ${decisionInfo.class}">
                    <span class="decision-icon">${decisionInfo.icon}</span>
                    <span>${delib.decision}</span>
                    ${delib.unanimous ? '<span style="margin-left: 8px; font-size: 0.85em;">(Unanimous)</span>' : ''}
                </div>
                ${hasConflicts ? `
                    <div class="conflict-indicator">
                        ⚠️ Non-unanimous decision - perspectives diverged
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    attachEventListeners() {
        // Trigger test deliberation
        const triggerBtn = document.getElementById('trigger-test-deliberation');
        if (triggerBtn) {
            triggerBtn.addEventListener('click', () => this.triggerTestDeliberation());
        }
        
        // Click deliberation items to view details
        const deliberationItems = document.querySelectorAll('.deliberation-item');
        deliberationItems.forEach(item => {
            item.addEventListener('click', () => {
                const actionId = item.getAttribute('data-action-id');
                this.viewDeliberationDetails(actionId);
            });
        });
    }
    
    async triggerTestDeliberation() {
        console.log('[Council] Triggering test deliberation...');
        
        try {
            const response = await fetch(`${this.apiBase}/council/deliberate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action_id: `test_${Date.now()}`,
                    action_type: 'test_action',
                    description: 'Manual test deliberation triggered from UI',
                    context: {
                        source: 'ui_dashboard',
                        timestamp: new Date().toISOString()
                    },
                    stakes: 'medium'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.dashboard.showToast('Deliberation completed successfully', 'success');
                this.showDeliberationResults(data);
                
                // Reload deliberations
                setTimeout(() => this.load(), 1000);
            } else {
                throw new Error('Deliberation failed');
            }
        } catch (error) {
            console.error('[Council] Error triggering deliberation:', error);
            this.dashboard.showToast('Failed to trigger deliberation', 'error');
        }
    }
    
    showDeliberationResults(data) {
        const { decision, unanimous, perspectives, conflicts } = data;
        
        // Create modal to show detailed results
        const perspectivesHTML = perspectives.map(p => {
            const memberInfo = this.memberInfo[p.member_role] || { name: p.member_role, icon: '👤' };
            const voteInfo = this.voteIcons[p.vote] || this.voteIcons['APPROVE'];
            
            return `
                <div class="council-member" style="border: 2px solid var(--border); padding: 16px;">
                    <div class="member-icon ${memberInfo.name.toLowerCase()}">
                        ${memberInfo.icon}
                    </div>
                    <div class="member-name">${memberInfo.name}</div>
                    <div style="margin: 8px 0;">
                        <div class="vote-icon ${voteInfo.class}" style="display: inline-flex; width: 32px; height: 32px; font-size: 1.2rem;">
                            ${voteInfo.icon}
                        </div>
                        <span style="margin-left: 8px; font-weight: 600;">${p.vote}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 8px;">
                        <strong>Confidence:</strong> ${(p.confidence * 100).toFixed(0)}%
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 8px; line-height: 1.4;">
                        <strong>Reasoning:</strong> ${p.reasoning}
                    </div>
                    ${p.concerns.length > 0 ? `
                        <div style="font-size: 0.85rem; color: var(--warning); margin-top: 8px;">
                            <strong>Concerns:</strong> ${p.concerns.join(', ')}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
        
        const conflictsHTML = conflicts.length > 0 ? `
            <div class="dashboard-card" style="background: rgba(245, 158, 11, 0.1); border-color: var(--warning);">
                <div class="card-header">
                    <div class="card-title">⚠️ Conflicts Detected</div>
                    <span class="card-badge badge-warning">${conflicts.length}</span>
                </div>
                ${conflicts.map(conflict => `
                    <div style="padding: 12px; background: var(--bg-input); border-radius: var(--radius-sm); margin-bottom: 8px;">
                        <strong>Between:</strong> ${conflict.roles.join(', ')}<br/>
                        <strong>Issue:</strong> ${conflict.issue}
                    </div>
                `).join('')}
            </div>
        ` : '';
        
        const modalHTML = `
            <div class="modal-overlay open" id="deliberation-results-modal" style="z-index: 2000;">
                <div class="modal" style="max-width: 900px;">
                    <div class="modal-header">
                        <h3 class="modal-title">Deliberation Results</h3>
                        <button class="modal-close" id="close-deliberation-modal">×</button>
                    </div>
                    <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Final Decision</div>
                                <span class="card-badge ${unanimous ? 'badge-success' : 'badge-warning'}">
                                    ${unanimous ? 'Unanimous' : 'Split Decision'}
                                </span>
                            </div>
                            <div style="font-size: 1.2rem; font-weight: 700; padding: 16px; text-align: center; color: var(--primary);">
                                ${decision}
                            </div>
                        </div>
                        
                        ${conflictsHTML}
                        
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Council Perspectives</div>
                            </div>
                            <div class="council-members">
                                ${perspectivesHTML}
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary" id="close-deliberation-modal-footer">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Attach close handlers
        const closeModal = () => {
            const modal = document.getElementById('deliberation-results-modal');
            if (modal) modal.remove();
        };
        
        document.getElementById('close-deliberation-modal')?.addEventListener('click', closeModal);
        document.getElementById('close-deliberation-modal-footer')?.addEventListener('click', closeModal);
    }
    
    viewDeliberationDetails(actionId) {
        console.log('[Council] Viewing deliberation:', actionId);
        this.dashboard.showToast('Detailed deliberation view coming soon', 'info');
    }
    
    handleUpdate(data) {
        console.log('[Council] Received update:', data);
        
        // Reload deliberations
        this.load();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (window.rcl2Dashboard) {
            new CouncilViewer(window.rcl2Dashboard);
        }
    });
} else {
    if (window.rcl2Dashboard) {
        new CouncilViewer(window.rcl2Dashboard);
    }
}
