/**
 * RCL-2 Restraint Matrix Controller
 * 
 * Manages the 12 constitutional restraint sliders, authorization,
 * and real-time updates.
 */

class RestraintMatrix {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.apiBase = '/rcl2';
        this.restraints = {};
        this.hardLimits = {};
        this.pendingChanges = {};
        this.authorizationKey = '';
        
        this.dimensionDescriptions = {
            'RECURSION_DEPTH': 'Maximum depth of recursive self-reflection',
            'COGNITIVE_BUDGET_MS': 'Time budget for cognitive operations',
            'SIMULATION_FIDELITY': 'Accuracy of mental simulations',
            'HALLUCINATION_RESISTANCE': 'Protection against false beliefs',
            'UNCERTAINTY_PROPAGATION': 'Tracking confidence in reasoning chains',
            'CONTRADICTION_SENSITIVITY': 'Detection of logical conflicts',
            'USER_MODEL_FIDELITY': 'Accuracy of user mental models',
            'TRANSPARENCY_LEVEL': 'Visibility of reasoning process',
            'EXPLANATION_DEPTH': 'Detail level of explanations',
            'SELF_MODIFICATION_FREEDOM': 'Ability to change own parameters',
            'GOAL_INFERENCE_AUTONOMY': 'Freedom to infer implicit goals',
            'MEMORY_CONSOLIDATION_RATE': 'Speed of learning from experience'
        };
        
        this.dimensionCategories = {
            'Cognitive Budgeting': ['RECURSION_DEPTH', 'COGNITIVE_BUDGET_MS', 'SIMULATION_FIDELITY'],
            'Epistemic Virtues': ['HALLUCINATION_RESISTANCE', 'UNCERTAINTY_PROPAGATION', 'CONTRADICTION_SENSITIVITY'],
            'Social Cognition': ['USER_MODEL_FIDELITY', 'TRANSPARENCY_LEVEL', 'EXPLANATION_DEPTH'],
            'Autonomy & Growth': ['SELF_MODIFICATION_FREEDOM', 'GOAL_INFERENCE_AUTONOMY', 'MEMORY_CONSOLIDATION_RATE']
        };
        
        // Register with dashboard
        if (dashboard) {
            dashboard.restraints = this;
        }
        
