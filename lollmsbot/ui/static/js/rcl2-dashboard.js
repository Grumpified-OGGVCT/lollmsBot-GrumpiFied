/**
 * RCL-2 Cognitive Dashboard - Main Controller
 * 
 * Handles dashboard initialization, tab switching, WebSocket connections,
 * and coordination between sub-components.
 */

class RCL2Dashboard {
    constructor() {
        this.isOpen = false;
        this.currentTab = 'restraints';
        this.ws = null;
        this.wsReconnectTimer = null;
        this.wsReconnectDelay = 3000;
        this.apiBase = '/rcl2';
        
        // Sub-components (initialized by their respective modules)
        this.restraints = null;
        this.council = null;
        this.debt = null;
        
        this.init();
    }
    
    init() {
        console.log('[RCL2] Initializing dashboard...');
        this.createDashboardHTML();
        this.attachEventListeners();
        this.initializeWebSocket();
    }
    
    createDashboardHTML() {
        // Create dashboard container
        const dashboardHTML = `
            <div class="cognitive-dashboard" id="cognitive-dashboard">
                <div class="dashboard-container">
                    <!-- Header -->
                    <div class="dashboard-header">
                        <div class="dashboard-title">
                            <div class="dashboard-icon">🧠</div>
                            <span>Cognitive Dashboard</span>
                            <span class="card-badge badge-info">RCL-2</span>
                        </div>
                        <button class="dashboard-close" id="close-dashboard" title="Close">×</button>
                    </div>
                    
                    <!-- Tab Navigation -->
                    <div class="dashboard-tabs">
                        <button class="tab-btn active" data-tab="restraints">Restraint Matrix</button>
                        <button class="tab-btn" data-tab="cognitive">Cognitive State</button>
                        <button class="tab-btn" data-tab="council">Council</button>
                        <button class="tab-btn" data-tab="debt">Cognitive Debt</button>
                        <button class="tab-btn" data-tab="audit">Audit Trail</button>
                        <button class="tab-btn" data-tab="decisions">Decision Log</button>
                    </div>
                    
                    <!-- Tab Content -->
                    <div class="dashboard-content">
                        <!-- Restraint Matrix Tab -->
                        <div class="tab-panel active" data-panel="restraints" id="restraints-panel">
                            <div class="loading-spinner">
                                <div class="spinner"></div>
                                <div class="loading-text">Loading restraint matrix...</div>
                            </div>
                        </div>
                        
                        <!-- Cognitive State Tab -->
                        <div class="tab-panel" data-panel="cognitive" id="cognitive-panel">
                            <div class="loading-spinner">
                                <div class="spinner"></div>
                                <div class="loading-text">Loading cognitive state...</div>
                            </div>
                        </div>
                        
                        <!-- Council Tab -->
                        <div class="tab-panel" data-panel="council" id="council-panel">
                            <div class="loading-spinner">
                                <div class="spinner"></div>
                                <div class="loading-text">Loading council data...</div>
                            </div>
                        </div>
                        
                        <!-- Cognitive Debt Tab -->
                        <div class="tab-panel" data-panel="debt" id="debt-panel">
                            <div class="loading-spinner">
                                <div class="spinner"></div>
                                <div class="loading-text">Loading cognitive debt...</div>
                            </div>
                        </div>
                        
                        <!-- Audit Trail Tab -->
                        <div class="tab-panel" data-panel="audit" id="audit-panel">
                            <div class="loading-spinner">
                                <div class="spinner"></div>
                                <div class="loading-text">Loading audit trail...</div>
                            </div>
                        </div>
                        
                        <!-- Decision Log Tab -->
                        <div class="tab-panel" data-panel="decisions" id="decisions-panel">
                            <div class="loading-spinner">
                                <div class="spinner"></div>
                                <div class="loading-text">Loading decision log...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Toast Container -->
            <div class="toast-container" id="toast-container"></div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', dashboardHTML);
    }
    
    attachEventListeners() {
        // Open dashboard button (added to header)
        const cognitiveBtn = document.getElementById('cognitive-btn');
        if (cognitiveBtn) {
            cognitiveBtn.addEventListener('click', () => this.open());
        }
        
        // Close button
        const closeBtn = document.getElementById('close-dashboard');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // Close on overlay click
        const dashboard = document.getElementById('cognitive-dashboard');
        if (dashboard) {
            dashboard.addEventListener('click', (e) => {
                if (e.target === dashboard) {
                    this.close();
                }
            });
        }
        
        // Tab switching
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Escape to close
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
            
            // Ctrl+K to open
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
        });
    }
    
    open() {
        console.log('[RCL2] Opening dashboard...');
        const dashboard = document.getElementById('cognitive-dashboard');
        if (dashboard) {
            dashboard.classList.add('open');
            this.isOpen = true;
            
            // Load current tab content
            this.loadTabContent(this.currentTab);
        }
    }
    
    close() {
        console.log('[RCL2] Closing dashboard...');
        const dashboard = document.getElementById('cognitive-dashboard');
        if (dashboard) {
            dashboard.classList.remove('open');
            this.isOpen = false;
        }
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    switchTab(tabName) {
        console.log(`[RCL2] Switching to tab: ${tabName}`);
        
        // Update tab buttons
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            if (btn.getAttribute('data-tab') === tabName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Update tab panels
        const tabPanels = document.querySelectorAll('.tab-panel');
        tabPanels.forEach(panel => {
            if (panel.getAttribute('data-panel') === tabName) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
        
        this.currentTab = tabName;
        
        // Load tab content
        this.loadTabContent(tabName);
    }
    
    loadTabContent(tabName) {
        console.log(`[RCL2] Loading content for tab: ${tabName}`);
        
        switch (tabName) {
            case 'restraints':
                if (this.restraints) {
                    this.restraints.load();
                }
                break;
            case 'cognitive':
                this.loadCognitiveState();
                break;
            case 'council':
                if (this.council) {
                    this.council.load();
                }
                break;
            case 'debt':
                if (this.debt) {
                    this.debt.load();
                }
                break;
            case 'audit':
                this.loadAuditTrail();
                break;
            case 'decisions':
                this.loadDecisions();
                break;
        }
    }
    
    async loadCognitiveState() {
        const panel = document.getElementById('cognitive-panel');
        
        try {
            const response = await fetch(`${this.apiBase}/cognitive-state`);
            const data = await response.json();
            
            if (data.success) {
                this.renderCognitiveState(panel, data);
            } else {
                throw new Error('Failed to load cognitive state');
            }
        } catch (error) {
            console.error('[RCL2] Error loading cognitive state:', error);
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-text">Failed to load cognitive state</div>
                    <div class="empty-hint">${error.message}</div>
                </div>
            `;
        }
    }
    
    renderCognitiveState(panel, data) {
        const { system1, system2, escalations } = data;
        
        panel.innerHTML = `
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Cognitive State Monitor</div>
                    <span class="card-badge badge-success">Active</span>
                </div>
                
                <div class="cognitive-stats">
                    <div class="stat-card">
                        <div class="stat-label">System 1 Calls</div>
                        <div class="stat-value">${system1.calls.toLocaleString()}</div>
                        <div class="stat-sublabel">Fast, intuitive processing</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">System 2 Calls</div>
                        <div class="stat-value">${system2.calls.toLocaleString()}</div>
                        <div class="stat-sublabel">Deep, reflective processing</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Escalations</div>
                        <div class="stat-value">${escalations.toLocaleString()}</div>
                        <div class="stat-sublabel">System 1 → System 2</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Total Time</div>
                        <div class="stat-value">${((system1.total_time_ms + system2.total_time_ms) / 1000).toFixed(1)}s</div>
                        <div class="stat-sublabel">Combined processing</div>
                    </div>
                </div>
                
                <div class="system-activity">
                    <div class="system-card system1">
                        <div class="system-header">
                            <span class="system-badge">System 1</span>
                            <span class="system-name">Fast Thinking</span>
                        </div>
                        <div class="system-metrics">
                            <div class="metric-row">
                                <span class="metric-label">Total Calls</span>
                                <span class="metric-value">${system1.calls.toLocaleString()}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Total Time</span>
                                <span class="metric-value">${(system1.total_time_ms / 1000).toFixed(2)}s</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Avg Time/Call</span>
                                <span class="metric-value">${system1.calls > 0 ? (system1.total_time_ms / system1.calls).toFixed(2) : 0}ms</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="system-card system2">
                        <div class="system-header">
                            <span class="system-badge">System 2</span>
                            <span class="system-name">Slow Thinking</span>
                        </div>
                        <div class="system-metrics">
                            <div class="metric-row">
                                <span class="metric-label">Total Calls</span>
                                <span class="metric-value">${system2.calls.toLocaleString()}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Total Time</span>
                                <span class="metric-value">${(system2.total_time_ms / 1000).toFixed(2)}s</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Avg Time/Call</span>
                                <span class="metric-value">${system2.calls > 0 ? (system2.total_time_ms / system2.calls).toFixed(2) : 0}ms</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    async loadAuditTrail() {
        const panel = document.getElementById('audit-panel');
        
        try {
            const response = await fetch(`${this.apiBase}/audit-trail?limit=100`);
            const data = await response.json();
            
            if (data.success) {
                this.renderAuditTrail(panel, data);
            } else {
                throw new Error('Failed to load audit trail');
            }
        } catch (error) {
            console.error('[RCL2] Error loading audit trail:', error);
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-text">Failed to load audit trail</div>
                    <div class="empty-hint">${error.message}</div>
                </div>
            `;
        }
    }
    
    renderAuditTrail(panel, data) {
        const { changes, chain_valid, unauthorized_attempts } = data;
        
        const changesHTML = changes.length > 0 ? changes.map(change => `
            <div class="timeline-item ${change.authorized ? 'authorized' : 'unauthorized'}">
                <div class="timeline-time">${new Date(change.timestamp).toLocaleString()}</div>
                <div class="timeline-dimension">${change.dimension}</div>
                <div class="timeline-change">
                    <span class="old-value">${change.old_value.toFixed(2)}</span>
                    <span class="timeline-arrow">→</span>
                    <span class="new-value">${change.new_value.toFixed(2)}</span>
                </div>
                <div class="timeline-hash">Hash: ${change.hash.substring(0, 16)}...</div>
            </div>
        `).join('') : '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">No audit trail entries</div></div>';
        
        panel.innerHTML = `
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Constitutional Audit Trail</div>
                    <span class="card-badge ${chain_valid ? 'badge-success' : 'badge-error'}">
                        ${chain_valid ? 'Valid' : 'Compromised'}
                    </span>
                </div>
                
                <div class="audit-status ${chain_valid ? 'valid' : 'invalid'}">
                    <div class="status-icon">${chain_valid ? '✓' : '⚠'}</div>
                    <div class="status-details">
                        <div class="status-title">${chain_valid ? 'Audit Chain Valid' : 'Audit Chain Compromised'}</div>
                        <div class="status-subtitle">
                            ${changes.length} total changes • 
                            ${unauthorized_attempts.length} unauthorized attempts
                        </div>
                    </div>
                </div>
                
                ${unauthorized_attempts.length > 0 ? `
                    <div class="dashboard-card" style="background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                        <div class="card-header">
                            <div class="card-title">⚠️ Unauthorized Attempts</div>
                            <span class="card-badge badge-error">${unauthorized_attempts.length}</span>
                        </div>
                        ${unauthorized_attempts.map(attempt => `
                            <div class="timeline-item unauthorized">
                                <div class="timeline-time">${new Date(attempt.timestamp).toLocaleString()}</div>
                                <div class="timeline-dimension">${attempt.dimension}</div>
                                <div class="timeline-change">
                                    <span>Attempted value: <span class="new-value">${attempt.attempted_value.toFixed(2)}</span></span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                <div class="audit-timeline">
                    ${changesHTML}
                </div>
            </div>
        `;
    }
    
    async loadDecisions() {
        const panel = document.getElementById('decisions-panel');
        
        try {
            const response = await fetch(`${this.apiBase}/decisions?limit=100`);
            const data = await response.json();
            
            if (data.success) {
                this.renderDecisions(panel, data);
            } else {
                throw new Error('Failed to load decisions');
            }
        } catch (error) {
            console.error('[RCL2] Error loading decisions:', error);
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-text">Failed to load decision log</div>
                    <div class="empty-hint">${error.message}</div>
                </div>
            `;
        }
    }
    
    renderDecisions(panel, data) {
        const { decisions, count } = data;
        
        const decisionsHTML = decisions.length > 0 ? decisions.map(decision => {
            const confidenceClass = decision.confidence >= 0.8 ? 'confidence-high' : 
                                   decision.confidence >= 0.5 ? 'confidence-medium' : 'confidence-low';
            
            return `
                <div class="decision-card">
                    <div class="decision-header">
                        <span class="decision-type">${decision.decision_type}</span>
                        <span class="decision-confidence ${confidenceClass}">${(decision.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div class="decision-text">${decision.decision}</div>
                    <div class="decision-meta">
                        <span class="decision-id-display">${decision.decision_id}</span>
                        <span>${new Date(decision.timestamp).toLocaleString()}</span>
                    </div>
                </div>
            `;
        }).join('') : '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">No decisions recorded</div></div>';
        
        panel.innerHTML = `
            <div class="dashboard-card">
                <div class="card-header">
                    <div class="card-title">Decision Log</div>
                    <span class="card-badge badge-info">${count} decisions</span>
                </div>
                
                <div class="decision-grid">
                    ${decisionsHTML}
                </div>
            </div>
        `;
    }
    
    initializeWebSocket() {
        // WebSocket for real-time updates (optional)
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}${this.apiBase}/ws`;
            
            console.log(`[RCL2] Connecting to WebSocket: ${wsUrl}`);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('[RCL2] WebSocket connected');
                this.showToast('Connected to RCL-2 real-time updates', 'success');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('[RCL2] Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('[RCL2] WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('[RCL2] WebSocket disconnected, reconnecting...');
                this.scheduleWebSocketReconnect();
            };
        } catch (error) {
            console.error('[RCL2] Failed to initialize WebSocket:', error);
        }
    }
    
    scheduleWebSocketReconnect() {
        if (this.wsReconnectTimer) {
            clearTimeout(this.wsReconnectTimer);
        }
        
        this.wsReconnectTimer = setTimeout(() => {
            this.initializeWebSocket();
        }, this.wsReconnectDelay);
    }
    
    handleWebSocketMessage(data) {
        console.log('[RCL2] WebSocket message:', data);
        
        // Handle different message types
        if (data.type === 'restraint_update') {
            if (this.restraints) {
                this.restraints.handleUpdate(data);
            }
        } else if (data.type === 'deliberation_complete') {
            if (this.council) {
                this.council.handleUpdate(data);
            }
            this.showToast('Council deliberation completed', 'info');
        } else if (data.type === 'debt_repaid') {
            if (this.debt) {
                this.debt.handleUpdate(data);
            }
            this.showToast('Cognitive debt repaid', 'success');
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-message">${message}</div>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// Initialize dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.rcl2Dashboard = new RCL2Dashboard();
    });
} else {
    window.rcl2Dashboard = new RCL2Dashboard();
}
