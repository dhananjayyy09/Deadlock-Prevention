#!/usr/bin/env python3
"""
Simplified Flask web server for Deadlock Detection Tool
Standalone version with embedded classes to avoid import issues
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import psutil
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass

app = Flask(__name__)
CORS(app)

# Embedded models to avoid import issues
@dataclass(frozen=True)
class Process:
    pid: int
    name: str

@dataclass(frozen=True)
class Resource:
    rid: str
    total: int

@dataclass
class SystemSnapshot:
    processes: List[Process]
    resources: Dict[str, Resource]
    allocation: Dict[Tuple[int, str], int]
    request: Dict[Tuple[int, str], int]

class WaitForGraph:
    def __init__(self, edges: Dict[int, Set[int]]):
        self.edges = edges

# Embedded algorithms
class BankersAlgorithm:
    def is_safe(self, snapshot: SystemSnapshot) -> bool:
        """Simplified Banker's algorithm implementation"""
        # For demo purposes, return True if no requests are made
        return all(count == 0 for count in snapshot.request.values())

class WFGDetector:
    def find_cycles(self, wfg: WaitForGraph) -> List[Set[int]]:
        """Find cycles in wait-for graph using DFS"""
        graph = wfg.edges
        visited: Set[int] = set()
        stack: Set[int] = set()
        cycles: List[Set[int]] = []

        def dfs(node: int, path: List[int]) -> None:
            visited.add(node)
            stack.add(node)
            for nbr in graph.get(node, set()):
                if nbr not in visited:
                    dfs(nbr, path + [nbr])
                elif nbr in stack:
                    # Found a cycle
                    if nbr in path:
                        idx = path.index(nbr)
                        cycles.append(set(path[idx:]))
            stack.remove(node)

        for n in list(graph.keys()):
            if n not in visited:
                dfs(n, [n])
        return cycles

class RecoveryManager:
    def choose_victims(self, cycles: List[Set[int]]) -> Set[int]:
        """Choose victims for recovery - pick one process from each cycle"""
        victims = set()
        for cycle in cycles:
            if cycle:
                victims.add(list(cycle)[0])  # Pick first process in cycle
        return victims
    
    def apply_preemption(self, snapshot: SystemSnapshot, victims: Set[int]) -> SystemSnapshot:
        """Apply preemption by removing allocations of victim processes"""
        new_allocation = dict(snapshot.allocation)
        new_request = dict(snapshot.request)
        
        for victim in victims:
            # Remove all allocations and requests for victim processes
            keys_to_remove = []
            for key in new_allocation:
                if key[0] == victim:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del new_allocation[key]
                
            keys_to_remove = []
            for key in new_request:
                if key[0] == victim:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del new_request[key]
        
        return SystemSnapshot(
            processes=snapshot.processes,
            resources=snapshot.resources,
            allocation=new_allocation,
            request=new_request
        )

class PsutilReader:
    def snapshot(self) -> Dict:
        """Get system process information"""
        processes = []
        for proc in list(psutil.process_iter(['pid', 'name']))[:10]:  # Limit to 10 processes
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'] or f"Process-{proc.info['pid']}"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"processes": processes}

class Normalizer:
    def to_snapshot(self, ps_data: Dict) -> SystemSnapshot:
        """Convert psutil data to SystemSnapshot"""
        processes = [Process(pid=p["pid"], name=p.get("name", f"P{p['pid']}")) 
                    for p in ps_data.get("processes", [])][:5]
        resources = {"R": Resource(rid="R", total=5)}
        allocation: Dict[Tuple[int, str], int] = {}
        request: Dict[Tuple[int, str], int] = {}
        
        for i, p in enumerate(processes):
            allocation[(p.pid, "R")] = 1 if i % 2 == 0 else 0
            request[(p.pid, "R")] = 1 if i % 3 == 0 else 0
            
        return SystemSnapshot(processes=processes, resources=resources, 
                            allocation=allocation, request=request)

# Initialize components
bankers = BankersAlgorithm()
wfg_detector = WFGDetector()
recovery = RecoveryManager()
reader = PsutilReader()
normalizer = Normalizer()

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/demo-snapshot', methods=['GET'])
def get_demo_snapshot():
    """Get a demo system snapshot"""
    p0 = Process(pid=1, name="P0")
    p1 = Process(pid=2, name="P1")
    p2 = Process(pid=3, name="P2")
    resources = {
        "R1": Resource(rid="R1", total=3),
        "R2": Resource(rid="R2", total=2)
    }
    allocation = {
        (1, "R1"): 1, 
        (2, "R1"): 1,
        (2, "R2"): 1,
        (3, "R2"): 1
    }
    request_dict = {
        (1, "R2"): 1, 
        (2, "R1"): 1,
        (3, "R1"): 1
    }
    
    snapshot = SystemSnapshot(
        processes=[p0, p1, p2], 
        resources=resources, 
        allocation=allocation, 
        request=request_dict
    )
    
    return jsonify(snapshot_to_dict(snapshot))

