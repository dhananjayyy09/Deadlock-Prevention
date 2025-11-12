import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List
from .models import SystemSnapshot


class DeadlockAnalytics:
    """
    Track and analyze historical deadlock occurrences.
    Provides insights, trends, and statistics.
    """
    
    def __init__(self, db_path: str = "deadlock_history.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema for storing deadlock history."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deadlock_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                num_processes INTEGER,
                num_resources INTEGER,
                num_cycles INTEGER,
                cycles_json TEXT,
                victims_json TEXT,
                detection_time_ms REAL,
                recovery_applied BOOLEAN
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                has_deadlock BOOLEAN,
                ml_probability REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_contention (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                contention_level REAL,
                processes_involved INTEGER
            )
        ''')
        
        self.conn.commit()
    
    def log_deadlock_event(self, snapshot: SystemSnapshot, cycles: List[set], 
                          victims: List[int], detection_time_ms: float, 
                          recovery_applied: bool = False):
        """
        Log a deadlock detection event to the database.
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO deadlock_events 
            (timestamp, num_processes, num_resources, num_cycles, 
             cycles_json, victims_json, detection_time_ms, recovery_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            len(snapshot.processes),
            len(snapshot.resources),
            len(cycles),
            json.dumps([list(c) for c in cycles]),
            json.dumps(victims),
            detection_time_ms,
            recovery_applied
        ))
        
        self.conn.commit()
    
    def log_snapshot(self, snapshot: SystemSnapshot, has_deadlock: bool, 
                    ml_probability: float = 0.0):
        """
        Log a system snapshot for training ML models.
        """
        cursor = self.conn.cursor()
        
        snapshot_dict = {
            'processes': [{'pid': p.pid, 'name': p.name} for p in snapshot.processes],
            'resources': {rid: {'total': r.total} for rid, r in snapshot.resources.items()},
            'allocation': {f"{pid}_{rid}": alloc for (pid, rid), alloc in snapshot.allocation.items()},
            'request': {f"{pid}_{rid}": req for (pid, rid), req in snapshot.request.items()}
        }
        
        cursor.execute('''
            INSERT INTO system_snapshots 
            (timestamp, snapshot_json, has_deadlock, ml_probability)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            json.dumps(snapshot_dict),
            has_deadlock,
            ml_probability
        ))
        
        self.conn.commit()
    
    def get_deadlock_trends(self, days: int = 7) -> Dict:
        """
        Analyze deadlock trends over specified time period.
        """
        cursor = self.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Total deadlocks
        cursor.execute('''
            SELECT COUNT(*) FROM deadlock_events 
            WHERE timestamp >= ?
        ''', (since,))
        total_deadlocks = cursor.fetchone()[0]
        
        # Average cycles per deadlock
        cursor.execute('''
            SELECT AVG(num_cycles) FROM deadlock_events 
            WHERE timestamp >= ?
        ''', (since,))
        avg_cycles = cursor.fetchone()[0] or 0
        
        # Most common cycle sizes
        cursor.execute('''
            SELECT num_cycles, COUNT(*) as count 
            FROM deadlock_events 
            WHERE timestamp >= ?
            GROUP BY num_cycles 
            ORDER BY count DESC
        ''', (since,))
        cycle_distribution = dict(cursor.fetchall())
        
        # Deadlocks by hour of day
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count 
            FROM deadlock_events 
            WHERE timestamp >= ?
            GROUP BY hour 
            ORDER BY count DESC
        ''', (since,))
        peak_hours = dict(cursor.fetchall())
        
        # Average detection time
        cursor.execute('''
            SELECT AVG(detection_time_ms) FROM deadlock_events 
            WHERE timestamp >= ?
        ''', (since,))
        avg_detection_time = cursor.fetchone()[0] or 0
        
        return {
            'total_deadlocks': total_deadlocks,
            'avg_cycles': round(avg_cycles, 2),
            'cycle_distribution': cycle_distribution,
            'peak_hours': peak_hours,
            'avg_detection_time_ms': round(avg_detection_time, 2)
        }
    
    def get_most_affected_processes(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """
        Find processes most frequently involved in deadlocks.
        """
        cursor = self.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT cycles_json FROM deadlock_events 
            WHERE timestamp >= ?
        ''', (since,))
        
        process_count = {}
        for (cycles_json,) in cursor.fetchall():
            cycles = json.loads(cycles_json)
            for cycle in cycles:
                for pid in cycle:
                    process_count[pid] = process_count.get(pid, 0) + 1
        
        # Sort by count
        sorted_processes = sorted(process_count.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'pid': pid, 'deadlock_count': count} 
            for pid, count in sorted_processes[:limit]
        ]
    
    def get_ml_training_data(self, limit: int = 1000) -> List:
        """
        Retrieve historical snapshots for ML model training.
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT snapshot_json, has_deadlock 
            FROM system_snapshots 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
    
    def export_report(self, days: int = 7) -> str:
        """
        Generate a comprehensive text report of deadlock statistics.
        """
        trends = self.get_deadlock_trends(days)
        affected_processes = self.get_most_affected_processes(days)
        
        report = f"""
=== DEADLOCK ANALYSIS REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {days} days

SUMMARY:
--------
Total Deadlocks: {trends['total_deadlocks']}
Average Cycles per Deadlock: {trends['avg_cycles']}
Average Detection Time: {trends['avg_detection_time_ms']} ms

CYCLE DISTRIBUTION:
------------------
"""
        for size, count in trends['cycle_distribution'].items():
            report += f"  {size} processes: {count} occurrences\n"
        
        report += "\nPEAK HOURS (UTC):\n"
        report += "-----------------\n"
        for hour, count in sorted(trends['peak_hours'].items(), key=lambda x: int(x[0])):
            report += f"  {hour}:00 - {count} deadlocks\n"
        
        report += "\nMOST AFFECTED PROCESSES:\n"
        report += "------------------------\n"
        for proc in affected_processes:
            report += f"  PID {proc['pid']}: {proc['deadlock_count']} deadlocks\n"
        
        return report
    
    def clear_old_data(self, days: int = 30):
        """
        Delete data older than specified days to manage database size.
        """
        cursor = self.conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('DELETE FROM deadlock_events WHERE timestamp < ?', (cutoff,))
        cursor.execute('DELETE FROM system_snapshots WHERE timestamp < ?', (cutoff,))
        cursor.execute('DELETE FROM resource_contention WHERE timestamp < ?', (cutoff,))
        
        self.conn.commit()
        print(f"Deleted data older than {days} days")
    
    def close(self):
        """Close database connection."""
        self.conn.close()
