from typing import Dict, Tuple, List
from .models import SystemSnapshot


class BankersAlgorithm:
    """
    Complete Banker's Algorithm implementation for deadlock avoidance.
    Determines if system is in safe state and finds safe execution sequences.
    """
    
    def is_safe(self, snapshot: SystemSnapshot) -> Tuple[bool, List[int], Dict[str, int]]:
        """
        Check if system is in safe state using Banker's algorithm.
        
        Returns:
            Tuple of (is_safe, safe_sequence, final_available)
            - is_safe: True if safe state exists
            - safe_sequence: List of process IDs in safe execution order
            - final_available: Available resources after all processes complete
        """
        # Calculate initial available resources
        available: Dict[str, int] = {rid: res.total for rid, res in snapshot.resources.items()}
        for (pid, rid), alloc in snapshot.allocation.items():
            available[rid] = available.get(rid, 0) - alloc
        
        # Track finished processes and safe sequence
        finished: Dict[int, bool] = {p.pid: False for p in snapshot.processes}
        safe_sequence: List[int] = []
        work = available.copy()
        
        # Keep trying to find processes that can finish
        made_progress = True
        while made_progress:
            made_progress = False
            
            for process in snapshot.processes:
                if finished[process.pid]:
                    continue
                
                # Calculate remaining need for this process
                needs: Dict[str, int] = {}
                for rid in snapshot.resources.keys():
                    current_alloc = snapshot.allocation.get((process.pid, rid), 0)
                    request = snapshot.request.get((process.pid, rid), 0)
                    # Need = what process still needs to complete
                    needs[rid] = request
                
                # Check if needs can be satisfied with available resources
                can_finish = all(work.get(rid, 0) >= need for rid, need in needs.items())
                
                if can_finish:
                    # Simulate process finishing: release its allocated resources
                    for rid in snapshot.resources.keys():
                        alloc = snapshot.allocation.get((process.pid, rid), 0)
                        work[rid] = work.get(rid, 0) + alloc
                    
                    finished[process.pid] = True
                    safe_sequence.append(process.pid)
                    made_progress = True
                    break
        
        is_safe = all(finished.values())
        return is_safe, safe_sequence if is_safe else [], work
    
    def find_all_safe_sequences(self, snapshot: SystemSnapshot) -> List[List[int]]:
        """
        Find all possible safe sequences using backtracking.
        Useful for showing alternative execution orders.
        """
        all_sequences = []
        
        def backtrack(available: Dict[str, int], finished: Dict[int, bool], sequence: List[int]):
            # Base case: all processes finished
            if all(finished.values()):
                all_sequences.append(sequence.copy())
                return
            
            # Try each unfinished process
            for process in snapshot.processes:
                if finished[process.pid]:
                    continue
                
                # Calculate needs
                needs = {}
                for rid in snapshot.resources.keys():
                    needs[rid] = snapshot.request.get((process.pid, rid), 0)
                
                # Check if can finish
                if all(available.get(rid, 0) >= need for rid, need in needs.items()):
                    # Make move
                    new_available = available.copy()
                    for rid in snapshot.resources.keys():
                        alloc = snapshot.allocation.get((process.pid, rid), 0)
                        new_available[rid] = new_available.get(rid, 0) + alloc
                    
                    finished[process.pid] = True
                    sequence.append(process.pid)
                    
                    # Recurse
                    backtrack(new_available, finished, sequence)
                    
                    # Undo move
                    finished[process.pid] = False
                    sequence.pop()
        
        # Start backtracking
        initial_available = {rid: res.total for rid, res in snapshot.resources.items()}
        for (pid, rid), alloc in snapshot.allocation.items():
            initial_available[rid] -= alloc
        
        initial_finished = {p.pid: False for p in snapshot.processes}
        backtrack(initial_available, initial_finished, [])
        
        return all_sequences
    
    def compute_need(self, snapshot: SystemSnapshot) -> Dict[Tuple[int, str], int]:
        """
        Compute need matrix: Need[i,j] = Max[i,j] - Allocation[i,j]
        For simplicity, we use request as proxy for remaining need.
        """
        return dict(snapshot.request)
    
    def analyze_resource_utilization(self, snapshot: SystemSnapshot) -> Dict[str, float]:
        """
        Calculate resource utilization percentages.
        """
        utilization = {}
        for rid, resource in snapshot.resources.items():
            allocated = sum(
                alloc for (pid, r), alloc in snapshot.allocation.items() 
                if r == rid
            )
            utilization[rid] = (allocated / resource.total * 100) if resource.total > 0 else 0
        return utilization
