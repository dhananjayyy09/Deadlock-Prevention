"""
Deadlock Simulator - Creates classic deadlock scenarios
Perfect for teaching and demonstration purposes
"""

from typing import List, Dict, Tuple
from .models import SystemSnapshot, Process, Resource


class DeadlockSimulator:
    """
    Generates well-known deadlock scenarios for educational purposes.
    Each scenario demonstrates different deadlock conditions.
    """
    
    def create_dining_philosophers(self, n: int = 5) -> SystemSnapshot:
        """
        Simulate the classic Dining Philosophers Problem.
        
        N philosophers sit at a round table with N chopsticks (forks).
        Each philosopher needs 2 chopsticks to eat.
        Creates a circular wait condition.
        
        Args:
            n: Number of philosophers (default 5)
        
        Returns:
            SystemSnapshot with circular wait deadlock
        """
        processes = []
        resources = {}
        allocation = {}
        request = {}
        
        # Create N philosophers (processes) and N chopsticks (resources)
        for i in range(n):
            processes.append(Process(pid=i, name=f"Philosopher_{i}"))
            rid = f"F{i}"  # Fork/Chopstick ID (short format)
            resources[rid] = Resource(rid=rid, total=1)
        
        # Each philosopher holds their left chopstick and requests the right one
        for i in range(n):
            left_fork = f"F{i}"
            right_fork = f"F{(i + 1) % n}"  # Circular
            
            # Philosopher holds left fork
            allocation[(i, left_fork)] = 1
            
            # Philosopher requests right fork
            request[(i, right_fork)] = 1
        
        return SystemSnapshot(
            processes=processes,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def create_reader_writer_deadlock(self) -> SystemSnapshot:
        """
        Simulate Reader-Writer deadlock.
        
        Scenario:
        - Reader holds read lock on DB1, wants write lock on DB2
        - Writer holds write lock on DB2, wants read lock on DB1
        
        Returns:
            SystemSnapshot with reader-writer deadlock
        """
        processes = [
            Process(pid=1, name="Reader"),
            Process(pid=2, name="Writer")
        ]
        
        resources = {
            "DB1": Resource(rid="DB1", total=2),  # Allows multiple readers
            "DB2": Resource(rid="DB2", total=2)
        }
        
        allocation = {
            (1, "DB1"): 1,  # Reader has read lock on DB1
            (2, "DB2"): 2   # Writer has exclusive lock on DB2
        }
        
        request = {
            (1, "DB2"): 2,  # Reader wants write lock on DB2
            (2, "DB1"): 1   # Writer wants read lock on DB1
        }
        
        return SystemSnapshot(
            processes=processes,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def create_circular_wait(self, processes_count: int = 4) -> SystemSnapshot:
        """
        Generate simple circular wait pattern.
        
        Pattern: P0 → R0 → P1 → R1 → P2 → R2 → P3 → R3 → P0
        
        Args:
            processes_count: Number of processes (default 4)
        
        Returns:
            SystemSnapshot with circular wait deadlock
        """
        process_list = []
        resources = {}
        allocation = {}
        request = {}
        
        # Create processes and resources
        for i in range(processes_count):
            process_list.append(Process(pid=i, name=f"P{i}"))
            rid = f"R{i}"
            resources[rid] = Resource(rid=rid, total=1)
        
        # Create circular wait: each process holds one resource and requests the next
        for i in range(processes_count):
            current_resource = f"R{i}"
            next_resource = f"R{(i + 1) % processes_count}"
            
            # Process i holds current resource
            allocation[(i, current_resource)] = 1
            
            # Process i requests next resource (creating circular dependency)
            request[(i, next_resource)] = 1
        
        return SystemSnapshot(
            processes=process_list,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def create_banker_unsafe(self) -> SystemSnapshot:
        """
        Create a scenario that is unsafe according to Banker's Algorithm.
        System can potentially deadlock but hasn't yet.
        
        Returns:
            SystemSnapshot that is unsafe (no safe sequence exists)
        """
        processes = [
            Process(pid=0, name="P0"),
            Process(pid=1, name="P1"),
            Process(pid=2, name="P2")
        ]
        
        resources = {
            "R1": Resource(rid="R1", total=3),
            "R2": Resource(rid="R2", total=2)
        }
        
        # Allocation that leaves system unsafe
        allocation = {
            (0, "R1"): 2,
            (0, "R2"): 0,
            (1, "R1"): 1,
            (1, "R2"): 1,
            (2, "R1"): 0,
            (2, "R2"): 1
        }
        
        # Requests that cannot all be satisfied
        request = {
            (0, "R1"): 1,
            (0, "R2"): 2,
            (1, "R1"): 2,
            (1, "R2"): 1,
            (2, "R1"): 3,
            (2, "R2"): 1
        }
        
        return SystemSnapshot(
            processes=processes,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def create_no_deadlock(self) -> SystemSnapshot:
        """
        Create a safe scenario with no deadlock.
        Perfect for comparing with deadlock scenarios.
        
        Returns:
            SystemSnapshot that is safe (has safe sequence)
        """
        processes = [
            Process(pid=0, name="P0"),
            Process(pid=1, name="P1"),
            Process(pid=2, name="P2")
        ]
        
        resources = {
            "R1": Resource(rid="R1", total=5),
            "R2": Resource(rid="R2", total=3)
        }
        
        # Safe allocation
        allocation = {
            (0, "R1"): 1,
            (0, "R2"): 0,
            (1, "R1"): 1,
            (1, "R2"): 1,
            (2, "R1"): 1,
            (2, "R2"): 1
        }
        
        # Requests that can be satisfied
        request = {
            (0, "R1"): 1,
            (0, "R2"): 1,
            (1, "R1"): 1,
            (1, "R2"): 0,
            (2, "R1"): 0,
            (2, "R2"): 1
        }
        
        return SystemSnapshot(
            processes=processes,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def create_producer_consumer_deadlock(self) -> SystemSnapshot:
        """
        Producer-Consumer deadlock scenario.
        
        Producer holds buffer, needs semaphore.
        Consumer holds semaphore, needs buffer.
        
        Returns:
            SystemSnapshot with producer-consumer deadlock
        """
        processes = [
            Process(pid=1, name="Producer"),
            Process(pid=2, name="Consumer")
        ]
        
        resources = {
            "Buffer": Resource(rid="Buffer", total=1),
            "Sem": Resource(rid="Sem", total=1)
        }
        
        allocation = {
            (1, "Buffer"): 1,   # Producer holds buffer
            (2, "Sem"): 1       # Consumer holds semaphore
        }
        
        request = {
            (1, "Sem"): 1,      # Producer needs semaphore
            (2, "Buffer"): 1    # Consumer needs buffer
        }
        
        return SystemSnapshot(
            processes=processes,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def get_all_scenarios(self) -> Dict[str, SystemSnapshot]:
        """
        Get all available simulation scenarios.
        
        Returns:
            Dictionary of scenario_name -> SystemSnapshot
        """
        return {
            "dining_philosophers": self.create_dining_philosophers(),
            "reader_writer": self.create_reader_writer_deadlock(),
            "circular_wait": self.create_circular_wait(),
            "banker_unsafe": self.create_banker_unsafe(),
            "no_deadlock": self.create_no_deadlock(),
            "producer_consumer": self.create_producer_consumer_deadlock()
        }
    
    def get_scenario_info(self) -> Dict[str, Dict[str, str]]:
        """
        Get human-readable information about each scenario.
        
        Returns:
            Dictionary with scenario descriptions
        """
        return {
            "dining_philosophers": {
                "name": "Dining Philosophers",
                "description": "Classic circular wait with 5 philosophers and forks",
                "type": "Circular Wait",
                "difficulty": "Easy",
                "icon": "🍴"
            },
            "reader_writer": {
                "name": "Reader-Writer Deadlock",
                "description": "Reader and writer processes competing for database locks",
                "type": "Hold and Wait",
                "difficulty": "Medium",
                "icon": "📖"
            },
            "circular_wait": {
                "name": "Circular Wait (4 Processes)",
                "description": "Simple circular dependency: P0→R0→P1→R1→P2→R2→P3→R3→P0",
                "type": "Circular Wait",
                "difficulty": "Easy",
                "icon": "🔄"
            },
            "banker_unsafe": {
                "name": "Banker's Unsafe State",
                "description": "System in unsafe state - no safe sequence exists",
                "type": "Unsafe State",
                "difficulty": "Hard",
                "icon": "⚠️"
            },
            "no_deadlock": {
                "name": "Safe State (No Deadlock)",
                "description": "Safe system with available safe sequence",
                "type": "Safe",
                "difficulty": "Easy",
                "icon": "✅"
            },
            "producer_consumer": {
                "name": "Producer-Consumer Deadlock",
                "description": "Producer and consumer with conflicting lock order",
                "type": "Hold and Wait",
                "difficulty": "Medium",
                "icon": "🏭"
            }
        }
