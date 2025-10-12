from typing import Dict, Set, List
from .models import WaitForGraph


class WFGDetector:
	def find_cycles(self, wfg: WaitForGraph) -> List[Set[int]]:
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
					# Found a cycle; collect nodes from nbr to end
					if nbr in path:
						idx = path.index(nbr)
						cycles.append(set(path[idx:]))
			stack.remove(node)

		for n in list(graph.keys()):
			if n not in visited:
				dfs(n, [n])
		return cycles
