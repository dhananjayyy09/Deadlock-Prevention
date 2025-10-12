# Deadlock Detection Tool - Web Version

A modern, interactive web application for deadlock prediction, detection, and recovery with beautiful animations and smooth user experience.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation & Setup

1. **Install Dependencies**
   ```bash
   cd deadlock_tool
   pip install -r requirements.txt
   ```

2. **Run the Web Application**
   ```bash
   python run_web.py
   ```

3. **Open in Browser**
   Navigate to: http://localhost:5000

## ✨ Features

### 🎨 Modern UI/UX
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Smooth Animations**: Powered by CSS transitions and Anime.js
- **Interactive Graphs**: D3.js-powered visualizations with zoom/pan
- **Real-time Updates**: Live system monitoring with auto-refresh
- **Toast Notifications**: Beautiful feedback for all actions
- **Dark Mode Support**: Automatic theme switching

### 🔧 Core Functionality
- **Banker's Algorithm**: Predict safe/unsafe states
- **Wait-for Graph Detection**: Find deadlock cycles
- **Recovery Strategies**: Automatic victim selection and preemption
- **Live System Integration**: Real-time process monitoring via psutil
- **Demo Mode**: Pre-configured examples for learning

### 🎮 Interactive Features
- **Drag & Drop**: Move nodes around the graph
- **Zoom & Pan**: Navigate large graphs easily
- **Hover Effects**: Highlight connected nodes and edges
- **Tooltips**: Detailed information on hover
- **Keyboard Shortcuts**: Quick access to all functions

## 🎯 How to Use

### 1. Load Data
- **Demo Snapshot**: Click "Load Demo Snapshot" for a pre-configured example
- **System Snapshot**: Click "Load System Snapshot" to read live system state
- **Auto-Refresh**: Enable to continuously monitor system changes

### 2. Analyze Deadlocks
- **Predict**: Run Banker's Algorithm to check if current state is safe
- **Detect**: Use Wait-for Graph to find actual deadlock cycles
- **Recover**: Apply recovery strategies to break deadlocks

### 3. Visualize Results
- **RAG View**: See Resource Allocation Graph with processes and resources
- **WFG View**: View Wait-for Graph showing process dependencies
- **Cycle Highlighting**: Deadlocked processes are highlighted in red

## 🎨 Visual Elements

### Graph Components
- **🔵 Process Nodes**: Blue circles representing system processes
- **🟢 Resource Nodes**: Green squares representing system resources
- **⚫ Allocation Edges**: Solid arrows showing resource allocations
- **🔴 Request Edges**: Dashed red arrows showing resource requests
- **🔴 Cycle Nodes**: Red nodes indicating deadlocked processes

### Color Coding
- **Blue (#2563eb)**: Safe processes and allocations
- **Green (#10b981)**: Resources and safe operations
- **Red (#ef4444)**: Deadlocked processes and dangerous requests
- **Gray (#64748b)**: Neutral elements and text

## ⌨️ Keyboard Shortcuts

- `Ctrl+1`: Load demo snapshot
- `Ctrl+2`: Load system snapshot
- `Ctrl+P`: Run prediction (Banker's)
- `Ctrl+D`: Run detection (WFG)
- `Ctrl+R`: Apply recovery
- `Ctrl++`: Zoom in
- `Ctrl+-`: Zoom out
- `Ctrl+0`: Reset view

## 🔧 Technical Details

### Architecture
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Flask (Python)
- **Visualization**: D3.js v7
- **Animations**: Anime.js + CSS Transitions
- **Icons**: Font Awesome 6

### API Endpoints
- `GET /`: Main application page
- `GET /api/demo-snapshot`: Load demo data
- `GET /api/system-snapshot`: Load live system data
- `POST /api/predict`: Run Banker's algorithm
- `POST /api/detect`: Run WFG detection
- `POST /api/recover`: Apply recovery strategies

### Browser Compatibility
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚨 Troubleshooting

### Common Issues

1. **Port 5000 in use**
   ```bash
   # Kill process using port 5000
   lsof -ti:5000 | xargs kill -9
   ```

2. **Permission errors on system snapshot**
   - Run with elevated permissions
   - Some system info may be limited

3. **Graph not rendering**
   - Check browser console for JavaScript errors
   - Ensure D3.js is loading properly

4. **Styling issues**
   - Clear browser cache
   - Check CSS file is loading

### Performance Tips
- Use demo snapshots for testing (faster)
- Disable auto-refresh for large systems
- Close other browser tabs for better performance

## 🎓 Educational Use

This tool is perfect for:
- **Operating Systems Courses**: Understanding deadlock concepts
- **System Administration**: Learning resource management
- **Computer Science Education**: Visualizing complex algorithms
- **Research Projects**: Analyzing system behavior

## 🔮 Future Enhancements

- [ ] Multiple algorithm implementations
- [ ] Export/import system snapshots
- [ ] Performance metrics and analytics
- [ ] Collaborative features
- [ ] Mobile app version
- [ ] Advanced recovery strategies

## 📄 License

Academic use - See main project license.

---

**Enjoy exploring deadlock detection with this beautiful, interactive tool! 🎉**
