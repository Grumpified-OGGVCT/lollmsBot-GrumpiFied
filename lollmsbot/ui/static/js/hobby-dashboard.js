/**
 * Autonomous Hobby System Dashboard - Main Controller
 * 
 * Handles dashboard initialization, tab switching, and data visualization
 * for the background learning system.
 */

class HobbyDashboard {
    constructor() {
        this.isOpen = false;
        this.currentTab = 'overview';
        this.apiBase = '/hobby';
        this.refreshTimer = null;
        this.refreshInterval = 5000; // 5 seconds
        
        this.init();
    }
    
    init() {
        console.log('[Hobby] Initializing dashboard...');
        this.createDashboardHTML();
        this.attachEventListeners();
        
        // Start polling for active status if open
        this.startPolling();
    }
    
    createDashboardHTML() {
        const dashboardHTML = `
            <div class="cognitive-dashboard" id="hobby-dashboard" style="display: none;">
                <div class="dashboard-container glass-panel">
                    <!-- Header -->
                    <div class="dashboard-header">
                        <div class="dashboard-title">
                            <span class="icon">🎨</span>
                            <span>Autonomous Hobby System</span>
                            <span class="version-badge">Phase 3</span>
                        </div>
                        <div class="dashboard-controls">
                            <div class="status-badge" id="hobby-status-badge">
                                <span class="dot"></span>
                                <span id="hobby-status-text">Idle</span>
                            </div>
                            <button class="btn-icon close-dashboard" id="close-hobby-dashboard" title="Close (Esc)">×</button>
                        </div>
                    </div>
                    
                    <!-- Tab Navigation -->
                    <div class="dashboard-nav">
                        <button class="nav-tab active" data-target="tab-overview">
                            <span class="icon">📊</span> Overview
                        </button>
                        <button class="nav-tab" data-target="tab-progress">
                            <span class="icon">📈</span> Progress
                        </button>
                        <button class="nav-tab" data-target="tab-activities">
                            <span class="icon">🕒</span> Activities
                        </button>
                        <button class="nav-tab" data-target="tab-insights">
                            <span class="icon">💡</span> Insights
                        </button>
                        <button class="nav-tab" data-target="tab-settings">
                            <span class="icon">⚙️</span> Settings
                        </button>
                    </div>
                    
                    <!-- Tab Content -->
                    <div class="dashboard-content">
                        <!-- Tab 1: Overview -->
                        <div class="tab-pane active" id="tab-overview">
                            <div class="overview-grid">
                                <!-- Status Card -->
                                <div class="dashboard-card main-status-card">
                                    <div class="card-header">
                                        <div class="card-title">System Status</div>
                                        <div class="toggle-switch">
                                            <label class="switch">
                                                <input type="checkbox" id="hobby-toggle">
                                                <span class="slider round"></span>
                                            </label>
                                            <span id="hobby-toggle-label">Disabled</span>
                                        </div>
                                    </div>
                                    <div class="status-content">
                                        <div class="current-activity" id="current-activity-display">
                                            <div class="activity-icon">💤</div>
                                            <div class="activity-details">
                                                <h3>System Idle</h3>
                                                <p>Waiting for user inactivity...</p>
                                            </div>
                                        </div>
                                        <div class="status-metrics">
                                            <div class="metric">
                                                <span class="label">Next Session</span>
                                                <span class="value" id="next-session-timer">--:--</span>
                                            </div>
                                            <div class="metric">
                                                <span class="label">Today's Sessions</span>
                                                <span class="value" id="today-sessions-count">0</span>
                                            </div>
                                            <div class="metric">
                                                <span class="label">Time Invested</span>
                                                <span class="value" id="total-time-invested">0h</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Quick Stats -->
                                <div class="dashboard-card">
                                    <div class="card-header">
                                        <div class="card-title">Top Skills</div>
                                    </div>
                                    <div class="skills-list" id="top-skills-list">
                                        <div class="loading-text">Loading...</div>
                                    </div>
                                </div>
                                
                                <!-- Recent Insight -->
                                <div class="dashboard-card">
                                    <div class="card-header">
                                        <div class="card-title">Latest Insight</div>
                                    </div>
                                    <div class="insight-card" id="latest-insight-card">
                                        <div class="insight-text">No recent insights recorded.</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Tab 2: Progress -->
                        <div class="tab-pane" id="tab-progress">
                            <div class="charts-container">
                                <div class="chart-row">
                                    <div class="dashboard-card chart-card">
                                        <div class="card-header">
                                            <div class="card-title">Proficiency by Hobby Type</div>
                                        </div>
                                        <div class="chart-wrapper" id="proficiency-chart-container">
                                            <!-- Chart injected here -->
                                            <div class="placeholder-chart">Radar Chart Placeholder</div>
                                        </div>
                                    </div>
                                    <div class="dashboard-card chart-card">
                                        <div class="card-header">
                                            <div class="card-title">Time Investment</div>
                                        </div>
                                        <div class="chart-wrapper" id="time-chart-container">
                                            <!-- Chart injected here -->
                                            <div class="placeholder-chart">Bar Chart Placeholder</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Tab 3: Activities -->
                        <div class="tab-pane" id="tab-activities">
                            <div class="activity-feed" id="activity-feed-list">
                                <div class="loading-spinner">
                                    <div class="spinner"></div>
                                    <div class="loading-text">Loading history...</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Tab 4: Insights -->
                        <div class="tab-pane" id="tab-insights">
                            <div class="insights-feed" id="insights-feed-list">
                                <div class="loading-spinner">
                                    <div class="spinner"></div>
                                    <div class="loading-text">Loading insights...</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Tab 5: Settings -->
                        <div class="tab-pane" id="tab-settings">
                            <div class="settings-form">
                                <div class="form-section">
                                    <h3>Timing & Schedule</h3>
                                    <div class="form-group">
                                        <label>Idle Threshold (minutes)</label>
                                        <input type="number" id="setting-idle-threshold" min="1" max="60" disabled> <!-- Read-only for now -->
                                        <span class="form-hint">Time before AI starts learning</span>
                                    </div>
                                    <div class="form-group">
                                        <label>Session Duration (minutes)</label>
                                        <input type="number" id="setting-duration" min="5" max="120" disabled>
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h3>Learning Focus</h3>
                                    <div class="checkbox-group" id="hobby-types-settings">
                                        <!-- Injected by JS -->
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', dashboardHTML);
    }
    
    attachEventListeners() {
        // Open button (Header)
        const openBtn = document.getElementById('hobby-btn');
        if (openBtn) {
            openBtn.addEventListener('click', () => this.open());
        }

        // Open/Close
        const closeBtn = document.getElementById('close-hobby-dashboard');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // Tab switching
        const tabs = document.querySelectorAll('#hobby-dashboard .nav-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.getAttribute('data-target');
                this.switchTab(target);
            });
        });
        
        // Overlay click to close
        const dashboard = document.getElementById('hobby-dashboard');
        if (dashboard) {
            dashboard.addEventListener('click', (e) => {
                if (e.target === dashboard) this.close();
            });
        }
        
        // System Toggle
        const toggle = document.getElementById('hobby-toggle');
        if (toggle) {
            toggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startSystem();
                } else {
                    this.stopSystem();
                }
            });
        }
        
        // Keyboard shortcut (Ctrl+H)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'h') {
                e.preventDefault();
                this.toggle();
            }
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }
    
    startPolling() {
        if (this.refreshTimer) clearInterval(this.refreshTimer);
        this.refreshTimer = setInterval(() => {
            if (this.isOpen) {
                this.refreshCurrentTab();
            }
        }, this.refreshInterval);
    }
    
    open() {
        const dashboard = document.getElementById('hobby-dashboard');
        if (dashboard) {
            dashboard.style.display = 'flex';
            requestAnimationFrame(() => {
                dashboard.classList.add('open');
            });
            this.isOpen = true;
            this.loadTabContent(this.currentTab);
        }
    }
    
    close() {
        const dashboard = document.getElementById('hobby-dashboard');
        if (dashboard) {
            dashboard.classList.remove('open');
            setTimeout(() => {
                dashboard.style.display = 'none';
            }, 300);
            this.isOpen = false;
        }
    }
    
    toggle() {
        if (this.isOpen) this.close();
        else this.open();
    }
    
    switchTab(tabId) {
        // Update nav
        document.querySelectorAll('#hobby-dashboard .nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`#hobby-dashboard .nav-tab[data-target="${tabId}"]`).classList.add('active');
        
        // Update panes
        document.querySelectorAll('#hobby-dashboard .tab-pane').forEach(p => p.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        
        this.currentTab = tabId.replace('tab-', '');
        this.loadTabContent(this.currentTab);
    }
    
    refreshCurrentTab() {
        if (this.currentTab === 'overview') this.loadOverview();
        // Other tabs typically don't need rapid polling
    }
    
    async loadTabContent(tab) {
        switch(tab) {
            case 'overview': await this.loadOverview(); break;
            case 'progress': await this.loadProgress(); break;
            case 'activities': await this.loadActivities(); break;
            case 'insights': await this.loadInsights(); break;
            case 'settings': await this.loadSettings(); break;
        }
    }
    
    // API Interactions
    
    async loadOverview() {
        try {
            const statusRes = await fetch(`${this.apiBase}/status`);
            const statusData = await statusRes.json();
            
            this.updateStatusUI(statusData);
            
        } catch (e) {
            console.error('[Hobby] Failed to load overview:', e);
        }
    }
    
    updateStatusUI(data) {
        // Toggle Switch
        const toggle = document.getElementById('hobby-toggle');
        const label = document.getElementById('hobby-toggle-label');
        if (toggle && label) {
            toggle.checked = data.enabled;
            label.textContent = data.enabled ? "Active" : "Disabled";
            label.style.color = data.enabled ? "var(--success)" : "var(--text-secondary)";
        }
        
        // Badge
        const badge = document.getElementById('hobby-status-badge');
        const badgeText = document.getElementById('hobby-status-text');
        
        // Current Activity
        const activityDisplay = document.getElementById('current-activity-display');
        
        // Check if actually running an activity (this depends on how your API reports it)
        // For now, assuming data.progress contains active info or we default to idle
        
        // Simplified Logic:
        if (data.enabled) {
            badge.classList.add('active');
            badgeText.textContent = 'Monitoring';
        } else {
            badge.classList.remove('active');
            badgeText.textContent = 'Disabled';
        }
        
        // Populate Top Skills
        const skillsList = document.getElementById('top-skills-list');
        if (data.progress && data.progress.proficiency) {
            const skills = Object.entries(data.progress.proficiency)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3);
                
            skillsList.innerHTML = skills.map(([name, level]) => `
                <div class="skill-item">
                    <span class="skill-name">${name}</span>
                    <div class="skill-bar-container">
                        <div class="skill-bar" style="width: ${level * 100}%"></div>
                    </div>
                    <span class="skill-val">${(level * 100).toFixed(0)}%</span>
                </div>
            `).join('');
        }
        
        // Sessions Count
        if (data.progress) {
             document.getElementById('today-sessions-count').textContent = data.progress.total_sessions || 0;
             const hours = (data.progress.total_duration_minutes || 0) / 60;
             document.getElementById('total-time-invested').textContent = `${hours.toFixed(1)}h`;
        }
    }
    
