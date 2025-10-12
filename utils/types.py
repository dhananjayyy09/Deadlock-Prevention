from __future__ import annotations

from enum import Enum


class RecoveryPolicy(str, Enum):
	MIN_IMPACT = "min_impact"
