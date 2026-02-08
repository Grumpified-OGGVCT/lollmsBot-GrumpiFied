/**
 * RCL-2 Narrative Identity UI Component
 * 
 * Displays biographical continuity, developmental stages, and life story events.
 */

class RCL2Narrative {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.apiBase = dashboard.apiBase;
        this.currentData = null;
        this.eventLimit = 50;
        
        console.log('[RCL2-Narrative] Initializing...');
    }
    
    async init() {
        await this.loadData();
        this.render();
        this.attachEventListeners();
    }
    
    async loadData() {
        try {
            // Load narrative summary
            const summaryResponse = await fetch(`${this.apiBase}/narrative`);
            const summaryData = await summaryResponse.json();
            
            // Load recent events
            const eventsResponse = await fetch(`${this.apiBase}/narrative/events?limit=${this.eventLimit}`);
            const eventsData = await eventsResponse.json();
            
            this.currentData = {
                summary: summaryData,
                events: eventsData
            };
            
            console.log('[RCL2-Narrative] Data loaded:', this.currentData);
        } catch (error) {
            console.error('[RCL2-Narrative] Error loading data:', error);
            this.currentData = { error: error.message };
        }
    }
    
    render() {
        const panel = document.getElementById('narrative-panel');
        if (!panel || !this.currentData) return;
        
        if (this.currentData.error) {
            panel.innerHTML = `
                <div class="error-message">
                    <div class="error-icon">⚠️</div>
                    <div class="error-text">Failed to load narrative identity: ${this.currentData.error}</div>
                </div>
            `;
            return;
        }
        
        const summary = this.currentData.summary;
        const events = this.currentData.events;
        
        if (summary.status === 'unavailable') {
            panel.innerHTML = `
                <div class="info-message">
                    <div class="info-icon">ℹ️</div>
                    <div class="info-text">Narrative Identity module is not available</div>
                </div>
            `;
            return;
        }
        
        const data = summary.data;
        
        // Map backend fields to frontend expectations
        if (!data.developmental_stage && data.current_stage) {
            data.developmental_stage = data.current_stage.charAt(0).toUpperCase() + data.current_stage.slice(1);
        }
        
        // Defaults for missing scores
        data.developmental_stage = data.developmental_stage || 'Nascent';
        data.coherence_score = data.coherence_score || 0;
        data.maturity_score = data.maturity_score || 0;
        data.total_events = data.total_events || 0;
        
        panel.innerHTML = `
            <div class="narrative-container">
                <!-- Summary Cards -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Developmental Stage</div>
                        <div class="metric-value stage-${data.developmental_stage.toLowerCase()}">
                            ${data.developmental_stage}
                        </div>
                        <div class="metric-subtitle">${this.getStageDescription(data.developmental_stage)}</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Narrative Coherence</div>
                        <div class="metric-value">${(data.coherence_score * 100).toFixed(0)}%</div>
                        <div class="metric-subtitle">${this.getCoherenceStatus(data.coherence_score)}</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Life Story Events</div>
                        <div class="metric-value">${data.total_events}</div>
                        <div class="metric-subtitle">Recorded experiences</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Maturity Score</div>
                        <div class="metric-value">${(data.maturity_score * 100).toFixed(0)}%</div>
                        <div class="metric-subtitle">${this.getMaturityStatus(data.maturity_score)}</div>
                    </div>
                </div>
                
                <!-- Consolidation Info -->
                <div class="card">
                    <div class="card-header">
                        <h3>Latest Consolidation</h3>
                        <button class="btn btn-primary" id="trigger-consolidation">
                            Consolidate Now
                        </button>
                    </div>
                    <div class="card-body">
                        ${data.last_consolidation ? `
                            <div class="consolidation-info">
                                <div class="info-row">
                                    <span class="info-label">Time:</span>
                                    <span class="info-value">${new Date(data.last_consolidation).toLocaleString()}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Since consolidation:</span>
                                    <span class="info-value">${this.timeSince(data.last_consolidation)}</span>
                                </div>
                            </div>
                        ` : `
                            <div class="info-message">No consolidation performed yet</div>
                        `}
                    </div>
                </div>
                
                <!-- Life Story Timeline -->
                <div class="card">
                    <div class="card-header">
                        <h3>Life Story Timeline</h3>
                        <div class="card-subtitle">${events.count || 0} recent events</div>
                    </div>
                    <div class="card-body">
                        ${this.renderEventTimeline(events.events || [])}
                    </div>
                </div>
                
                <!-- Detected Patterns -->
                ${data.detected_patterns && data.detected_patterns.length > 0 ? `
                    <div class="card">
                        <div class="card-header">
                            <h3>Detected Patterns</h3>
                        </div>
                        <div class="card-body">
                            <div class="patterns-list">
                                ${data.detected_patterns.map(pattern => `
                                    <div class="pattern-item">
                                        <div class="pattern-icon">🔍</div>
                                        <div class="pattern-text">${pattern}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                <!-- Contradictions Warning -->
                ${data.contradictions && data.contradictions.length > 0 ? `
                    <div class="card warning-card">
                        <div class="card-header">
                            <h3>⚠️ Detected Contradictions</h3>
                        </div>
                        <div class="card-body">
                            <div class="contradictions-list">
                                ${data.contradictions.map(contradiction => `
                                    <div class="contradiction-item">
                                        <div class="contradiction-text">${contradiction}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    renderEventTimeline(events) {
        if (!events || events.length === 0) {
            return '<div class="info-message">No events recorded yet</div>';
        }
        
        return `
            <div class="timeline">
                ${events.map(event => `
                    <div class="timeline-item">
                        <div class="timeline-marker ${this.getEventClass(event.event_type)}"></div>
                        <div class="timeline-content">
                            <div class="timeline-header">
                                <span class="timeline-type">${event.event_type}</span>
                                <span class="timeline-time">${this.formatTime(event.timestamp)}</span>
                            </div>
                            <div class="timeline-description">${event.description}</div>
                            <div class="timeline-meta">
                                <span class="meta-item">
                                    Significance: ${this.renderSignificance(event.significance)}
                                </span>
                                ${event.emotional_valence !== 0 ? `
                                    <span class="meta-item">
                                        Emotion: ${this.renderEmotion(event.emotional_valence)}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    getStageDescription(stage) {
        const descriptions = {
            'Nascent': 'Just beginning to form identity',
            'Early': 'Developing basic patterns',
            'Intermediate': 'Established core identity',
            'Mature': 'Well-formed self-concept',
            'Expert': 'Deep self-understanding'
        };
        return descriptions[stage] || 'Unknown stage';
    }
    
    getCoherenceStatus(score) {
        if (score >= 0.8) return 'Highly coherent';
        if (score >= 0.6) return 'Moderately coherent';
        if (score >= 0.4) return 'Some inconsistencies';
        return 'Needs consolidation';
    }
    
    getMaturityStatus(score) {
        if (score >= 0.8) return 'Highly mature';
        if (score >= 0.6) return 'Developing well';
        if (score >= 0.4) return 'Early development';
        return 'Very early stage';
    }
    
    getEventClass(eventType) {
        const typeMap = {
            'interaction': 'event-interaction',
            'decision': 'event-decision',
            'learning': 'event-learning',
            'error': 'event-error',
            'milestone': 'event-milestone'
        };
        return typeMap[eventType] || 'event-default';
    }
    
    renderSignificance(value) {
        const filled = Math.round(value * 5);
        return '★'.repeat(filled) + '☆'.repeat(5 - filled);
    }
    
    renderEmotion(valence) {
        if (valence > 0.5) return '😊 Positive';
        if (valence > 0) return '🙂 Slightly positive';
        if (valence < -0.5) return '😞 Negative';
        if (valence < 0) return '😐 Slightly negative';
        return '😐 Neutral';
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
        
        return date.toLocaleDateString();
    }
    
    timeSince(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const hours = Math.floor(diff / 3600000);
        const minutes = Math.floor((diff % 3600000) / 60000);
        
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    }
    
    attachEventListeners() {
        const consolidateBtn = document.getElementById('trigger-consolidation');
        if (consolidateBtn) {
            consolidateBtn.addEventListener('click', () => this.triggerConsolidation());
        }
    }
    
    async triggerConsolidation() {
        const btn = document.getElementById('trigger-consolidation');
        if (!btn) return;
        
        btn.disabled = true;
        btn.textContent = 'Consolidating...';
        
        try {
            const response = await fetch(`${this.apiBase}/narrative/consolidation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Reload data
                await this.loadData();
                this.render();
                this.attachEventListeners();
                
                // Show success message
                this.showNotification('Consolidation complete!', 'success');
            } else {
                this.showNotification('Consolidation failed', 'error');
            }
        } catch (error) {
            console.error('[RCL2-Narrative] Consolidation error:', error);
            this.showNotification('Consolidation error', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Consolidate Now';
        }
    }
    
    showNotification(message, type = 'info') {
        // Simple notification (can be enhanced with toast library)
        console.log(`[RCL2-Narrative] ${type.toUpperCase()}: ${message}`);
        
        // Create temporary notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
            color: white;
            border-radius: 8px;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Export for use in dashboard
window.RCL2Narrative = RCL2Narrative;