    async loadActivities() {
        try {
            const res = await fetch(`${this.apiBase}/activities?count=20`);
            const activities = await res.json();
            
            const list = document.getElementById('activity-feed-list');
            if (activities.length === 0) {
                list.innerHTML = '<div class="empty-state">No recorded activities</div>';
                return;
            }
            
            list.innerHTML = activities.map(act => `
                <div class="activity-card">
                    <div class="activity-header">
                        <span class="activity-type">${act.hobby_type}</span>
                        <span class="activity-time">${new Date(act.started_at).toLocaleString()}</span>
                    </div>
                    <div class="activity-meta">
                        <span>Duration: ${act.duration_minutes ? act.duration_minutes.toFixed(1) + 'm' : 'N/A'}</span>
                        <span>Success: ${act.success ? '✅' : '❌'}</span>
                    </div>
                </div>
            `).join('');
            
        } catch (e) {
            document.getElementById('activity-feed-list').innerHTML = '<div class="error-state">Failed to load data</div>';
        }
    }

    async loadInsights() {
        try {
            const res = await fetch(`${this.apiBase}/insights?count=20`);
            const data = await res.json();
            const insights = data.insights || [];
            
            const list = document.getElementById('insights-feed-list');
            if (insights.length === 0) {
                list.innerHTML = '<div class="empty-state">No insights recorded</div>';
                return;
            }
            
            list.innerHTML = insights.map(item => `
                <div class="insight-item">
                    <div class="insight-icon">💡</div>
                    <div class="insight-content">
                        <div class="insight-text">${item.insight}</div>
                        <div class="insight-meta">${item.hobby_type} • ${new Date(item.timestamp).toLocaleDateString()}</div>
                    </div>
                </div>
            `).join('');
            
        } catch (e) {
            document.getElementById('insights-feed-list').innerHTML = '<div class="error-state">Failed to load insights</div>';
        }
    }
    