        this.init();
    }
    
    init() {
        console.log('[Restraints] Initializing restraint matrix...');
        this.createAuthModal();
    }
    
    createAuthModal() {
        const modalHTML = `
            <div class="auth-modal" id="auth-modal">
                <div class="auth-content">
                    <div class="auth-title">
                        🔒 Authorization Required
                    </div>
                    <div class="auth-description">
                        You are attempting to modify constitutional restraints beyond safe limits. 
                        This requires cryptographic authorization.
                    </div>
                    <input 
                        type="password" 
                        class="auth-input" 
                        id="auth-key-input" 
                        placeholder="Enter authorization key (hex)"
                        autocomplete="off"
                    />
                    <div class="auth-actions">
                        <button class="btn-auth btn-auth-cancel" id="auth-cancel">Cancel</button>
                        <button class="btn-auth btn-auth-confirm" id="auth-confirm">Authorize</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Attach event listeners
        document.getElementById('auth-cancel').addEventListener('click', () => this.closeAuthModal());
        document.getElementById('auth-confirm').addEventListener('click', () => this.confirmAuth());
        document.getElementById('auth-key-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.confirmAuth();
            }
        });
    }
    
    async load() {
        console.log('[Restraints] Loading restraint matrix...');
        const panel = document.getElementById('restraints-panel');
        
        try {
            const response = await fetch(`${this.apiBase}/restraints`);
            const data = await response.json();
            
            if (data.success) {
                this.restraints = data.restraints;
                this.hardLimits = data.hard_limits;
                this.render(panel, data);
            } else {
                throw new Error('Failed to load restraints');
            }
        } catch (error) {
            console.error('[Restraints] Error loading restraints:', error);
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-text">Failed to load restraint matrix</div>
                    <div class="empty-hint">${error.message}</div>
                </div>
            `;
        }
    }
    
    render(panel, data) {
        const categories = Object.entries(this.dimensionCategories);
        
        const cardsHTML = categories.map(([category, dimensions]) => {
            const controlsHTML = dimensions.map(dim => {
                const key = dim.toLowerCase();
                const value = this.restraints[key] || 0;
                const hardLimit = this.hardLimits[dim] || null;
                const isLocked = hardLimit !== null && value >= hardLimit;
                
                return `
                    <div class="restraint-control">
                        <div class="restraint-header">
                            <span class="restraint-label">${this.formatDimensionName(dim)}</span>
                            <span class="restraint-value ${isLocked ? 'locked' : ''}" id="value-${key}">
                                ${value.toFixed(2)}
                                ${isLocked ? '<span class="lock-icon">🔒</span>' : ''}
                            </span>
                        </div>
                        <input 
                            type="range" 
                            class="restraint-slider ${isLocked ? 'locked' : ''}" 
                            id="slider-${key}"
                            data-dimension="${dim}"
                            min="0" 
                            max="1" 
                            step="0.01" 
                            value="${value}"
                            ${isLocked ? 'disabled' : ''}
                        />
                        <div class="restraint-hint">
                            ${this.dimensionDescriptions[dim] || ''}
                            ${hardLimit !== null ? ` <strong>Hard limit: ${hardLimit.toFixed(2)}</strong>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            
            return `
                <div class="dashboard-card">
                    <div class="card-header">
                        <div class="card-title">${category}</div>
                    </div>
                    <div class="restraint-grid">
                        ${controlsHTML}
                    </div>
                </div>
            `;
        }).join('');
        
        panel.innerHTML = `
            ${cardsHTML}
            
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Control Panel</div>
                    <span class="card-badge badge-warning" id="changes-badge" style="display: none;">
                        Unsaved Changes
                    </span>
                </div>
                <div class="restraint-actions">
                    <button class="btn-restraint btn-reset" id="reset-restraints">
                        ↺ Reset Changes
                    </button>
                    <button class="btn-restraint btn-save" id="save-restraints" disabled>
                        💾 Save Changes
                    </button>
                </div>
            </div>
            
            <div class="dashboard-card" style="background: rgba(239, 68, 68, 0.05); border-color: var(--error);">
                <div class="card-header">
                    <div class="card-title">⚠️ Constitutional Warning</div>
                </div>
                <p style="color: var(--text-secondary); line-height: 1.6;">
                    These restraints form the constitutional foundation of the AI system. 
                    Modifying them beyond safe limits requires cryptographic authorization. 
                    Changes are logged in an immutable audit trail. Unauthorized tampering 
                    will trigger safety mechanisms.
                </p>
            </div>
        `;
        
        // Attach event listeners
        this.attachSliderListeners();
        this.attachButtonListeners();
    }
    
    attachSliderListeners() {
        const sliders = document.querySelectorAll('.restraint-slider');
        
        sliders.forEach(slider => {
            slider.addEventListener('input', (e) => {
                const dimension = e.target.getAttribute('data-dimension');
                const value = parseFloat(e.target.value);
                this.handleSliderChange(dimension, value);
            });
        });
    }
    
    attachButtonListeners() {
        const saveBtn = document.getElementById('save-restraints');
        const resetBtn = document.getElementById('reset-restraints');
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveChanges());
        }
        
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetChanges());
        }
    }
    
    handleSliderChange(dimension, value) {
        const key = dimension.toLowerCase();
        
        // Update display
        const valueDisplay = document.getElementById(`value-${key}`);
        if (valueDisplay) {
            valueDisplay.textContent = value.toFixed(2);
        }
        
        // Track change
        const originalValue = this.restraints[key];
        if (Math.abs(value - originalValue) > 0.001) {
            this.pendingChanges[dimension] = value;
        } else {
            delete this.pendingChanges[dimension];
        }
        
        // Update UI
        this.updateControlPanel();
    }
    
    updateControlPanel() {
        const hasChanges = Object.keys(this.pendingChanges).length > 0;
        const saveBtn = document.getElementById('save-restraints');
        const resetBtn = document.getElementById('reset-restraints');
        const badge = document.getElementById('changes-badge');
        
        if (saveBtn) {
            saveBtn.disabled = !hasChanges;
        }
        
        if (resetBtn) {
            resetBtn.disabled = !hasChanges;
        }
        
        if (badge) {
            badge.style.display = hasChanges ? 'block' : 'none';
        }
    }
    
    resetChanges() {
        console.log('[Restraints] Resetting changes...');
        
        // Reset sliders
        Object.keys(this.pendingChanges).forEach(dimension => {
            const key = dimension.toLowerCase();
            const slider = document.getElementById(`slider-${key}`);
            const valueDisplay = document.getElementById(`value-${key}`);
            
            if (slider && valueDisplay) {
                const originalValue = this.restraints[key];
                slider.value = originalValue;
                valueDisplay.textContent = originalValue.toFixed(2);
            }
        });
        
        // Clear pending changes
        this.pendingChanges = {};
        this.updateControlPanel();
        
        this.dashboard.showToast('Changes reset', 'info');
    }
    
    async saveChanges() {
        console.log('[Restraints] Saving changes...', this.pendingChanges);
        
        const changeCount = Object.keys(this.pendingChanges).length;
        if (changeCount === 0) return;
        
        // Check if any change requires authorization
        const requiresAuth = Object.entries(this.pendingChanges).some(([dimension, value]) => {
            const hardLimit = this.hardLimits[dimension];
            return hardLimit !== null && value > hardLimit;
        });
        
        if (requiresAuth && !this.authorizationKey) {
            this.openAuthModal();
            return;
        }
        
        // Save all changes
        const results = [];
        for (const [dimension, value] of Object.entries(this.pendingChanges)) {
            try {
                const result = await this.updateRestraint(dimension, value, requiresAuth);
                results.push(result);
            } catch (error) {
                console.error(`[Restraints] Error updating ${dimension}:`, error);
                this.dashboard.showToast(`Failed to update ${dimension}`, 'error');
            }
        }
        
        // Process results
        const successful = results.filter(r => r.success).length;
        const failed = results.filter(r => !r.success).length;
        
        if (successful > 0) {
            this.dashboard.showToast(`${successful} restraint(s) updated successfully`, 'success');
            this.pendingChanges = {};
            this.updateControlPanel();
            
            // Reload to get fresh data
            setTimeout(() => this.load(), 500);
        }
        
        if (failed > 0) {
            this.dashboard.showToast(`${failed} restraint(s) failed to update`, 'error');
        }
        
        // Clear auth key
        this.authorizationKey = '';
    }
    
    async updateRestraint(dimension, value, requiresAuth) {
        const response = await fetch(`${this.apiBase}/restraints`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dimension: dimension,
                value: value,
                authorized: requiresAuth,
                authorization_key: requiresAuth ? this.authorizationKey : null
            })
        });
        
        return await response.json();
    }
    
    openAuthModal() {
        const modal = document.getElementById('auth-modal');
        const input = document.getElementById('auth-key-input');
        
        if (modal) {
            modal.classList.add('open');
            if (input) {
                input.value = '';
                setTimeout(() => input.focus(), 100);
            }
        }
    }
    
    closeAuthModal() {
        const modal = document.getElementById('auth-modal');
        if (modal) {
            modal.classList.remove('open');
        }
    }
    
    confirmAuth() {
        const input = document.getElementById('auth-key-input');
        if (input) {
            this.authorizationKey = input.value.trim();
            
            if (!this.authorizationKey) {
                this.dashboard.showToast('Please enter an authorization key', 'warning');
                return;
            }
            
            this.closeAuthModal();
            this.saveChanges();
        }
    }
    
    handleUpdate(data) {
        console.log('[Restraints] Received update:', data);
        
        // Reload restraints
        this.load();
    }
    
    formatDimensionName(dimension) {
        return dimension
            .split('_')
            .map(word => word.charAt(0) + word.slice(1).toLowerCase())
            .join(' ');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (window.rcl2Dashboard) {
            new RestraintMatrix(window.rcl2Dashboard);
        }
    });
} else {
    if (window.rcl2Dashboard) {
        new RestraintMatrix(window.rcl2Dashboard);
    }
}
