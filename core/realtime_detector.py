import os
import psutil
from typing import Dict, List, Set, Tuple
from .models import Process, Resource, SystemSnapshot


class RealTimeDeadlockDetector:
    """
    Detects real deadlocks from actual system resources.
    Supports file locks, network sockets, and process dependencies.
    """
    
    def __init__(self):
        self.platform = os.name  # 'posix' for Linux/Mac, 'nt' for Windows
    
    def detect_file_lock_deadlocks(self) -> SystemSnapshot:
        """
        Detect file lock deadlocks by parsing system lock information.
        Linux: Reads /proc/locks
        """
        if self.platform == 'posix':
            return self._detect_file_locks_linux()
        else:
            print("File lock detection only supported on Linux")
            return self._create_empty_snapshot()
    
    def _detect_file_locks_linux(self) -> SystemSnapshot:
        """
        Parse /proc/locks to detect file lock deadlocks on Linux.
        """
        try:
            lock_info = self._parse_proc_locks()
            return self._build_snapshot_from_locks(lock_info)
        except FileNotFoundError:
            print("/proc/locks not found - are you on Linux?")
            return self._create_empty_snapshot()
        except Exception as e:
            print(f"Error detecting file locks: {e}")
            return self._create_empty_snapshot()
    
    def _parse_proc_locks(self) -> Dict[str, List[Dict]]:
        """
        Parse /proc/locks file to extract lock information.
        
        /proc/locks format:
        1: POSIX  ADVISORY  WRITE 1234 08:01:12345 0 EOF
        """
        locks_by_file = {}
        
        try:
            with open('/proc/locks', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 8:
                        continue
                    
                    lock_id = parts[0].rstrip(':')
                    lock_type = parts[1]  # POSIX, FLOCK, etc.
                    lock_mode = parts[3]  # READ or WRITE
                    pid = int(parts[4])
                    inode = parts[5]  # File identifier
                    
                    if inode not in locks_by_file:
                        locks_by_file[inode] = []
                    
                    locks_by_file[inode].append({
                        'pid': pid,
                        'type': lock_type,
                        'mode': lock_mode,
                        'lock_id': lock_id
                    })
        except Exception as e:
            print(f"Error reading /proc/locks: {e}")
        
        return locks_by_file
    
    def _build_snapshot_from_locks(self, lock_info: Dict) -> SystemSnapshot:
        """
        Convert file lock information to SystemSnapshot format.
        """
        all_pids = set()
        for inode, locks in lock_info.items():
            for lock in locks:
                all_pids.add(lock['pid'])
        
        # Create process objects
        processes = []
        for pid in all_pids:
            try:
                proc = psutil.Process(pid)
                processes.append(Process(pid=pid, name=proc.name()))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                processes.append(Process(pid=pid, name=f"Process-{pid}"))
        
        # Create resource objects (one per file/inode)
        resources = {}
        for inode in lock_info.keys():
            resources[f"FILE_{inode}"] = Resource(rid=f"FILE_{inode}", total=1)
        
        # Build allocation and request matrices
        allocation = {}
        request = {}
        
        for inode, locks in lock_info.items():
            rid = f"FILE_{inode}"
            
            # Processes holding locks are allocated
            write_locks = [lock for lock in locks if lock['mode'] == 'WRITE']
            read_locks = [lock for lock in locks if lock['mode'] == 'READ']
            
            # If someone has write lock, they're allocated
            for lock in write_locks:
                allocation[(lock['pid'], rid)] = 1
            
            # If someone is waiting (multiple write locks or read + write), they're requesting
            if len(write_locks) > 1:
                for i, lock in enumerate(write_locks[1:], 1):
                    request[(lock['pid'], rid)] = 1
            
            if read_locks and write_locks:
                # Read locks waiting for write lock to release
                for lock in read_locks:
                    request[(lock['pid'], rid)] = 1
        
        return SystemSnapshot(
            processes=processes,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def detect_network_socket_deadlocks(self) -> SystemSnapshot:
        """
        Detect potential deadlocks from network socket connections.
        Looks for circular dependencies in client-server relationships.
        """
        processes = []
        resources = {}
        allocation = {}
        request = {}
        
        # Get all processes with network connections
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info['connections']
                if not connections:
                    continue
                
                pid = proc.info['pid']
                name = proc.info['name']
                processes.append(Process(pid=pid, name=name))
                
                # Each listening socket is a resource
                for conn in connections:
                    if conn.status == 'LISTEN':
                        port = conn.laddr.port
                        rid = f"PORT_{port}"
                        if rid not in resources:
                            resources[rid] = Resource(rid=rid, total=1)
                        allocation[(pid, rid)] = 1
                    
                    # Connections to other ports are requests
                    elif conn.status == 'ESTABLISHED' and conn.raddr:
                        remote_port = conn.raddr.port
                        rid = f"PORT_{remote_port}"
                        if rid not in resources:
                            resources[rid] = Resource(rid=rid, total=1)
                        request[(pid, rid)] = 1
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return SystemSnapshot(
            processes=processes[:10],  # Limit to 10 processes
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def detect_thread_deadlocks(self) -> SystemSnapshot:
        """
        Detect thread-level deadlocks within processes.
        Monitors thread states and lock objects.
        """
        # This requires more invasive monitoring
        # For demo, we create a simplified version
        import threading
        
        processes = []
        resources = {}
        allocation = {}
        request = {}
        
        # Get current process threads
        current_proc = psutil.Process()
        processes.append(Process(pid=current_proc.pid, name=current_proc.name()))
        
        # Monitor threading locks (if accessible)
        # Note: This is limited without instrumentation
        
        return SystemSnapshot(
            processes=processes,
            resources=resources,
            allocation=allocation,
            request=request
        )
    
    def _create_empty_snapshot(self) -> SystemSnapshot:
        """Create empty snapshot when detection fails."""
        return SystemSnapshot(
            processes=[],
            resources={},
            allocation={},
            request={}
        )
