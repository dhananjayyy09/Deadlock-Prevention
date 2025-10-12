from __future__ import annotations

from datetime import datetime
from typing import Any


class AppLogger:
	"""Simple structured logger used across layers (prints to stdout)."""

	def _log(self, level: str, message: str, **kw: Any) -> None:
		ts = datetime.now().strftime("%H:%M:%S")
		extra = (" " + " ".join(f"{k}={v}" for k, v in kw.items())) if kw else ""
		print(f"[{ts}] {level}: {message}{extra}")

	def info(self, message: str, **kw: Any) -> None:
		self._log("INFO", message, **kw)

	def warn(self, message: str, **kw: Any) -> None:
		self._log("WARN", message, **kw)

	def error(self, message: str, **kw: Any) -> None:
		self._log("ERROR", message, **kw)
