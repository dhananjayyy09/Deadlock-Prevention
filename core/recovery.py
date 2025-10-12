from typing import List, Set, Dict, Tuple
from .models import SystemSnapshot


class RecoveryManager:
	def choose_victims(self, cycles: List[Set[int]], policy: str = "min_impact") -> List[int]:
		victims: List[int] = []
		seen: Set[int] = set()
		for cycle in cycles:
			if not cycle:
				continue
			# Choose arbitrary minimal pid for determinism
			cand = min(cycle)
			if cand not in seen:
				victims.append(cand)
				seen.add(cand)
		return victims

	def apply_preemption(self, snapshot: SystemSnapshot, victims: List[int]) -> SystemSnapshot:
		if not victims:
			return snapshot
		# Release all allocations of victims
		for (pid, rid), alloc in list(snapshot.allocation.items()):
			if pid in victims and alloc > 0:
				snapshot.allocation[(pid, rid)] = 0
				# Convert remaining need to zero to simulate termination
		for pid in victims:
			for (p, rid), req in list(snapshot.request.items()):
				if p == pid:
					snapshot.request[(p, rid)] = 0
		return snapshot
