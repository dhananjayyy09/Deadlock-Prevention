from typing import Dict, Tuple
from core.models import Process, Resource, SystemSnapshot


class Normalizer:
	"""Map psutil-derived data into a minimal internal SystemSnapshot.

	For demonstration, creates a single generic resource and random small
	allocations/requests to visualize. Replace with real mapping as needed.
	"""

	def to_snapshot(self, ps_data: Dict) -> SystemSnapshot:
		processes = [Process(pid=p["pid"], name=p.get("name", f"P{p['pid']}")) for p in ps_data.get("processes", [])][:5]
		resources = {"R": Resource(rid="R", total=5)}
		allocation: Dict[Tuple[int, str], int] = {}
		request: Dict[Tuple[int, str], int] = {}
		for i, p in enumerate(processes):
			allocation[(p.pid, "R")] = 1 if i % 2 == 0 else 0
			request[(p.pid, "R")] = 1 if i % 3 == 0 else 0
		return SystemSnapshot(processes=processes, resources=resources, allocation=allocation, request=request)