@app.route('/api/system-snapshot', methods=['GET'])
def get_system_snapshot():
    """Get live system snapshot using psutil"""
    try:
        data = reader.snapshot()
        snapshot = normalizer.to_snapshot(data)
        return jsonify(snapshot_to_dict(snapshot))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict_deadlock():
    """Run Banker's algorithm prediction"""
    try:
        snapshot_data = request.json
        snapshot = dict_to_snapshot(snapshot_data)
        safe = bankers.is_safe(snapshot)
        
        return jsonify({
            "safe": safe,
            "message": "SAFE" if safe else "UNSAFE",
            "details": "System is in a safe state" if safe else "System may lead to deadlock"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/detect', methods=['POST'])
def detect_deadlock():
    """Run WFG cycle detection"""
    try:
        snapshot_data = request.json
        snapshot = dict_to_snapshot(snapshot_data)
        wfg = build_wfg(snapshot)
        cycles = wfg_detector.find_cycles(wfg)
        
        return jsonify({
            "cycles": [list(cycle) for cycle in cycles],
            "has_deadlock": len(cycles) > 0,
            "message": "No cycles detected" if not cycles else f"Found {len(cycles)} cycle(s)",
            "wfg": wfg_to_dict(wfg)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recover', methods=['POST'])
def recover_deadlock():
    """Apply recovery strategies"""
    try:
        snapshot_data = request.json
        snapshot = dict_to_snapshot(snapshot_data)
        wfg = build_wfg(snapshot)
        cycles = wfg_detector.find_cycles(wfg)
        victims = recovery.choose_victims(cycles)
        new_snapshot = recovery.apply_preemption(snapshot, victims)
        
        return jsonify({
            "victims": list(victims) if victims else [],
            "message": f"Preempted processes: {list(victims)}" if victims else "No recovery needed",
            "new_snapshot": snapshot_to_dict(new_snapshot)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def build_wfg(snapshot: SystemSnapshot) -> WaitForGraph:
    """Build wait-for graph from system snapshot"""
    edges = {}
    for (pid_r, rid), need in snapshot.request.items():
        if need <= 0:
            continue
        blockers = [pid for (pid, r), alloc in snapshot.allocation.items() 
                   if r == rid and alloc > 0 and pid != pid_r]
        if blockers:
            edges.setdefault(pid_r, set()).update(blockers)
    return WaitForGraph(edges)

def snapshot_to_dict(snapshot: SystemSnapshot) -> Dict[str, Any]:
    """Convert SystemSnapshot to dictionary for JSON serialization"""
    return {
        "processes": [{"pid": p.pid, "name": p.name} for p in snapshot.processes],
        "resources": {rid: {"rid": r.rid, "total": r.total} for rid, r in snapshot.resources.items()},
        "allocation": {f"{pid}_{rid}": count for (pid, rid), count in snapshot.allocation.items()},
        "request": {f"{pid}_{rid}": count for (pid, rid), count in snapshot.request.items()}
    }

def dict_to_snapshot(data: Dict[str, Any]) -> SystemSnapshot:
    """Convert dictionary to SystemSnapshot"""
    processes = [Process(pid=p["pid"], name=p["name"]) for p in data["processes"]]
    resources = {rid: Resource(rid=r["rid"], total=r["total"]) for rid, r in data["resources"].items()}
    
    allocation = {}
    for key, count in data["allocation"].items():
        pid_str, rid = key.split("_", 1)
        allocation[(int(pid_str), rid)] = count
    
    request_dict = {}
    for key, count in data["request"].items():
        pid_str, rid = key.split("_", 1)
        request_dict[(int(pid_str), rid)] = count
    
    return SystemSnapshot(processes, resources, allocation, request_dict)

def wfg_to_dict(wfg: WaitForGraph) -> Dict[str, List[int]]:
    """Convert WaitForGraph to dictionary for JSON serialization"""
    return {str(pid): list(nbrs) for pid, nbrs in wfg.edges.items()}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
