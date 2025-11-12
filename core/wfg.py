from typing import Dict, Set, List
from .models import WaitForGraph


class WFGDetector:
    """
    Wait-For Graph cycle detection using multiple algorithms.
    Supports DFS-based detection and Tarjan's SCC algorithm.
    """
    
    def find_cycles(self, wfg: WaitForGraph) -> List[Set[int]]:
        """
        Find all cycles in wait-for graph using DFS.
        """
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
    
    def find_cycles_tarjan(self, wfg: WaitForGraph) -> List[Set[int]]:
        """
        Find strongly connected components (cycles) using Tarjan's algorithm.
        More efficient for large graphs: O(V + E) time complexity.
        """
        graph = wfg.edges
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = set()
        sccs = []

        def strongconnect(node):
            # Set the depth index for node
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack.add(node)

            # Consider successors of node
            for successor in graph.get(node, set()):
                if successor not in index:
                    # Successor has not yet been visited; recurse on it
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif successor in on_stack:
                    # Successor is in stack and hence in the current SCC
                    lowlinks[node] = min(lowlinks[node], index[successor])

            # If node is a root node, pop the stack and generate an SCC
            if lowlinks[node] == index[node]:
                connected_component = set()
                while True:
                    successor = stack.pop()
                    on_stack.remove(successor)
                    connected_component.add(successor)
                    if successor == node:
                        break
                # Only add cycles (SCCs with more than one node)
                if len(connected_component) > 1:
                    sccs.append(connected_component)

        for node in graph.keys():
            if node not in index:
                strongconnect(node)

        return sccs
    
    def detect_by_timeout(self, wfg: WaitForGraph, timeout_threshold: int = 5000) -> List[int]:
        """
        Detect processes that have been waiting beyond timeout threshold.
        Returns list of potentially deadlocked process IDs.
        
        Args:
            wfg: Wait-for graph
            timeout_threshold: Time in milliseconds
        
        Note: In real implementation, would track actual wait times.
        """
        # For demo, return processes with high out-degree (waiting for many others)
        stuck_processes = []
        for pid, waiting_for in wfg.edges.items():
            if len(waiting_for) >= 2:  # Waiting for 2+ processes
                stuck_processes.append(pid)
        return stuck_processes
    
    def analyze_wait_chains(self, wfg: WaitForGraph) -> Dict[int, List[List[int]]]:
        """
        Find all wait chains for each process.
        A wait chain shows the dependency path: P1 -> P2 -> P3 -> ...
        """
        chains = {}
        
        def find_chains(start_pid: int, current_pid: int, path: List[int], visited: Set[int]):
            if current_pid in visited:
                # Found a cycle
                return [[*path, current_pid]]
            
            visited_copy = visited.copy()
            visited_copy.add(current_pid)
            
            waiting_for = wfg.edges.get(current_pid, set())
            if not waiting_for:
                # End of chain
                return [path]
            
            all_chains = []
            for next_pid in waiting_for:
                sub_chains = find_chains(start_pid, next_pid, path + [next_pid], visited_copy)
                all_chains.extend(sub_chains)
            
            return all_chains
        
        for pid in wfg.edges.keys():
            chains[pid] = find_chains(pid, pid, [pid], set())
        
        return chains
