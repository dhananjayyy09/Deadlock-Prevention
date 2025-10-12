from deadlock_tool.core.recovery import RecoveryManager


def test_recovery_choose_victims_empty():
	mgr = RecoveryManager()
	assert mgr.choose_victims([]) == []
