/**
 * RCL-2 IQL (Introspection Query Language) UI Component
 * 
 * Provides SQL-like query interface for cognitive state introspection.
 */

class RCL2IQL {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.apiBase = dashboard.apiBase;
        this.examples = [];
        this.queryHistory = [];
        this.currentQuery = '';
        
        console.log('[RCL2-IQL] Initializing...');
    }
    
    async init() {
        await this.loadExamples();
        this.render();
        this.attachEventListeners();
    }
    
    async loadExamples() {
        try {
            const response = await fetch(`${this.apiBase}/iql/examples`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.examples = data.examples;
                console.log('[RCL2-IQL] Examples loaded:', this.examples.length);
            }
        } catch (error) {
            console.error('[RCL2-IQL] Error loading examples:', error);
        }
    }
    
    render() {
        const panel = document.getElementById('iql-panel');
        if (!panel) return;
        
        panel.innerHTML = `
            <div class="iql-container">
                <!-- IQL Introduction -->
                <div class="card info-card">
                    <div class="card-header">
                        <h3>🔍 Introspection Query Language (IQL)</h3>
                    </div>
                    <div class="card-body">
                        <p class="intro-text">
                            IQL provides a SQL-like syntax for querying the agent's cognitive state. 
                            Use it to inspect uncertainty, restraint values, council activity, memory stats, and more.
                        </p>
                        <div class="syntax-example">
                            <pre><code>INTROSPECT {
    SELECT field1, field2, ...
    FROM data_source
    WHERE condition
    DEPTH level
    WITH transparency = "full"
    CONSTRAINT max_latency = 200ms
}</code></pre>
                        </div>
                    </div>
                </div>
                
                <!-- Query Console -->
                <div class="card">
                    <div class="card-header">
                        <h3>Query Console</h3>
                        <div class="console-actions">
                            <button class="btn btn-sm" id="clear-query-btn">Clear</button>
                            <button class="btn btn-sm" id="format-query-btn">Format</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="query-editor">
                            <textarea 
                                id="iql-query-input" 
                                class="query-textarea"
                                placeholder="Enter IQL query here..."
                                rows="8"
                            >${this.currentQuery}</textarea>
                            <div class="editor-actions">
                                <button class="btn btn-primary btn-lg" id="execute-iql-btn">
                                    ▶ Execute Query
                                </button>
                            </div>
                        </div>
                        <div id="iql-results" class="iql-results"></div>
                    </div>
                </div>
                
                <!-- Example Queries -->
                <div class="card">
                    <div class="card-header">
                        <h3>Example Queries</h3>
                        <div class="card-subtitle">Click to load into console</div>
                    </div>
                    <div class="card-body">
                        <div class="examples-grid">
                            ${this.renderExamples()}
                        </div>
                    </div>
                </div>
                
                <!-- Available Data Sources -->
                <div class="card">
                    <div class="card-header">
                        <h3>Available Data Sources</h3>
                    </div>
                    <div class="card-body">
                        <div class="data-sources-list">
                            ${this.renderDataSources()}
                        </div>
                    </div>
                </div>
                
                <!-- Query History -->
                ${this.queryHistory.length > 0 ? `
                    <div class="card">
                        <div class="card-header">
                            <h3>Query History</h3>
                            <button class="btn btn-sm" id="clear-history-btn">Clear History</button>
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
    
    renderExamples() {
        if (this.examples.length === 0) {
            return '<div class="info-message">No examples available</div>';
        }
        
        return this.examples.map((example, index) => `
            <div class="example-card" data-example-id="${index}">
                <div class="example-header">
                    <div class="example-name">${example.name}</div>
                    <button class="btn btn-xs example-load-btn" data-example-id="${index}">Load</button>
                </div>
                <div class="example-description">${example.description}</div>
                <div class="example-query">
                    <pre><code>${this.escapeHtml(example.query)}</code></pre>
                </div>
            </div>
        `).join('');
    }
    
    renderDataSources() {
        const sources = [
            {
                name: 'current_cognitive_state',
                description: 'Current System 1/2 mode, uncertainty, attention focus, epistemic status',
                fields: ['uncertainty', 'system_mode', 'attention_focus', 'epistemic_status', 'system1_calls', 'system2_calls']
            },
            {
                name: 'restraints',
                description: 'Constitutional restraint dimension values',
                fields: ['hallucination_resistance', 'transparency_level', 'goal_autonomy', 'epistemic_rigor', 'etc.']
            },
            {
                name: 'council',
                description: 'Reflective council status and deliberations',
                fields: ['enabled', 'member_count', 'recent_deliberations', 'consensus_rate']
            },
            {
                name: 'twin',
                description: 'Cognitive twin predictions and accuracy',
                fields: ['enabled', 'predictions', 'accuracy', 'deviation_rate']
            },
            {
                name: 'narrative',
                description: 'Narrative identity summary',
                fields: ['developmental_stage', 'coherence_score', 'event_count', 'maturity_score']
            },
            {
                name: 'memory',
                description: 'Eigenmemory system statistics',
                fields: ['total_memories', 'strong_memories', 'confabulation_rate', 'average_confidence']
            }
        ];
        
        return sources.map(source => `
            <div class="data-source-item">
                <div class="source-name">${source.name}</div>
                <div class="source-description">${source.description}</div>
                <div class="source-fields">
                    <span class="fields-label">Available fields:</span>
                    ${source.fields.map(field => `<span class="field-tag">${field}</span>`).join(' ')}
                </div>
            </div>
        `).join('');
    }
    
    renderQueryHistory() {
        return this.queryHistory.slice(-10).reverse().map((entry, index) => `
            <div class="history-item">
                <div class="history-header">
                    <span class="history-time">${this.formatTime(entry.timestamp)}</span>
                    <span class="history-status ${entry.success ? 'status-success' : 'status-error'}">
                        ${entry.success ? '✓' : '✗'}
                    </span>
                    <button class="btn btn-xs history-rerun-btn" data-history-id="${index}">Re-run</button>
                </div>
                <div class="history-query"><pre><code>${this.escapeHtml(entry.query)}</code></pre></div>
                ${entry.success ? `
                    <div class="history-result">
                        Execution time: ${entry.execution_time_ms.toFixed(2)}ms | 
                        Fields returned: ${Object.keys(entry.fields).length}
                    </div>
                ` : `
                    <div class="history-error">${entry.error}</div>
                `}
            </div>
        `).join('');
    }
    
    attachEventListeners() {
        // Execute query
        const executeBtn = document.getElementById('execute-iql-btn');
        if (executeBtn) {
            executeBtn.addEventListener('click', () => this.executeQuery());
        }
        
        // Clear query
        const clearBtn = document.getElementById('clear-query-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                const textarea = document.getElementById('iql-query-input');
                if (textarea) textarea.value = '';
            });
        }
        
        // Format query
        const formatBtn = document.getElementById('format-query-btn');
        if (formatBtn) {
            formatBtn.addEventListener('click', () => this.formatQuery());
        }
        
        // Load example queries
        document.querySelectorAll('.example-load-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const exampleId = parseInt(e.target.dataset.exampleId);
                this.loadExample(exampleId);
            });
        });
        
        // Re-run from history
        document.querySelectorAll('.history-rerun-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const historyId = parseInt(e.target.dataset.historyId);
                this.rerunFromHistory(historyId);
            });
        });
        
        // Clear history
        const clearHistoryBtn = document.getElementById('clear-history-btn');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                this.queryHistory = [];
                this.render();
                this.attachEventListeners();
            });
        }
    }
    
    loadExample(exampleId) {
        if (exampleId < 0 || exampleId >= this.examples.length) return;
        
        const example = this.examples[exampleId];
        const textarea = document.getElementById('iql-query-input');
        if (textarea) {
            textarea.value = example.query;
            textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    rerunFromHistory(historyId) {
        const actualIndex = this.queryHistory.length - 1 - historyId;
        if (actualIndex < 0 || actualIndex >= this.queryHistory.length) return;
        
        const entry = this.queryHistory[actualIndex];
        const textarea = document.getElementById('iql-query-input');
        if (textarea) {
            textarea.value = entry.query;
        }
        
        this.executeQuery();
    }
    
    formatQuery() {
        const textarea = document.getElementById('iql-query-input');
        if (!textarea) return;
        
        let query = textarea.value;
        
        // Simple formatting (basic indentation)
        query = query
            .replace(/INTROSPECT\s*\{/g, 'INTROSPECT {\n    ')
            .replace(/SELECT\s+/g, 'SELECT ')
            .replace(/FROM\s+/g, '\n    FROM ')
            .replace(/WHERE\s+/g, '\n    WHERE ')
            .replace(/DEPTH\s+/g, '\n    DEPTH ')
            .replace(/WITH\s+/g, '\n    WITH ')
            .replace(/CONSTRAINT\s+/g, '\n    CONSTRAINT ')
            .replace(/\}/g, '\n}');
        
        textarea.value = query;
    }
    
    async executeQuery() {
        const textarea = document.getElementById('iql-query-input');
        const resultsDiv = document.getElementById('iql-results');
        
        if (!textarea || !resultsDiv) return;
        
        const query = textarea.value.trim();
        if (!query) {
            this.showError(resultsDiv, 'Please enter a query');
            return;
        }
        
        resultsDiv.innerHTML = '<div class="loading">Executing query...</div>';
        
        const startTime = performance.now();
        
        try {
            const response = await fetch(`${this.apiBase}/iql`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            const executionTime = performance.now() - startTime;
            
            if (data.status === 'success') {
                const result = data.result;
                
                // Add to history
                this.queryHistory.push({
                    query,
                    timestamp: new Date(),
                    success: true,
                    execution_time_ms: result.execution_time_ms,
                    fields: result.fields
                });
                
                // Display result
                resultsDiv.innerHTML = `
                    <div class="query-result result-success">
                        <div class="result-header">
                            <span class="result-status">✓ Query executed successfully</span>
                            <span class="result-timing">
                                ${result.execution_time_ms.toFixed(2)}ms (backend) + 
                                ${(executionTime - result.execution_time_ms).toFixed(2)}ms (network)
                            </span>
                        </div>
                        
                        ${result.errors && result.errors.length > 0 ? `
                            <div class="result-warnings">
                                <div class="warning-header">⚠️ Warnings:</div>
                                ${result.errors.map(error => `<div class="warning-item">${error}</div>`).join('')}
                            </div>
                        ` : ''}
                        
                        <div class="result-data">
                            <div class="data-header">
                                <strong>Results:</strong> ${Object.keys(result.fields).length} fields returned
                            </div>
                            <div class="data-table">
                                ${this.renderResultTable(result.fields)}
                            </div>
                        </div>
                        
                        <div class="result-meta">
                            <div class="meta-item">
                                <span class="meta-label">Constraints satisfied:</span>
                                <span class="meta-value ${result.constraints_satisfied ? 'value-yes' : 'value-no'}">
                                    ${result.constraints_satisfied ? 'Yes' : 'No'}
                                </span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Query parsed:</span>
                                <span class="meta-value">${result.query.data_source || 'unknown'}</span>
                            </div>
                        </div>
                    </div>
                `;
                
                // Re-render to show history
                setTimeout(() => this.render() && this.attachEventListeners(), 100);
            } else {
                this.queryHistory.push({
                    query,
                    timestamp: new Date(),
                    success: false,
                    error: data.message || 'Query failed'
                });
                
                this.showError(resultsDiv, data.message || 'Query execution failed');
            }
        } catch (error) {
            console.error('[RCL2-IQL] Query error:', error);
            
            this.queryHistory.push({
                query,
                timestamp: new Date(),
                success: false,
                error: error.message
            });
            
            this.showError(resultsDiv, 'Error: ' + error.message);
        }
    }
    
    renderResultTable(fields) {
        const entries = Object.entries(fields);
        
        if (entries.length === 0) {
            return '<div class="info-message">No data returned</div>';
        }
        
        return `
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Field</th>
                        <th>Value</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    ${entries.map(([field, value]) => `
                        <tr>
                            <td class="field-name">${field}</td>
                            <td class="field-value">${this.formatValue(value)}</td>
                            <td class="field-type">${typeof value}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    formatValue(value) {
        if (value === null) return '<span class="value-null">null</span>';
        if (value === undefined) return '<span class="value-undefined">undefined</span>';
        if (typeof value === 'boolean') return `<span class="value-boolean">${value}</span>`;
        if (typeof value === 'number') return `<span class="value-number">${value.toFixed(4)}</span>`;
        if (typeof value === 'object') return `<pre class="value-object">${JSON.stringify(value, null, 2)}</pre>`;
        return this.escapeHtml(String(value));
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showError(container, message) {
        container.innerHTML = `
            <div class="query-result result-error">
                <div class="result-header">
                    <span class="result-status">✗ Query failed</span>
                </div>
                <div class="error-message">
                    <div class="error-icon">⚠️</div>
                    <div class="error-text">${message}</div>
                </div>
            </div>
        `;
    }
}

// Export for use in dashboard
window.RCL2IQL = RCL2IQL;
