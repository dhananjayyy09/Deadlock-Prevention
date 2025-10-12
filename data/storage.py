from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class Storage:
	"""Simple JSON storage for recovery checkpoints and states."""

	def __init__(self, path: Path | None = None) -> None:
		self.path = path or Path.home() / ".deadlock_tool_state.json"

	def save_state(self, state: Dict[str, Any]) -> None:
		self.path.write_text(json.dumps(state, indent=2))

	def load_state(self) -> Dict[str, Any]:
		if not self.path.exists():
			return {}
		return json.loads(self.path.read_text())
