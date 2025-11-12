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
        this.socket = null;
        this.mlPrediction = null;
        this.isRealtimeMode = false;
        this.savedSnapshots = []; // Store saved snapshots
        this.comparisonGraphA = null;
        this.comparisonGraphB = null;
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

        this.graphVisualization = new GraphVisualization('graphSvg');
        this.showToast('success', 'Application Loaded', 'Deadlock Detection Tool is ready!');
    }

    setupEventListeners() {
        // Control buttons
        document.getElementById('predictBtn')?.addEventListener('click', () => this.predict());
        document.getElementById('predictMlBtn')?.addEventListener('click', () => this.predictML());
        document.getElementById('detectBtn')?.addEventListener('click', () => this.detect());
        document.getElementById('recoverBtn')?.addEventListener('click', () => this.recover());

        // Data source buttons
        document.getElementById('loadDemoBtn')?.addEventListener('click', () => this.loadDemoSnapshot());
        document.getElementById('loadSystemBtn')?.addEventListener('click', () => this.loadSystemSnapshot());
        document.getElementById('loadRealtimeBtn')?.addEventListener('click', () => this.loadRealtimeSnapshot());

        // Real-time and analytics
        document.getElementById('toggleRealtimeBtn')?.addEventListener('click', () => this.toggleRealtimeMonitoring());
        document.getElementById('viewAnalyticsBtn')?.addEventListener('click', () => this.showAnalytics());

        // Auto refresh
        document.getElementById('autoRefreshCheck')?.addEventListener('change', (e) => {
            this.toggleAutoRefresh(e.target.checked);
        });

        // View mode
        document.querySelectorAll('input[name="viewMode"]').forEach(radio => {
            radio.addEventListener('change', () => this.switchViewMode());
        });

        // Graph controls
        document.getElementById('zoomInBtn')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOutBtn')?.addEventListener('click', () => this.zoomOut());
        document.getElementById('resetViewBtn')?.addEventListener('click', () => this.resetView());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        document.getElementById('saveSnapshotBtn')?.addEventListener('click', () => this.saveSnapshot());
        document.getElementById('compareBtn')?.addEventListener('click', () => this.openComparisonMode());
        document.getElementById('snapshotA')?.addEventListener('change', (e) => this.loadComparisonSnapshot('A', e.target.value));
        document.getElementById('snapshotB')?.addEventListener('change', (e) => this.loadComparisonSnapshot('B', e.target.value));
        document.getElementById('viewSimulationsBtn')?.addEventListener('click', () => this.showSimulations());
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

    async loadRealtimeSnapshot() {
        try {
            this.showLoading('Reading real file locks from system...');
            this.isRealtimeMode = true;

            const response = await fetch('/api/realtime-snapshot');
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.currentSnapshot = data;
            this.updateStatus('Real-time file lock snapshot loaded', 'success');
            this.refreshVisualization();

            if (data.processes.length === 0) {
                this.showToast('info', 'No Locks Found',
                    'No file locks detected. System may not have lock contention.');
            } else {
                this.showToast('success', 'Real Locks Loaded',
                    `Found ${data.processes.length} processes with file locks`);
            }

        } catch (error) {
            this.showToast('error', 'Real-time Error',
                'Failed to load real locks. Linux only feature. Error: ' + error.message);
            console.error('Error loading real-time snapshot:', error);
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
            let statusText = `Prediction: ${result.message}`;

            if (result.safe_sequence && result.safe_sequence.length > 0) {
                statusText += ` | Safe Sequence: [${result.safe_sequence.join(' → ')}]`;
            }

            this.updateStatus(statusText, statusClass);
            this.updateFooter(`Detection Time: ${result.detection_time_ms}ms`);

            // Show detailed info
            let details = result.details;
            if (result.all_safe_sequences && result.all_safe_sequences.length > 1) {
                details += `\n\nFound ${result.all_safe_sequences.length} possible safe sequences`;
            }

            if (result.resource_utilization) {
                details += '\n\nResource Utilization:';
                for (const [rid, util] of Object.entries(result.resource_utilization)) {
                    details += `\n${rid}: ${util.toFixed(1)}%`;
                }
            }

            this.showToast(
                result.safe ? 'success' : 'warning',
                'Safety Analysis Complete',
                details
            );

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
            let statusText = `Detection: ${result.message}`;

            // Add algorithm comparison
            if (result.cycles_tarjan) {
                const tarjanMatch = result.cycles.length === result.cycles_tarjan.length;
                statusText += ` | Tarjan's: ${result.cycles_tarjan.length} cycles`;
                if (tarjanMatch) {
                    statusText += ' ✓';
                }
            }

            statusText += ` | Time: ${result.detection_time_ms}ms`;

            this.updateStatus(statusText, statusClass);
            this.updateFooter('Ran WFG detection with multiple algorithms');

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
            this.updateFooter(`Recovery Time: ${result.recovery_time_ms}ms`);

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

    async predictML() {
        if (!this.currentSnapshot) {
            this.showToast('warning', 'No Data', 'Please load a snapshot first');
            return;
        }

        try {
            this.updateStatus('Running ML prediction...', 'processing');
            this.showLoading('Analyzing with machine learning...');

            const response = await fetch('/api/predict-ml', {
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

            this.mlPrediction = result;

            const probability = (result.probability * 100).toFixed(1);
            const statusText = `ML Prediction: ${result.risk_level} Risk (${probability}% probability)`;

            const statusClass = result.risk_level === 'LOW' ? 'success' :
                result.risk_level === 'MEDIUM' ? 'warning' : 'error';

            this.updateStatus(statusText, statusClass);

            // Show feature importance
            let details = `Deadlock Probability: ${probability}%\nRisk Level: ${result.risk_level}`;

            if (result.feature_importance) {
                details += '\n\nTop Contributing Factors:';
                const sorted = Object.entries(result.feature_importance)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3);

                for (const [feature, importance] of sorted) {
                    details += `\n• ${feature}: ${(importance * 100).toFixed(1)}%`;
                }
            }

            this.showToast(
                statusClass,
                'ML Prediction Complete',
                details
            );

            // Display ML probability on UI
            this.displayMLProbability(result);

        } catch (error) {
            this.showToast('error', 'ML Prediction Error', error.message);
            console.error('Error in ML prediction:', error);
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

    toggleRealtimeMonitoring() {
        const btn = document.getElementById('toggleRealtimeBtn');

        if (this.socket && this.socket.connected) {
            // Stop monitoring
            this.socket.disconnect();
            this.socket = null;
            btn.textContent = '▶️ Start Real-Time';
            btn.classList.remove('active');
            this.showToast('info', 'Monitoring Stopped', 'Real-time monitoring disabled');
        } else {
            // Start monitoring
            this.startRealtimeMonitoring();
            btn.textContent = '⏸️ Stop Real-Time';
            btn.classList.add('active');
            this.showToast('success', 'Monitoring Started', 'Real-time updates every 2 seconds');
        }
    }

    startRealtimeMonitoring() {
        // Initialize Socket.IO
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.socket.emit('start_monitoring');
        });

        this.socket.on('system_update', (data) => {
            console.log('Real-time update received:', data);

            // Update snapshot
            this.currentSnapshot = data.snapshot;
            this.currentCycles = data.cycles;

            // Update ML probability
            if (data.ml_probability !== undefined) {
                this.displayMLProbability({
                    probability: data.ml_probability,
                    risk_level: data.ml_probability > 0.7 ? 'HIGH' :
                        data.ml_probability > 0.4 ? 'MEDIUM' : 'LOW'
                });
            }

            // Update visualization
            this.refreshVisualization();

            // Update status
            if (data.cycles.length > 0) {
                this.updateStatus(`🚨 DEADLOCK DETECTED: ${data.cycles.length} cycle(s)`, 'error');
            } else {
                this.updateStatus('✅ System healthy - No deadlocks', 'success');
            }
        });

        this.socket.on('error', (error) => {
            console.error('WebSocket error:', error);
            this.showToast('error', 'Monitoring Error', error.message);
        });
    }

    async showAnalytics() {
        try {
            this.showLoading('Loading analytics...');

            const response = await fetch('/api/analytics/trends?days=7');
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Create analytics modal
            this.displayAnalyticsModal(data);

        } catch (error) {
            this.showToast('error', 'Analytics Error', error.message);
            console.error('Error loading analytics:', error);
        } finally {
            this.hideLoading();
        }
    }

    displayAnalyticsModal(data) {
        const modal = document.createElement('div');
        modal.className = 'analytics-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>📊 Deadlock Analytics (Last 7 Days)</h2>
                    <button class="close-btn" onclick="this.closest('.analytics-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">${data.trends.total_deadlocks}</div>
                            <div class="stat-label">Total Deadlocks</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.trends.avg_cycles}</div>
                            <div class="stat-label">Avg Cycles</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.trends.avg_detection_time_ms}ms</div>
                            <div class="stat-label">Avg Detection Time</div>
                        </div>
                    </div>
                    
                    <h3>Most Affected Processes</h3>
                    <table class="analytics-table">
                        <thead>
                            <tr>
                                <th>Process ID</th>
                                <th>Deadlock Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.most_affected_processes.map(p => `
                                <tr>
                                    <td>PID ${p.pid}</td>
                                    <td>${p.deadlock_count}</td>
                                </tr>
                            `).join('') || '<tr><td colspan="2">No data available</td></tr>'}
                        </tbody>
                    </table>
                    
                    <h3>Peak Hours</h3>
                    <div class="peak-hours">
                        ${Object.entries(data.trends.peak_hours || {})
                .map(([hour, count]) => `
                                <div class="hour-bar">
                                    <span>${hour}:00</span>
                                    <div class="bar" style="width: ${count * 20}px">${count}</div>
                                </div>
                            `).join('')}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    displayMLProbability(mlResult) {
        // Add ML probability indicator to status section
        const statusSection = document.querySelector('.status-section');

        let mlDisplay = document.getElementById('ml-probability-display');
        if (!mlDisplay) {
            mlDisplay = document.createElement('div');
            mlDisplay.id = 'ml-probability-display';
            mlDisplay.className = 'ml-display';
            statusSection.appendChild(mlDisplay);
        }

        const probability = (mlResult.probability * 100).toFixed(1);
        const riskClass = mlResult.risk_level.toLowerCase();

        mlDisplay.innerHTML = `
            <h4>🤖 ML Prediction</h4>
            <div class="ml-probability ${riskClass}">
                <div class="probability-bar">
                    <div class="probability-fill" style="width: ${probability}%"></div>
                </div>
                <div class="probability-text">
                    ${probability}% - ${mlResult.risk_level} Risk
                </div>
            </div>
        `;
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

    // Add these new methods to DeadlockApp class

    saveSnapshot() {
        if (!this.currentSnapshot) {
            this.showToast('warning', 'No Data', 'Please load a snapshot first');
            return;
        }

        const timestamp = new Date().toISOString();
        const name = `Snapshot ${this.savedSnapshots.length + 1}`;

        const savedSnapshot = {
            id: Date.now(),
            name: name,
            timestamp: timestamp,
            data: JSON.parse(JSON.stringify(this.currentSnapshot)), // Deep copy
            cycles: this.currentCycles ? [...this.currentCycles] : [],
            wfg: this.currentWFG ? JSON.parse(JSON.stringify(this.currentWFG)) : null
        };

        this.savedSnapshots.push(savedSnapshot);
        this.showToast('success', 'Snapshot Saved', `Saved as "${name}"`);

        // Update comparison dropdowns
        this.updateComparisonDropdowns();
    }

    updateComparisonDropdowns() {
        const selectA = document.getElementById('snapshotA');
        const selectB = document.getElementById('snapshotB');

        if (!selectA || !selectB) return;

        // Clear existing options except first
        selectA.innerHTML = '<option value="">Select snapshot...</option>';
        selectB.innerHTML = '<option value="">Select snapshot...</option>';

        // Add saved snapshots
        this.savedSnapshots.forEach(snapshot => {
            const optionA = document.createElement('option');
            optionA.value = snapshot.id;
            optionA.textContent = `${snapshot.name} (${new Date(snapshot.timestamp).toLocaleString()})`;
            selectA.appendChild(optionA);

            const optionB = optionA.cloneNode(true);
            selectB.appendChild(optionB);
        });
    }

    openComparisonMode() {
        if (this.savedSnapshots.length < 2) {
            this.showToast('warning', 'Not Enough Data',
                'Please save at least 2 snapshots to compare. Use "Save for Comparison" button.');
            return;
        }

        this.updateComparisonDropdowns();
        document.getElementById('comparisonModal').classList.remove('hidden');

        // Initialize comparison graphs if not already
        if (!this.comparisonGraphA) {
            this.comparisonGraphA = new GraphVisualization('graphA');
        }
        if (!this.comparisonGraphB) {
            this.comparisonGraphB = new GraphVisualization('graphB');
        }
    }

    loadComparisonSnapshot(side, snapshotId) {
        if (!snapshotId) return;

        const snapshot = this.savedSnapshots.find(s => s.id == snapshotId);
        if (!snapshot) return;

        // Render graph
        const graphViz = side === 'A' ? this.comparisonGraphA : this.comparisonGraphB;
        if (graphViz) {
            graphViz.renderRAG(snapshot.data);
        }

        // Display stats
        this.displayComparisonStats(side, snapshot);

        // If both snapshots loaded, show diff
        const selectA = document.getElementById('snapshotA');
        const selectB = document.getElementById('snapshotB');

        if (selectA.value && selectB.value) {
            const snapshotA = this.savedSnapshots.find(s => s.id == selectA.value);
            const snapshotB = this.savedSnapshots.find(s => s.id == selectB.value);
            this.displayDifferences(snapshotA, snapshotB);
        }
    }

    displayComparisonStats(side, snapshot) {
        const statsDiv = document.getElementById(`stats${side}`);

        const numProcesses = snapshot.data.processes.length;
        const numResources = Object.keys(snapshot.data.resources).length;
        const numAllocations = Object.values(snapshot.data.allocation).reduce((sum, val) => sum + val, 0);
        const numRequests = Object.values(snapshot.data.request).reduce((sum, val) => sum + val, 0);
        const hasCycles = snapshot.cycles.length > 0;

        statsDiv.innerHTML = `
        <div class="stat-row">
            <span class="stat-label">Processes:</span>
            <span class="stat-value">${numProcesses}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Resources:</span>
            <span class="stat-value">${numResources}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Allocations:</span>
            <span class="stat-value">${numAllocations}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Requests:</span>
            <span class="stat-value">${numRequests}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Deadlock:</span>
            <span class="stat-value" style="color: ${hasCycles ? '#ef4444' : '#10b981'}">
                ${hasCycles ? `Yes (${snapshot.cycles.length} cycles)` : 'No'}
            </span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Timestamp:</span>
            <span class="stat-value">${new Date(snapshot.timestamp).toLocaleTimeString()}</span>
        </div>
    `;
    }

    displayDifferences(snapshotA, snapshotB) {
        const diffDiv = document.getElementById('diffResults');
        const differences = [];

        // Compare processes
        const processesA = new Set(snapshotA.data.processes.map(p => p.pid));
        const processesB = new Set(snapshotB.data.processes.map(p => p.pid));

        processesB.forEach(pid => {
            if (!processesA.has(pid)) {
                differences.push({
                    type: 'added',
                    icon: 'fas fa-plus-circle',
                    text: `Process P${pid} was added`
                });
            }
        });

        processesA.forEach(pid => {
            if (!processesB.has(pid)) {
                differences.push({
                    type: 'removed',
                    icon: 'fas fa-minus-circle',
                    text: `Process P${pid} was removed`
                });
            }
        });

        // Compare cycles
        const cyclesA = snapshotA.cycles.length;
        const cyclesB = snapshotB.cycles.length;

        if (cyclesA !== cyclesB) {
            const change = cyclesB - cyclesA;
            differences.push({
                type: change > 0 ? 'removed' : 'added',
                icon: change > 0 ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle',
                text: `Deadlock cycles changed from ${cyclesA} to ${cyclesB} (${change > 0 ? '+' : ''}${change})`
            });
        }

        // Compare allocations
        const allocA = Object.keys(snapshotA.data.allocation).length;
        const allocB = Object.keys(snapshotB.data.allocation).length;

        if (allocA !== allocB) {
            differences.push({
                type: 'changed',
                icon: 'fas fa-exchange-alt',
                text: `Resource allocations changed from ${allocA} to ${allocB}`
            });
        }

        // Compare requests
        const reqA = Object.keys(snapshotA.data.request).length;
        const reqB = Object.keys(snapshotB.data.request).length;

        if (reqA !== reqB) {
            differences.push({
                type: 'changed',
                icon: 'fas fa-exchange-alt',
                text: `Resource requests changed from ${reqA} to ${reqB}`
            });
        }

        // Display differences
        if (differences.length === 0) {
            diffDiv.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No significant differences detected</p>';
        } else {
            diffDiv.innerHTML = differences.map(diff => `
            <div class="diff-item ${diff.type}">
                <i class="diff-icon ${diff.icon}"></i>
                <span class="diff-text">${diff.text}</span>
            </div>
        `).join('');
        }
    }
    // Add these new methods to the DeadlockApp class
    async showSimulations() {
        try {
            this.showLoading('Loading simulations...');
            const response = await fetch('/api/simulations');
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            this.displaySimulationsModal(data.scenarios);
        } catch (error) {
            this.showToast('error', 'Simulation Error', error.message);
        } finally {
            this.hideLoading();
        }
    }

    displaySimulationsModal(scenarios) {
        const modal = document.createElement('div');
        modal.className = 'analytics-modal'; // Reuse analytics modal styles
        modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>🎓 Deadlock Simulation Scenarios</h2>
                <button class="close-btn" onclick="this.closest('.analytics-modal').remove()">×</button>
            </div>
            <div class="modal-body">
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                    Load classic deadlock scenarios for demonstration and learning
                </p>
                <div class="simulation-grid">
                    ${Object.entries(scenarios).map(([key, info]) => `
                        <div class="simulation-card" onclick="window.deadlockApp.loadSimulation('${key}')">
                            <div class="simulation-icon">${info.icon}</div>
                            <h3>${info.name}</h3>
                            <p class="simulation-desc">${info.description}</p>
                            <div class="simulation-meta">
                                <span class="badge ${info.type.toLowerCase().replace(' ', '-')}">${info.type}</span>
                                <span class="difficulty ${info.difficulty.toLowerCase()}">${info.difficulty}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
        document.body.appendChild(modal);
    }

    async loadSimulation(scenarioKey) {
        try {
            // Close modal
            document.querySelector('.analytics-modal')?.remove();

            this.showLoading(`Loading ${scenarioKey} simulation...`);
            const response = await fetch(`/api/simulate/${scenarioKey}`);
            const data = await response.json();

            if (data.error) throw new Error(data.error);

            this.currentSnapshot = data.snapshot;
            this.updateStatus(`Simulation loaded: ${data.info.name}`, 'success');
            this.refreshVisualization();

            this.showToast('success', 'Simulation Loaded',
                `${data.info.icon} ${data.info.name}\n${data.info.description}`);
        } catch (error) {
            this.showToast('error', 'Simulation Error', error.message);
        } finally {
            this.hideLoading();
        }
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
