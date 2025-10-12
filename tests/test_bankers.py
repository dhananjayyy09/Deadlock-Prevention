from deadlock_tool.core.bankers import BankersAlgorithm
from deadlock_tool.core.models import SystemSnapshot, Process, Resource


def test_bankers_safe_minimal():
	banker = BankersAlgorithm()
	p = Process(pid=1, name="P1")
	res = {"R": Resource(rid="R", total=1)}
	alloc = {(1, "R"): 0}
	req = {(1, "R"): 0}
	snap = SystemSnapshot([p], res, alloc, req)
	assert banker.is_safe(snap)
