/**
 * Main application JavaScript for Deadlock Detection Tool
 * Handles UI interactions, API calls, and state management
 */

class DeadlockApp {
    constructor() {
        this.currentSnapshot = null;
        this.currentWFG = null;
        this.currentCycles = [];
        this.autoRefreshInterval = null;
        this.runtimeStart = Date.now();
        this.graphVisualization = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startRuntimeCounter();
        
        // Test if D3 is available
        if (typeof d3 === 'undefined') {
            this.showToast('error', 'D3.js Error', 'D3.js library failed to load. Please check your internet connection.');
            return;
        }
        
        // Test if container exists
        const container = document.getElementById('graphSvg');
        if (!container) {
            this.showToast('error', 'Container Error', 'Graph container not found in HTML.');
            return;
        }
        
        this.loadDemoSnapshot();
        this.showToast('success', 'Application Loaded', 'Deadlock Detection Tool is ready!');
    }

    setupEventListeners() {
        // Control buttons
        document.getElementById('predictBtn').addEventListener('click', () => this.predict());
        document.getElementById('detectBtn').addEventListener('click', () => this.detect());
        document.getElementById('recoverBtn').addEventListener('click', () => this.recover());
        
        // Data source buttons
        document.getElementById('loadDemoBtn').addEventListener('click', () => this.loadDemoSnapshot());
        document.getElementById('loadSystemBtn').addEventListener('click', () => this.loadSystemSnapshot());
        
        // Auto refresh
        document.getElementById('autoRefreshCheck').addEventListener('change', (e) => {
            this.toggleAutoRefresh(e.target.checked);
        });
        
        // View mode
        document.querySelectorAll('input[name="viewMode"]').forEach(radio => {
            radio.addEventListener('change', () => this.switchViewMode());
        });
        
        // Graph controls
        document.getElementById('zoomInBtn').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoomOut());
        document.getElementById('resetViewBtn').addEventListener('click', () => this.resetView());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    async loadDemoSnapshot() {
        try {
            this.showLoading('Loading demo snapshot...');
            const response = await fetch('/api/demo-snapshot');
            const data = await response.json();
            
            this.currentSnapshot = data;
            this.updateStatus('Demo snapshot loaded', 'idle');
            this.refreshVisualization();
            this.showToast('success', 'Demo Loaded', 'Demo system snapshot loaded successfully');
        } catch (error) {
            this.showToast('error', 'Load Error', 'Failed to load demo snapshot');
            console.error('Error loading demo snapshot:', error);
        } finally {
            this.hideLoading();
        }
    }

    async loadSystemSnapshot() {
        try {
            this.showLoading('Reading system state...');
            const response = await fetch('/api/system-snapshot');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.currentSnapshot = data;
            this.updateStatus('System snapshot loaded', 'success');
            this.refreshVisualization();
            this.showToast('success', 'System Loaded', 'Live system snapshot loaded successfully');
        } catch (error) {
            this.showToast('error', 'System Error', 'Failed to load system snapshot: ' + error.message);
            console.error('Error loading system snapshot:', error);
        } finally {
            this.hideLoading();
        }
    }

