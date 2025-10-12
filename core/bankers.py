from typing import Dict, Tuple, List
from .models import SystemSnapshot


class BankersAlgorithm:
	def is_safe(self, snapshot: SystemSnapshot) -> bool:
		available: Dict[str, int] = {rid: res.total for rid, res in snapshot.resources.items()}
		for (pid, rid), alloc in snapshot.allocation.items():
			available[rid] = available.get(rid, 0) - alloc

		finished: Dict[int, bool] = {p.pid: False for p in snapshot.processes}
		made_progress = True
		while made_progress:
			made_progress = False
			for p in snapshot.processes:
				if finished[p.pid]:
					continue
				# Need approximated by current request vector
				needs: Dict[str, int] = {}
				for rid in snapshot.resources.keys():
					needs[rid] = snapshot.request.get((p.pid, rid), 0)

				if all(available.get(rid, 0) >= need for rid, need in needs.items()):
					# Pretend p finishes: release its allocation
					for (pid, rid), alloc in list(snapshot.allocation.items()):
						if pid == p.pid and alloc > 0:
							available[rid] = available.get(rid, 0) + alloc
					finished[p.pid] = True
					made_progress = True
					break

		return all(finished.values())

	def compute_need(self, snapshot: SystemSnapshot) -> Dict[Tuple[int, str], int]:
		# Using request as a proxy for remaining need in this minimal model
		return dict(snapshot.request)
