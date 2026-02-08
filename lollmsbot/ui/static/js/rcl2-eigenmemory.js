/**
 * RCL-2 Eigenmemory UI Component
 * 
 * Displays memory statistics, provides query interface, and intentional amnesia controls.
 */

class RCL2Eigenmemory {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.apiBase = dashboard.apiBase;
        this.currentStats = null;
        this.queryHistory = [];
        
        console.log('[RCL2-Eigenmemory] Initializing...');
    }
    
    async init() {
        await this.loadData();
        this.render();
        this.attachEventListeners();
    }
    
    async loadData() {
        try {
            const response = await fetch(`${this.apiBase}/eigenmemory`);
            const data = await response.json();
            this.currentStats = data;
            console.log('[RCL2-Eigenmemory] Data loaded:', this.currentStats);
        } catch (error) {
            console.error('[RCL2-Eigenmemory] Error loading data:', error);
            this.currentStats = { error: error.message };
        }
    }
    
    render() {
        const panel = document.getElementById('eigenmemory-panel');
        if (!panel || !this.currentStats) return;
        
        if (this.currentStats.error) {
            panel.innerHTML = `
                <div class="error-message">
                    <div class="error-icon">⚠️</div>
                    <div class="error-text">Failed to load eigenmemory: ${this.currentStats.error}</div>
                </div>
            `;
            return;
        }
        
        if (this.currentStats.status === 'unavailable') {
            panel.innerHTML = `
                <div class="info-message">
                    <div class="info-icon">ℹ️</div>
                    <div class="info-text">Eigenmemory module is not available</div>
                </div>
            `;
            return;
        }
        
        const stats = this.currentStats.data;
        
        // Provide defaults if missing (e.g. empty memory state)
        stats.by_strength = stats.by_strength || { strong: 0, moderate: 0, weak: 0, forgotten: 0 };
        stats.by_source = stats.by_source || { episodic: 0, semantic: 0, procedural: 0, confabulated: 0, inherited: 0, inferred: 0 };
        stats.confabulation_rate = stats.confabulation_rate || 0;
        stats.average_confidence = stats.average_confidence || 0;
        stats.total_memories = stats.total_memories || 0;
        
        panel.innerHTML = `
            <div class="eigenmemory-container">
                <!-- Memory Statistics -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Memories</div>
                        <div class="metric-value">${stats.total_memories}</div>
                        <div class="metric-subtitle">Stored traces</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Strong Memories</div>
                        <div class="metric-value">${stats.by_strength.strong || 0}</div>
                        <div class="metric-subtitle">${this.percentage(stats.by_strength.strong, stats.total_memories)}%</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Confabulation Rate</div>
                        <div class="metric-value">${(stats.confabulation_rate * 100).toFixed(1)}%</div>
                        <div class="metric-subtitle">${this.getConfabulationStatus(stats.confabulation_rate)}</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Average Confidence</div>
                        <div class="metric-value">${(stats.average_confidence * 100).toFixed(0)}%</div>
                        <div class="metric-subtitle">${this.getConfidenceStatus(stats.average_confidence)}</div>
                    </div>
                </div>
                
                <!-- Memory Source Distribution -->
                <div class="card">
                    <div class="card-header">
                        <h3>Memory Source Distribution</h3>
                    </div>
                    <div class="card-body">
                        <div class="source-chart">
                            ${this.renderSourceChart(stats.by_source)}
                        </div>
                    </div>
                </div>
                
                <!-- Memory Strength Distribution -->
                <div class="card">
                    <div class="card-header">
                        <h3>Memory Strength Distribution</h3>
                    </div>
                    <div class="card-body">
                        <div class="strength-bars">
                            ${this.renderStrengthBars(stats.by_strength, stats.total_memories)}
                        </div>
                    </div>
                </div>
                
                <!-- Metamemory Query Interface -->
                <div class="card">
                    <div class="card-header">
                        <h3>Metamemory Query</h3>
                        <div class="card-subtitle">Query what the system knows or remembers</div>
                    </div>
                    <div class="card-body">
                        <div class="query-interface">
                            <div class="query-type-selector">
                                <label>
                                    <input type="radio" name="query-type" value="knowledge" checked>
                                    "Do I know...?" (Semantic check)
                                </label>
                                <label>
                                    <input type="radio" name="query-type" value="remember">
                                    "Do I remember...?" (Episodic recall)
                                </label>
                            </div>
                            
                            <div class="query-input-group">
                                <input 
                                    type="text" 
                                    id="memory-query-input" 
                                    class="query-input" 
                                    placeholder="Enter query (e.g., 'user preferences', 'last interaction')..."
                                />
                                <button class="btn btn-primary" id="execute-query-btn">Query</button>
                            </div>
                            
                            <div id="query-results" class="query-results"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Intentional Amnesia (GDPR Compliance) -->
                <div class="card warning-card">
                    <div class="card-header">
                        <h3>🗑️ Intentional Amnesia</h3>
                        <div class="card-subtitle">GDPR-compliant memory deletion</div>
                    </div>
                    <div class="card-body">
                        <div class="amnesia-interface">
                            <p class="warning-text">
                                ⚠️ This will permanently delete memories related to the specified subject.
                                This action cannot be undone.
                            </p>
                            
                            <div class="forget-input-group">
                                <input 
                                    type="text" 
                                    id="forget-subject-input" 
                                    class="query-input" 
                                    placeholder="Enter subject to forget (e.g., 'user email', 'conversation history')..."
                                />
                                <button class="btn btn-danger" id="forget-btn">Forget</button>
                            </div>
                            
                            <div id="forget-results" class="forget-results"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Query History -->
                ${this.queryHistory.length > 0 ? `
                    <div class="card">
                        <div class="card-header">
                            <h3>Query History</h3>
                        </div>
                        <div class="card-body">
                            <div class="query-history">
                                ${this.renderQueryHistory()}
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    renderSourceChart(bySource) {
        const sources = [
            { key: 'episodic', label: 'Episodic', color: '#3b82f6', icon: '📍' },
            { key: 'semantic', label: 'Semantic', color: '#8b5cf6', icon: '📚' },
            { key: 'procedural', label: 'Procedural', color: '#10b981', icon: '⚙️' },
            { key: 'confabulated', label: 'Confabulated', color: '#ef4444', icon: '❓' },
            { key: 'inherited', label: 'Inherited', color: '#f59e0b', icon: '🧬' },
            { key: 'inferred', label: 'Inferred', color: '#6366f1', icon: '🔮' }
        ];
        
        const total = Object.values(bySource).reduce((sum, count) => sum + count, 0);
        
        return `
            <div class="source-items">
                ${sources.map(source => {
                    const count = bySource[source.key] || 0;
                    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;
                    return `
                        <div class="source-item">
                            <div class="source-icon" style="background: ${source.color}">${source.icon}</div>
                            <div class="source-info">
                                <div class="source-label">${source.label}</div>
                                <div class="source-value">${count} (${percentage}%)</div>
                            </div>
                            <div class="source-bar">
                                <div class="source-bar-fill" style="width: ${percentage}%; background: ${source.color}"></div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    renderStrengthBars(byStrength, total) {
        const strengths = [
            { key: 'strong', label: 'Strong', color: '#10b981' },
            { key: 'moderate', label: 'Moderate', color: '#f59e0b' },
            { key: 'weak', label: 'Weak', color: '#ef4444' },
            { key: 'forgotten', label: 'Forgotten', color: '#6b7280' }
        ];
        
        return strengths.map(strength => {
            const count = byStrength[strength.key] || 0;
            const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;
            return `
                <div class="strength-bar-item">
                    <div class="strength-label">${strength.label}</div>
                    <div class="strength-bar">
                        <div class="strength-bar-fill" style="width: ${percentage}%; background: ${strength.color}">
                            <span class="strength-bar-text">${count} (${percentage}%)</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    renderQueryHistory() {
        return this.queryHistory.slice(-5).reverse().map(entry => `
            <div class="history-item">
                <div class="history-header">
                    <span class="history-type">${entry.type === 'knowledge' ? '📚' : '📍'} ${entry.type}</span>
                    <span class="history-time">${this.formatTime(entry.timestamp)}</span>
                </div>
                <div class="history-query">"${entry.query}"</div>
                <div class="history-result ${entry.result.knows ? 'result-positive' : 'result-negative'}">
                    ${entry.result.knows ? '✓ Yes' : '✗ No'} 
                    ${entry.result.confidence ? `(${(entry.result.confidence * 100).toFixed(0)}% confidence)` : ''}
                </div>
            </div>
        `).join('');
    }
    
    percentage(value, total) {
        return total > 0 ? ((value / total) * 100).toFixed(1) : 0;
    }
    
    getConfabulationStatus(rate) {
        if (rate < 0.05) return 'Excellent';
        if (rate < 0.15) return 'Good';
        if (rate < 0.30) return 'Moderate';
        return 'High - review needed';
    }
    
    getConfidenceStatus(confidence) {
        if (confidence >= 0.8) return 'High confidence';
        if (confidence >= 0.6) return 'Moderate confidence';
        if (confidence >= 0.4) return 'Low confidence';
        return 'Very uncertain';
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    attachEventListeners() {
        const queryBtn = document.getElementById('execute-query-btn');
        if (queryBtn) {
            queryBtn.addEventListener('click', () => this.executeQuery());
        }
        
        const queryInput = document.getElementById('memory-query-input');
        if (queryInput) {
            queryInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.executeQuery();
            });
        }
        
        const forgetBtn = document.getElementById('forget-btn');
        if (forgetBtn) {
            forgetBtn.addEventListener('click', () => this.forgetMemory());
        }
    }
    
    async executeQuery() {
        const input = document.getElementById('memory-query-input');
        const resultsDiv = document.getElementById('query-results');
        const queryType = document.querySelector('input[name="query-type"]:checked').value;
        
        if (!input || !resultsDiv) return;
        
        const query = input.value.trim();
        if (!query) {
            this.showError(resultsDiv, 'Please enter a query');
            return;
        }
        
        resultsDiv.innerHTML = '<div class="loading">Querying memory...</div>';
        
        try {
            const response = await fetch(`${this.apiBase}/eigenmemory/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, query_type: queryType })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const result = data.result;
                
                // Add to history
                this.queryHistory.push({
                    query,
                    type: queryType,
                    result,
                    timestamp: new Date()
                });
                
                // Display result
                resultsDiv.innerHTML = `
                    <div class="query-result ${result.knows ? 'result-positive' : 'result-negative'}">
                        <div class="result-status">
                            ${result.knows ? '✓ Yes' : '✗ No'}
                        </div>
                        <div class="result-details">
                            ${result.confidence ? `<div>Confidence: ${(result.confidence * 100).toFixed(0)}%</div>` : ''}
                            ${result.memory_count ? `<div>Memories found: ${result.memory_count}</div>` : ''}
                            ${result.source ? `<div>Source: ${result.source}</div>` : ''}
                            ${result.explanation ? `<div class="result-explanation">${result.explanation}</div>` : ''}
                        </div>
                    </div>
                `;
                
                // Re-render to show history
                setTimeout(() => this.render() && this.attachEventListeners(), 100);
            } else {
                this.showError(resultsDiv, data.message || 'Query failed');
            }
        } catch (error) {
            console.error('[RCL2-Eigenmemory] Query error:', error);
            this.showError(resultsDiv, 'Query error: ' + error.message);
        }
    }
    
    async forgetMemory() {
        const input = document.getElementById('forget-subject-input');
        const resultsDiv = document.getElementById('forget-results');
        
        if (!input || !resultsDiv) return;
        
        const subject = input.value.trim();
        if (!subject) {
            this.showError(resultsDiv, 'Please enter a subject to forget');
            return;
        }
        
        // Confirmation dialog
        if (!confirm(`Are you sure you want to permanently forget all memories related to "${subject}"? This action cannot be undone.`)) {
            return;
        }
        
        resultsDiv.innerHTML = '<div class="loading">Forgetting...</div>';
        
        try {
            const response = await fetch(`${this.apiBase}/eigenmemory/forget`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subject, require_confirmation: true })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                resultsDiv.innerHTML = `
                    <div class="forget-result result-positive">
                        <div class="result-status">✓ Successfully forgotten</div>
                        <div class="result-details">
                            Removed ${data.forgotten_count} ${data.forgotten_count === 1 ? 'memory' : 'memories'} related to "${data.subject}"
                        </div>
                    </div>
                `;
                
                input.value = '';
                
                // Reload stats
                setTimeout(() => {
                    this.loadData().then(() => {
                        this.render();
                        this.attachEventListeners();
                    });
                }, 1000);
            } else {
                this.showError(resultsDiv, data.message || 'Forget operation failed');
            }
        } catch (error) {
            console.error('[RCL2-Eigenmemory] Forget error:', error);
            this.showError(resultsDiv, 'Error: ' + error.message);
        }
    }
    
    showError(container, message) {
        container.innerHTML = `
            <div class="error-message">
                <div class="error-icon">⚠️</div>
                <div class="error-text">${message}</div>
            </div>
        `;
    }
}

// Export for use in dashboard
window.RCL2Eigenmemory = RCL2Eigenmemory;