    async predict() {
        if (!this.currentSnapshot) {
            this.showToast('warning', 'No Data', 'Please load a snapshot first');
            return;
        }

        try {
            this.updateStatus('Running Banker\'s Algorithm...', 'processing');
            this.showLoading('Analyzing safety...');
            
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentSnapshot)
            });
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            const statusClass = result.safe ? 'success' : 'error';
            const statusText = `Prediction: ${result.message}`;
            
            this.updateStatus(statusText, statusClass);
            this.updateFooter(`Ran Banker's prediction - ${result.details}`);
            
            this.showToast(
                result.safe ? 'success' : 'warning',
                'Safety Analysis Complete',
                result.details
            );
            
            // Animate the result and refresh visualization to show current state
            this.animateResult(statusClass);
            this.refreshVisualization();
            
        } catch (error) {
            this.showToast('error', 'Prediction Error', 'Failed to run prediction: ' + error.message);
            this.updateStatus('Prediction failed', 'error');
            console.error('Error in prediction:', error);
        } finally {
            this.hideLoading();
        }
    }

    async detect() {
        if (!this.currentSnapshot) {
            this.showToast('warning', 'No Data', 'Please load a snapshot first');
            return;
        }

        try {
            this.updateStatus('Detecting cycles...', 'processing');
            this.showLoading('Analyzing wait-for graph...');
            
            const response = await fetch('/api/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentSnapshot)
            });
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            this.currentWFG = result.wfg;
            this.currentCycles = result.cycles;
            
            const statusClass = result.has_deadlock ? 'error' : 'success';
            const statusText = `Detection: ${result.message}`;
            
            this.updateStatus(statusText, statusClass);
            this.updateFooter('Ran WFG detection');
            
            this.showToast(
                result.has_deadlock ? 'error' : 'success',
                'Deadlock Detection Complete',
                result.message
            );
            
            // Switch to WFG view if not already
            if (!document.querySelector('input[name="viewMode"][value="WFG"]').checked) {
                document.querySelector('input[name="viewMode"][value="WFG"]').checked = true;
                this.switchViewMode();
            }
            
            this.animateResult(statusClass);
            
        } catch (error) {
            this.showToast('error', 'Detection Error', 'Failed to detect deadlocks: ' + error.message);
            this.updateStatus('Detection failed', 'error');
            console.error('Error in detection:', error);
        } finally {
            this.hideLoading();
        }
    }

    async recover() {
        if (!this.currentSnapshot) {
            this.showToast('warning', 'No Data', 'Please load a snapshot first');
            return;
        }

        try {
            this.updateStatus('Applying recovery...', 'processing');
            this.showLoading('Choosing victims and applying preemption...');
            
            const response = await fetch('/api/recover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentSnapshot)
            });
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Update snapshot with recovery results
            this.currentSnapshot = result.new_snapshot;
            
            const statusText = `Recovery: ${result.message}`;
            this.updateStatus(statusText, 'success');
            this.updateFooter('Applied recovery simulation');
            
            this.showToast(
                result.victims.length > 0 ? 'warning' : 'success',
                'Recovery Complete',
                result.message
            );
            
            // Refresh visualization with new snapshot
            this.refreshVisualization();
            this.animateResult('success');
            
        } catch (error) {
            this.showToast('error', 'Recovery Error', 'Failed to apply recovery: ' + error.message);
            this.updateStatus('Recovery failed', 'error');
            console.error('Error in recovery:', error);
        } finally {
            this.hideLoading();
        }
    }

    switchViewMode() {
        const selectedMode = document.querySelector('input[name="viewMode"]:checked').value;
        const graphTitle = document.getElementById('graphTitle');
        
        if (selectedMode === 'RAG') {
            graphTitle.textContent = 'Resource Allocation Graph';
        } else {
            graphTitle.textContent = 'Wait-for Graph';
        }
        
        // Always refresh visualization after switching modes
        this.refreshVisualization();
    }

    buildWFGFromSnapshot() {
        if (!this.currentSnapshot) return;
        
        // Simple WFG building logic (matching Python implementation)
        const edges = {};
        const requests = this.currentSnapshot.request;
        const allocations = this.currentSnapshot.allocation;
        
        for (const [key, need] of Object.entries(requests)) {
            if (need <= 0) continue;
            
            const [pidStr, rid] = key.split('_');
            const pid = parseInt(pidStr);
            
            const blockers = [];
            for (const [allocKey, alloc] of Object.entries(allocations)) {
                const [allocPidStr, allocRid] = allocKey.split('_');
                const allocPid = parseInt(allocPidStr);
                
                if (allocRid === rid && alloc > 0 && allocPid !== pid) {
                    blockers.push(allocPid);
                }
            }
            
            if (blockers.length > 0) {
                if (!edges[pid]) edges[pid] = [];
                edges[pid].push(...blockers);
            }
        }
        
        this.currentWFG = edges;
    }

    refreshVisualization() {
        console.log('Refreshing visualization...');
        const selectedMode = document.querySelector('input[name="viewMode"]:checked').value;
        
        // Check if D3 is available
        if (typeof d3 === 'undefined') {
            console.error('D3.js not loaded!');
            this.showToast('error', 'Graph Error', 'D3.js library not loaded. Please refresh the page.');
            return;
        }
        
        // Check if container exists
        const container = document.getElementById('graphSvg');
        if (!container) {
            console.error('Graph container not found!');
            this.showToast('error', 'Graph Error', 'Graph container not found.');
            return;
        }
        
        console.log('Container found, initializing graph...');
        
        // Initialize graph visualization if it doesn't exist
        if (!this.graphVisualization) {
            try {
                this.graphVisualization = new GraphVisualization('graphSvg');
                console.log('Graph visualization initialized');
            } catch (error) {
                console.error('Error initializing graph:', error);
                this.showToast('error', 'Graph Error', 'Failed to initialize graph visualization.');
                return;
            }
        }
        
        if (selectedMode === 'RAG' && this.currentSnapshot) {
            console.log('Rendering RAG with snapshot:', this.currentSnapshot);
            this.graphVisualization.renderRAG(this.currentSnapshot);
        } else if (selectedMode === 'WFG') {
            if (this.currentWFG) {
                console.log('Rendering WFG with cycles:', this.currentCycles);
                this.graphVisualization.renderWFG(this.currentWFG, this.currentCycles);
            } else if (this.currentSnapshot) {
                // Build WFG from current snapshot if not available
                console.log('Building WFG from snapshot...');
                this.buildWFGFromSnapshot();
                if (this.currentWFG) {
                    console.log('Rendering WFG after building:', this.currentWFG);
                    this.graphVisualization.renderWFG(this.currentWFG, this.currentCycles);
                }
            }
        }
        
        // Fallback: if no graph is rendered, show RAG if we have snapshot data
        if (this.currentSnapshot && selectedMode === 'RAG') {
            console.log('Fallback: rendering RAG');
            this.graphVisualization.renderRAG(this.currentSnapshot);
        }
        
        console.log('Visualization refresh complete');
    }

    toggleAutoRefresh(enabled) {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
        
        if (enabled) {
            this.autoRefreshInterval = setInterval(() => {
                this.loadSystemSnapshot();
            }, 2000);
            this.showToast('success', 'Auto-Refresh Enabled', 'System will refresh every 2 seconds');
        } else {
            this.showToast('info', 'Auto-Refresh Disabled', 'Manual refresh only');
        }
    }

    zoomIn() {
        if (this.graphVisualization) {
            this.graphVisualization.zoomIn();
        }
    }

    zoomOut() {
        if (this.graphVisualization) {
            this.graphVisualization.zoomOut();
        }
    }

    resetView() {
        if (this.graphVisualization) {
            this.graphVisualization.resetView();
        }
    }

    updateStatus(text, type = 'idle') {
        const statusDisplay = document.getElementById('statusDisplay');
        const statusText = statusDisplay.querySelector('.status-text');
        const statusIndicator = statusDisplay.querySelector('.status-indicator');
        
        statusText.textContent = text;
        statusIndicator.className = `status-indicator ${type}`;
    }

    updateFooter(text) {
        document.getElementById('footerStatus').textContent = text;
    }

    showLoading(text = 'Processing...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        
        loadingText.textContent = text;
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }

    showToast(type, title, message) {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="toast-icon ${icons[type]}"></i>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    animateResult(type) {
        const statusDisplay = document.getElementById('statusDisplay');
        statusDisplay.classList.add('fade-in');
        
        setTimeout(() => {
            statusDisplay.classList.remove('fade-in');
        }, 300);
        
        // Animate buttons
        const buttons = document.querySelectorAll('.action-btn');
        buttons.forEach(btn => {
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                btn.style.transform = '';
            }, 150);
        });
    }

    handleKeyboard(e) {
        // Keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case '1':
                    e.preventDefault();
                    this.loadDemoSnapshot();
                    break;
                case '2':
                    e.preventDefault();
                    this.loadSystemSnapshot();
                    break;
                case 'p':
                    e.preventDefault();
                    this.predict();
                    break;
                case 'd':
                    e.preventDefault();
                    this.detect();
                    break;
                case 'r':
                    e.preventDefault();
                    this.recover();
                    break;
                case '=':
                case '+':
                    e.preventDefault();
                    this.zoomIn();
                    break;
                case '-':
                    e.preventDefault();
                    this.zoomOut();
                    break;
                case '0':
                    e.preventDefault();
                    this.resetView();
                    break;
            }
        }
    }

    startRuntimeCounter() {
        setInterval(() => {
            const runtime = Date.now() - this.runtimeStart;
            const minutes = Math.floor(runtime / 60000);
            const seconds = Math.floor((runtime % 60000) / 1000);
            document.getElementById('runtime').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
        
        // Simulate memory usage (in a real app, this would come from system)
        setInterval(() => {
            const memory = Math.floor(Math.random() * 100) + 50;
            document.getElementById('memoryUsage').textContent = `${memory} MB`;
        }, 3000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.deadlockApp = new DeadlockApp();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DeadlockApp;
}
