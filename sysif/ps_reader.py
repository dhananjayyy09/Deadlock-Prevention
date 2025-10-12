import psutil
from typing import Any, Dict, List


class PsutilReader:
	"""Collect a safe subset of system info for academic modeling.

	This does not attempt to infer OS-level resource locks; it only enumerates
	processes and provides placeholders that can be mapped by normalize.py.
	"""

	def snapshot(self) -> Dict[str, Any]:
		procs: List[Dict[str, Any]] = []
		for p in psutil.process_iter(attrs=["pid", "name"]):
			info = p.info
			procs.append({"pid": info.get("pid"), "name": info.get("name", "proc")})
		return {"processes": procs}
