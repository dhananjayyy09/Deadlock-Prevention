from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


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
	allocation: Dict[Tuple[int, str], int]  # (pid, rid) -> allocated units
	request: Dict[Tuple[int, str], int]     # (pid, rid) -> requested units


class WaitForGraph:
	def __init__(self, edges: Dict[int, Set[int]]):
		self.edges = edges
