/**
 * D3.js Graph Visualization for Deadlock Detection Tool
 * Handles RAG (Resource Allocation Graph) and WFG (Wait-for Graph) rendering
 */

class GraphVisualization {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = d3.select(`#${containerId}`);
        this.width = 800;
        this.height = 600;
        this.zoom = d3.zoom();
        this.scale = 1;
        this.translate = [0, 0];

        this.setupSVG();
        this.setupZoom();
    }

    setupSVG() {
        // Clear existing content
        this.container.selectAll("*").remove();

        // Create SVG
        this.svg = this.container
            .append("svg")
            .attr("width", this.width)
            .attr("height", this.height)
            .attr("viewBox", `0 0 ${this.width} ${this.height}`)
            .style("background", "transparent");

        // Create main group for zoom/pan
        this.g = this.svg.append("g");

        // Create groups for different elements
        this.linkGroup = this.g.append("g").attr("class", "links");
        this.nodeGroup = this.g.append("g").attr("class", "nodes");
        this.labelGroup = this.g.append("g").attr("class", "labels");
    }

    setupZoom() {
        this.zoom
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                this.g.attr("transform", event.transform);
                this.scale = event.transform.k;
                this.translate = [event.transform.x, event.transform.y];
            });

        this.svg.call(this.zoom);
    }

    renderRAG(snapshot) {
        console.log('Rendering RAG with snapshot:', snapshot);
        const graph = this.buildRAGGraph(snapshot);
        console.log('Built RAG graph:', graph);
        this.renderGraph(graph, 'rag');
    }

    renderWFG(wfg, cycles = []) {
        const graph = this.buildWFGGraph(wfg, cycles);
        this.renderGraph(graph, 'wfg');
    }

    buildRAGGraph(snapshot) {
        const nodes = [];
        const links = [];

        // Add process nodes
        snapshot.processes.forEach(process => {
            nodes.push({
                id: `P${process.pid}`,
                name: `P${process.pid}`,
                type: 'process',
                pid: process.pid,
                ...process
            });
        });

        // Add resource nodes
        Object.entries(snapshot.resources).forEach(([rid, resource]) => {
            nodes.push({
                id: `R${rid}`,
                name: `R${rid}`,
                type: 'resource',
                rid: rid,
                total: resource.total,
                ...resource
            });
        });

        // Add allocation edges
        Object.entries(snapshot.allocation).forEach(([key, count]) => {
            if (count > 0) {
                const [pidStr, rid] = key.split('_');
                links.push({
                    source: `P${pidStr}`,
                    target: `R${rid}`,
                    type: 'allocation',
                    weight: count,
                    id: `alloc_${key}`
                });
            }
        });

        // Add request edges
        Object.entries(snapshot.request).forEach(([key, count]) => {
            if (count > 0) {
                const [pidStr, rid] = key.split('_');
                links.push({
                    source: `R${rid}`,
                    target: `P${pidStr}`,
                    type: 'request',
                    weight: count,
                    id: `req_${key}`
                });
            }
        });

        return { nodes, links };
    }

    buildWFGGraph(wfg, cycles = []) {
        const nodes = [];
        const links = [];
        const cycleNodes = new Set();

        // Collect all cycle nodes
        cycles.forEach(cycle => {
            cycle.forEach(pid => cycleNodes.add(pid));
        });

        // Add process nodes
        const allPids = new Set();
        Object.keys(wfg).forEach(pid => {
            allPids.add(parseInt(pid));
            wfg[pid].forEach(targetPid => allPids.add(targetPid));
        });

        allPids.forEach(pid => {
            nodes.push({
                id: `P${pid}`,
                name: `P${pid}`,
                type: 'process',
                pid: pid,
                inCycle: cycleNodes.has(pid)
            });
        });

        // Add wait-for edges
        Object.entries(wfg).forEach(([srcPid, targets]) => {
            targets.forEach(targetPid => {
                links.push({
                    source: `P${srcPid}`,
                    target: `P${targetPid}`,
                    type: 'wait-for',
                    id: `wfg_${srcPid}_${targetPid}`
                });
            });
        });

        return { nodes, links };
    }

    renderGraph(graph, graphType) {
        console.log('Rendering graph:', graphType, graph);
        const { nodes, links } = graph;

        console.log('Nodes:', nodes);
        console.log('Links:', links);

        // Clear previous content
        this.linkGroup.selectAll("*").remove();
        this.nodeGroup.selectAll("*").remove();
        this.labelGroup.selectAll("*").remove();

        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(40))
            .alpha(0.3)
            .restart();

        // Add links
        const link = this.linkGroup
            .selectAll("line")
            .data(links)
            .enter()
            .append("line")
            .attr("class", d => `link link-${d.type}`)
            .style("stroke", d => this.getEdgeColor(d.type))
            .style("stroke-width", 2)
            .style("stroke-dasharray", d => d.type === 'request' ? "5,5" : "none");

        // Add link labels
        const linkLabels = this.labelGroup
            .selectAll("text")
            .data(links.filter(d => d.weight))
            .enter()
            .append("text")
            .attr("class", "edge-label")
            .text(d => d.weight)
            .style("font-size", "12px")
            .style("fill", "#64748b");

        // Add nodes
        const node = this.nodeGroup
            .selectAll("circle")
            .data(nodes)
            .enter()
            .append("circle")
            .attr("class", d => `node node-${d.type} ${d.inCycle ? 'node-cycle' : ''}`)
            .attr("r", d => this.getNodeRadius(d))
            .style("fill", d => this.getNodeColor(d))
            .style("stroke", d => this.getNodeStrokeColor(d))
            .style("stroke-width", 3)
            .call(this.drag(simulation));

        // Add node labels
        const nodeLabels = this.labelGroup
            .selectAll("text")
            .data(nodes)
            .enter()
            .append("text")
            .attr("class", "node-label")
            .text(d => d.name)
            .style("font-size", "14px")
            .style("font-weight", "600")
            .style("fill", "white")
            .style("text-anchor", "middle")
            .style("dominant-baseline", "central");

        // Add hover effects
        node
            .on("mouseover", function (event, d) {
                // Highlight connected nodes and links
                const connectedNodes = new Set();
                const connectedLinks = [];

                links.forEach(link => {
                    if (link.source.id === d.id || link.target.id === d.id) {
                        connectedLinks.push(link);
                        connectedNodes.add(link.source.id);
                        connectedNodes.add(link.target.id);
                    }
                });

                // Dim all elements
                node.style("opacity", 0.3);
                link.style("opacity", 0.3);
                nodeLabels.style("opacity", 0.3);
                linkLabels.style("opacity", 0.3);

                // Highlight connected elements
                connectedNodes.forEach(nodeId => {
                    node.filter(d => d.id === nodeId).style("opacity", 1);
                    nodeLabels.filter(d => d.id === nodeId).style("opacity", 1);
                });

                connectedLinks.forEach(linkData => {
                    link.filter(d => d.id === linkData.id).style("opacity", 1);
                    linkLabels.filter(d => d.id === linkData.id).style("opacity", 1);
                });

                // Show tooltip
                showTooltip(event, d);
            })
            .on("mouseout", function () {
                // Restore all elements
                node.style("opacity", 1);
                link.style("opacity", 1);
                nodeLabels.style("opacity", 1);
                linkLabels.style("opacity", 1);

                hideTooltip();
            });

        // Update positions on simulation tick
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x || 0)
                .attr("y1", d => d.source.y || 0)
                .attr("x2", d => d.target.x || 0)
                .attr("y2", d => d.target.y || 0);

            node
                .attr("cx", d => d.x || 0)
                .attr("cy", d => d.y || 0);

            nodeLabels
                .attr("x", d => d.x || 0)
                .attr("y", d => d.y || 0);

            linkLabels
                .attr("x", d => {
                    const sx = d.source?.x ?? 0;
                    const tx = d.target?.x ?? 0;
                    return (sx + tx) / 2;
                })
                .attr("y", d => {
                    const sy = d.source?.y ?? 0;
                    const ty = d.target?.y ?? 0;
                    return (sy + ty) / 2;
                });
        });

        // Ensure simulation runs long enough to position nodes
        simulation.on("end", () => {
            console.log('Simulation ended');
        });

        // Stop simulation after 3 seconds
        setTimeout(() => {
            simulation.stop();
        }, 3000);

        // Add animations
        this.animateGraph(graphType);
    }

    getNodeColor(node) {
        if (node.inCycle) return "#ef4444"; // Red for cycle nodes
        if (node.type === 'process') return "#2563eb"; // Blue for processes
        if (node.type === 'resource') return "#10b981"; // Green for resources
        return "#64748b"; // Default gray
    }

    getNodeStrokeColor(node) {
        if (node.inCycle) return "#dc2626"; // Darker red
        return "white";
    }

    getNodeRadius(node) {
        if (node.type === 'resource') return 25;
        return 30;
    }

    getEdgeColor(type) {
        switch (type) {
            case 'allocation': return "#1f2937"; // Dark gray
            case 'request': return "#ef4444"; // Red
            case 'wait-for': return "#64748b"; // Gray
            default: return "#64748b";
        }
    }

    drag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    }

    animateGraph(graphType) {
        // Animate nodes appearing
        this.nodeGroup.selectAll("circle")
            .style("opacity", 0)
            .transition()
            .duration(800)
            .delay((d, i) => i * 100)
            .style("opacity", 1);

        // Animate links appearing
        this.linkGroup.selectAll("line")
            .style("opacity", 0)
            .transition()
            .duration(600)
            .delay((d, i) => i * 50)
            .style("opacity", 1);

        // Animate labels appearing
        this.labelGroup.selectAll("text")
            .style("opacity", 0)
            .transition()
            .duration(400)
            .delay(400)
            .style("opacity", 1);

        // Pulse cycle nodes if present
        if (graphType === 'wfg') {
            this.nodeGroup.selectAll(".node-cycle")
                .transition()
                .duration(1000)
                .delay(1000)
                .style("stroke-width", 5)
                .transition()
                .duration(1000)
                .style("stroke-width", 3);
        }
    }

    zoomIn() {
        this.scale = Math.min(this.scale * 1.2, 4);
        this.svg.transition().duration(300).call(
            this.zoom.transform,
            d3.zoomIdentity.translate(this.translate[0], this.translate[1]).scale(this.scale)
        );
    }

    zoomOut() {
        this.scale = Math.max(this.scale / 1.2, 0.1);
        this.svg.transition().duration(300).call(
            this.zoom.transform,
            d3.zoomIdentity.translate(this.translate[0], this.translate[1]).scale(this.scale)
        );
    }

    resetView() {
        this.scale = 1;
        this.translate = [0, 0];
        this.svg.transition().duration(500).call(
            this.zoom.transform,
            d3.zoomIdentity
        );
    }
}

// Tooltip functions
function showTooltip(event, d) {
    const tooltip = d3.select("body")
        .append("div")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("background", "rgba(0, 0, 0, 0.8)")
        .style("color", "white")
        .style("padding", "8px 12px")
        .style("border-radius", "6px")
        .style("font-size", "12px")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);

    let content = `<strong>${d.name}</strong><br/>`;

    if (d.type === 'process') {
        content += `Process ID: ${d.pid}<br/>`;
        if (d.inCycle) {
            content += `<span style="color: #ef4444;">⚠️ In Deadlock Cycle</span>`;
        }
    } else if (d.type === 'resource') {
        content += `Resource: ${d.rid}<br/>`;
        content += `Total Units: ${d.total}`;
    }

    tooltip.html(content)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 10) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);

    // Store reference for cleanup
    event.target._tooltip = tooltip;
}

function hideTooltip() {
    d3.selectAll(".tooltip").remove();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GraphVisualization;
}
