from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
	import yaml  # type: ignore
except Exception:  # pragma: no cover
	yaml = None


class ConfigManager:
	"""Load/save configs in JSON or YAML, with a small default set of policies."""

	def __init__(self, path: Optional[Path] = None) -> None:
		self.path = path or Path.home() / ".deadlock_tool_config.yaml"
		self.data: Dict[str, Any] = {
			"banker": {"enabled": True},
			"wfg": {"enabled": True},
			"recovery": {"policy": "min_impact"},
		}
		self.load()

	def load(self) -> None:
		if not self.path.exists():
			return
		if self.path.suffix.lower() in (".yaml", ".yml") and yaml is not None:
			self.data.update(yaml.safe_load(self.path.read_text()) or {})
		else:
			self.data.update(json.loads(self.path.read_text()))

	def save(self) -> None:
		if self.path.suffix.lower() in (".yaml", ".yml") and yaml is not None:
			self.path.write_text(yaml.safe_dump(self.data))
		else:
			self.path.write_text(json.dumps(self.data, indent=2))

	def get(self, key: str, default: Any = None) -> Any:
		return self.data.get(key, default)
