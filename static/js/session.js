/**
 * Session Management for MEDLEY
 * Handles localStorage for recent analyses and user preferences
 */

class MedleySession {
    constructor() {
        this.storageKey = 'medley_session';
        this.recentKey = 'medley_recent_analyses';
        this.prefsKey = 'medley_preferences';
        this.maxRecent = 10;
        this.init();
    }

    init() {
        // Initialize storage if not exists
        if (!localStorage.getItem(this.storageKey)) {
            localStorage.setItem(this.storageKey, JSON.stringify({
                sessionId: this.generateSessionId(),
                createdAt: new Date().toISOString(),
                lastAccess: new Date().toISOString()
            }));
        }
        
        if (!localStorage.getItem(this.recentKey)) {
            localStorage.setItem(this.recentKey, JSON.stringify([]));
        }
        
        if (!localStorage.getItem(this.prefsKey)) {
            localStorage.setItem(this.prefsKey, JSON.stringify({
                consensusThreshold: 30,
                minorityThreshold: 10,
                autoSave: true,
                showRaw: true,
                notifications: true,
                theme: 'light'
            }));
        }
        
        // Update last access
        this.updateLastAccess();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    updateLastAccess() {
        const session = JSON.parse(localStorage.getItem(this.storageKey));
        session.lastAccess = new Date().toISOString();
        localStorage.setItem(this.storageKey, JSON.stringify(session));
    }

    // Recent Analyses Management
    addRecentAnalysis(analysis) {
        const recent = this.getRecentAnalyses();
        
        // Add to beginning of array
        recent.unshift({
            id: 'analysis_' + Date.now(),
            timestamp: new Date().toISOString(),
            ...analysis
        });
        
        // Keep only the most recent
        if (recent.length > this.maxRecent) {
            recent.splice(this.maxRecent);
        }
        
        localStorage.setItem(this.recentKey, JSON.stringify(recent));
        this.updateRecentAnalysesUI();
    }

    getRecentAnalyses() {
        return JSON.parse(localStorage.getItem(this.recentKey) || '[]');
    }

    clearRecentAnalyses() {
        localStorage.setItem(this.recentKey, JSON.stringify([]));
        this.updateRecentAnalysesUI();
    }

    removeRecentAnalysis(id) {
        const recent = this.getRecentAnalyses();
        const filtered = recent.filter(a => a.id !== id);
        localStorage.setItem(this.recentKey, JSON.stringify(filtered));
        this.updateRecentAnalysesUI();
    }

    // Preferences Management
    getPreferences() {
        return JSON.parse(localStorage.getItem(this.prefsKey));
    }

    setPreference(key, value) {
        const prefs = this.getPreferences();
        prefs[key] = value;
        localStorage.setItem(this.prefsKey, JSON.stringify(prefs));
    }

    setPreferences(prefs) {
        localStorage.setItem(this.prefsKey, JSON.stringify(prefs));
    }

    // UI Updates
    updateRecentAnalysesUI() {
        const container = document.getElementById('recent-analyses-sidebar');
        if (!container) return;
        
        const recent = this.getRecentAnalyses();
        
        if (recent.length === 0) {
            container.innerHTML = `
                <div style="padding: 16px; text-align: center; color: var(--md-sys-color-on-surface-variant);">
                    <span class="material-symbols-rounded" style="font-size: 48px; opacity: 0.5;">history</span>
                    <p style="margin-top: 8px;">No recent analyses</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = recent.map(analysis => `
            <div class="recent-analysis-item" data-id="${analysis.id}" 
                 style="padding: 12px; border-bottom: 1px solid var(--md-sys-color-outline-variant); 
                        cursor: pointer; transition: background 0.2s;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="font-weight: 500; margin-bottom: 4px;">
                            ${analysis.title || 'Untitled Analysis'}
                        </div>
                        <div style="font-size: 12px; color: var(--md-sys-color-on-surface-variant);">
                            ${analysis.caseType || 'Custom Case'}
                        </div>
                        <div style="font-size: 11px; color: var(--md-sys-color-on-surface-variant); margin-top: 4px;">
                            ${this.formatTime(analysis.timestamp)}
                        </div>
                    </div>
                    <button class="btn-icon" onclick="medleySession.removeRecentAnalysis('${analysis.id}')" 
                            style="background: none; border: none; cursor: pointer; padding: 4px;">
                        <span class="material-symbols-rounded" style="font-size: 18px;">close</span>
                    </button>
                </div>
                ${analysis.primaryDiagnosis ? `
                    <div style="margin-top: 8px; padding: 4px 8px; background: var(--md-sys-color-primary-container); 
                                border-radius: 4px; font-size: 12px;">
                        ${analysis.primaryDiagnosis}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        // Add click handlers
        container.querySelectorAll('.recent-analysis-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.btn-icon')) {
                    const analysis = recent.find(a => a.id === item.dataset.id);
                    if (analysis && analysis.url) {
                        window.location.href = analysis.url;
                    }
                }
            });
            
            item.addEventListener('mouseenter', (e) => {
                item.style.background = 'var(--md-sys-color-surface-variant)';
            });
            
            item.addEventListener('mouseleave', (e) => {
                item.style.background = 'transparent';
            });
        });
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;
        
        return date.toLocaleDateString();
    }

    // Session Statistics
    getSessionStats() {
        const session = JSON.parse(localStorage.getItem(this.storageKey));
        const recent = this.getRecentAnalyses();
        
        return {
            sessionId: session.sessionId,
            sessionDuration: this.calculateDuration(session.createdAt),
            totalAnalyses: recent.length,
            lastAnalysis: recent.length > 0 ? recent[0].timestamp : null
        };
    }

    calculateDuration(startTime) {
        const start = new Date(startTime);
        const now = new Date();
        const diff = now - start;
        
        const hours = Math.floor(diff / 3600000);
        const minutes = Math.floor((diff % 3600000) / 60000);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    }

    // Export/Import Session Data
    exportSession() {
        const data = {
            session: JSON.parse(localStorage.getItem(this.storageKey)),
            recent: this.getRecentAnalyses(),
            preferences: this.getPreferences(),
            exportedAt: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `medley_session_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    importSession(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                
                if (data.session) {
                    localStorage.setItem(this.storageKey, JSON.stringify(data.session));
                }
                if (data.recent) {
                    localStorage.setItem(this.recentKey, JSON.stringify(data.recent));
                }
                if (data.preferences) {
                    localStorage.setItem(this.prefsKey, JSON.stringify(data.preferences));
                }
                
                this.updateRecentAnalysesUI();
                alert('Session imported successfully!');
            } catch (error) {
                alert('Failed to import session: Invalid file format');
            }
        };
        reader.readAsText(file);
    }

    // Clear All Data
    clearAllData() {
        if (confirm('Are you sure you want to clear all session data? This cannot be undone.')) {
            localStorage.removeItem(this.storageKey);
            localStorage.removeItem(this.recentKey);
            localStorage.removeItem(this.prefsKey);
            this.init();
            this.updateRecentAnalysesUI();
            alert('All session data cleared');
        }
    }
}

// Initialize session manager
const medleySession = new MedleySession();

// Auto-save current page to recent if it's a case or analysis
window.addEventListener('load', function() {
    const path = window.location.pathname;
    
    if (path.startsWith('/case/')) {
        // Extract case info from page
        setTimeout(() => {
            const title = document.getElementById('case-title')?.textContent;
            const primary = document.getElementById('primary-diagnosis-name')?.textContent;
            
            if (title && title !== 'Loading...') {
                medleySession.addRecentAnalysis({
                    title: title,
                    caseType: 'Predefined Case',
                    primaryDiagnosis: primary,
                    url: window.location.href
                });
            }
        }, 2000); // Wait for page to load
    }
});

// Export session manager to global scope
window.medleySession = medleySession;