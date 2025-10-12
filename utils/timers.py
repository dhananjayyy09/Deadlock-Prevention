from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def measure(label: str) -> Iterator[None]:
	start = time.perf_counter()
	yield
	elapsed = (time.perf_counter() - start) * 1000.0
	print(f"{label} took {elapsed:.2f} ms")