    async loadSettings() {
        try {
            const res = await fetch(`${this.apiBase}/config`);
            const config = await res.json();
            
            document.getElementById('setting-idle-threshold').value = config.idle_threshold_minutes;
            document.getElementById('setting-duration').value = config.max_hobby_duration_minutes;
            
            // Hobbies list
            const container = document.getElementById('hobby-types-settings');
            if (config.hobbies_enabled) {
                container.innerHTML = Object.entries(config.hobbies_enabled).map(([hobby, enabled]) => `
                    <label class="checkbox-item">
                        <input type="checkbox" ${enabled ? 'checked' : ''} disabled>
                        <span>${hobby}</span>
                    </label>
                `).join('');
            }
            
        } catch (e) {
            console.error("Settings load failed", e);
        }
    }
    
    async startSystem() {
        try {
            await fetch(`${this.apiBase}/start`, { method: 'POST' });
            this.loadOverview();
        } catch (e) { console.error(e); }
    }
    
    async stopSystem() {
        try {
            await fetch(`${this.apiBase}/stop`, { method: 'POST' });
            this.loadOverview();
        } catch (e) { console.error(e); }
    }
    
    async loadProgress() {
        // Placeholder for chart loading logic
        // In a real app, this would use Chart.js or similar
        document.getElementById('proficiency-chart-container').innerHTML = '<div class="placeholder-text">Chart visualization requires external library (e.g. Chart.js)</div>';
        document.getElementById('time-chart-container').innerHTML = '';
        
        // Simple text-based stats as fallback
        try {
            const res = await fetch(`${this.apiBase}/progress`);
            const data = await res.json();
            
            let html = '<ul class="stats-list">';
            for(let [type, level] of Object.entries(data.proficiency || {})) {
                 html += `<li><strong>${type}:</strong> ${(level*100).toFixed(0)}%</li>`;
            }
            html += '</ul>';
            
            document.getElementById('proficiency-chart-container').innerHTML = html;
        } catch(e) {}
    }
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.hobbyDashboard = new HobbyDashboard();
    });
} else {
    window.hobbyDashboard = new HobbyDashboard();
}
