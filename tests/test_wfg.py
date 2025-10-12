from deadlock_tool.core.wfg import WFGDetector
from deadlock_tool.core.models import WaitForGraph


def test_wfg_no_cycle():
	det = WFGDetector()
	wfg = WaitForGraph({1: {2}, 2: set()})
	assert det.find_cycles(wfg) == []
