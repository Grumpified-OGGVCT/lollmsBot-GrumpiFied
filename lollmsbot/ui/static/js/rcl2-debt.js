/**
 * RCL-2 Cognitive Debt Manager
 * 
 * Manages cognitive debt queue, repayment, and history tracking.
 */

class CognitiveDebtManager {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.apiBase = '/rcl2';
        this.debtItems = [];
        this.repaymentHistory = [];
        
        this.priorityLabels = {
            'high': { class: 'priority-high', label: 'High', value: 3 },
            'medium': { class: 'priority-medium', label: 'Medium', value: 2 },
            'low': { class: 'priority-low', label: 'Low', value: 1 }
        };
        
        // Register with dashboard
        if (dashboard) {
            dashboard.debt = this;
        }
    }
    
    async load() {
        console.log('[Debt] Loading cognitive debt...');
        const panel = document.getElementById('debt-panel');
        
        try {
            const response = await fetch(`${this.apiBase}/debt`);
            const data = await response.json();
            
            if (data.success) {
                this.debtItems = data.debt_items || [];
                this.render(panel, data);
            } else {
                throw new Error('Failed to load cognitive debt');
            }
        } catch (error) {
            console.error('[Debt] Error loading cognitive debt:', error);
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-text">Failed to load cognitive debt</div>
                    <div class="empty-hint">${error.message}</div>
                </div>
            `;
        }
    }
    
    render(panel, data) {
        const { outstanding_debt, debt_items } = data;
        
        // Calculate statistics
        const highPriority = debt_items.filter(d => d.priority === 'high').length;
        const mediumPriority = debt_items.filter(d => d.priority === 'medium').length;
        const lowPriority = debt_items.filter(d => d.priority === 'low').length;
        
        // Sort by priority (high to low) then by timestamp
        const sortedDebt = [...debt_items].sort((a, b) => {
            const priorityA = this.priorityLabels[a.priority]?.value || 0;
            const priorityB = this.priorityLabels[b.priority]?.value || 0;
            
            if (priorityA !== priorityB) {
                return priorityB - priorityA;
            }
            
            return new Date(b.logged_at) - new Date(a.logged_at);
        });
        
        // Render table
        const tableRowsHTML = sortedDebt.length > 0 ? sortedDebt.map(item => {
            const priorityInfo = this.priorityLabels[item.priority] || this.priorityLabels['low'];
            const time = new Date(item.logged_at).toLocaleString();
            
            return `
                <tr>
                    <td>
                        <span style="font-family: 'Fira Code', monospace; font-size: 0.85rem;">
                            ${item.decision_id}
                        </span>
                    </td>
                    <td>${item.reason}</td>
                    <td>
                        <span class="priority-indicator ${priorityInfo.class}">
                            ${priorityInfo.label}
                        </span>
                    </td>
                    <td style="font-size: 0.85rem; color: var(--text-muted);">
                        ${time}
                    </td>
                    <td>
                        <div class="debt-actions">
                            <button 
                                class="btn-repay" 
                                data-decision-id="${item.decision_id}"
                                title="Repay this debt"
                            >
                                Repay
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('') : `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <div class="empty-icon" style="font-size: 3rem; margin-bottom: 12px;">✨</div>
                    <div>No outstanding cognitive debt</div>
                    <div style="font-size: 0.85rem; margin-top: 8px;">All obligations have been fulfilled</div>
                </td>
            </tr>
        `;
        
        panel.innerHTML = `
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Cognitive Debt Overview</div>
                    <span class="card-badge ${outstanding_debt > 0 ? 'badge-warning' : 'badge-success'}">
                        ${outstanding_debt} Outstanding
                    </span>
                </div>
                
                <div class="debt-summary">
                    <div class="stat-card">
                        <div class="stat-label">Total Debt</div>
                        <div class="stat-value">${outstanding_debt}</div>
                        <div class="stat-sublabel">Items requiring attention</div>
                    </div>
                    
                    <div class="stat-card" style="border-left: 3px solid var(--error);">
                        <div class="stat-label">High Priority</div>
                        <div class="stat-value" style="color: var(--error);">${highPriority}</div>
                        <div class="stat-sublabel">Urgent obligations</div>
                    </div>
                    
                    <div class="stat-card" style="border-left: 3px solid var(--warning);">
                        <div class="stat-label">Medium Priority</div>
                        <div class="stat-value" style="color: var(--warning);">${mediumPriority}</div>
                        <div class="stat-sublabel">Important obligations</div>
                    </div>
                    
                    <div class="stat-card" style="border-left: 3px solid var(--text-muted);">
                        <div class="stat-label">Low Priority</div>
                        <div class="stat-value" style="color: var(--text-muted);">${lowPriority}</div>
                        <div class="stat-sublabel">Routine obligations</div>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Outstanding Debt Queue</div>
                </div>
                
                <div style="overflow-x: auto;">
                    <table class="debt-table">
                        <thead>
                            <tr>
                                <th>Decision ID</th>
                                <th>Reason</th>
                                <th>Priority</th>
                                <th>Logged At</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableRowsHTML}
                        </tbody>
                    </table>
                </div>
                
                ${outstanding_debt > 0 ? `
                    <button class="btn-repay-all" id="repay-all-btn">
                        💳 Repay All Outstanding Debt (${outstanding_debt} items)
                    </button>
                ` : ''}
            </div>
            
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">About Cognitive Debt</div>
                </div>
                <div style="color: var(--text-secondary); line-height: 1.8; font-size: 0.95rem;">
                    <p style="margin-bottom: 12px;">
                        <strong>Cognitive debt</strong> occurs when the system makes quick decisions under time 
                        pressure or uncertainty, deferring deeper analysis. Like technical debt, it must be 
                        repaid to maintain epistemic integrity.
                    </p>
                    <p style="margin-bottom: 12px;">
                        <strong>High priority debt</strong> indicates decisions with significant uncertainty or 
                        potential impact that require reflection. The system will automatically attempt to repay 
                        debt during idle periods, but manual repayment ensures immediate resolution.
                    </p>
                    <p>
                        <strong>Repayment</strong> involves revisiting the decision context, gathering additional 
                        information, and updating internal models based on deeper analysis.
                    </p>
                </div>
            </div>
        `;
        
        // Attach event listeners
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        // Individual repay buttons
        const repayButtons = document.querySelectorAll('.btn-repay');
        repayButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const decisionId = btn.getAttribute('data-decision-id');
                this.repayDebt(decisionId);
            });
        });
        
        // Repay all button
        const repayAllBtn = document.getElementById('repay-all-btn');
        if (repayAllBtn) {
            repayAllBtn.addEventListener('click', () => this.repayAllDebt());
        }
    }
    
    async repayDebt(decisionId) {
        console.log('[Debt] Repaying debt:', decisionId);
        
        try {
            const response = await fetch(`${this.apiBase}/debt/repay`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    decision_id: decisionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.dashboard.showToast(`Debt repaid: ${decisionId}`, 'success');
                
                // Reload debt data
                setTimeout(() => this.load(), 500);
            } else {
                throw new Error(data.message || 'Failed to repay debt');
            }
        } catch (error) {
            console.error('[Debt] Error repaying debt:', error);
            this.dashboard.showToast('Failed to repay debt', 'error');
        }
    }
    
    async repayAllDebt() {
        console.log('[Debt] Repaying all debt...');
        
        if (this.debtItems.length === 0) {
            this.dashboard.showToast('No debt to repay', 'info');
            return;
        }
        
        // Show confirmation
        if (!confirm(`Repay all ${this.debtItems.length} outstanding debt items? This may take some time.`)) {
            return;
        }
        
        this.dashboard.showToast('Repaying all debt...', 'info');
        
        let successCount = 0;
        let failCount = 0;
        
        // Repay each debt item
        for (const item of this.debtItems) {
            try {
                const response = await fetch(`${this.apiBase}/debt/repay`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        decision_id: item.decision_id
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                console.error('[Debt] Error repaying debt:', item.decision_id, error);
                failCount++;
            }
        }
        
        // Show results
        if (successCount > 0) {
            this.dashboard.showToast(`Successfully repaid ${successCount} debt item(s)`, 'success');
        }
        
        if (failCount > 0) {
            this.dashboard.showToast(`Failed to repay ${failCount} debt item(s)`, 'error');
        }
        
        // Reload debt data
        setTimeout(() => this.load(), 1000);
    }
    
    handleUpdate(data) {
        console.log('[Debt] Received update:', data);
        
        // Reload debt
        this.load();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (window.rcl2Dashboard) {
            new CognitiveDebtManager(window.rcl2Dashboard);
        }
    });
} else {
    if (window.rcl2Dashboard) {
        new CognitiveDebtManager(window.rcl2Dashboard);
    }
}
