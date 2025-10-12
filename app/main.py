from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Set

from .graph_view import GraphView
from ..core.bankers import BankersAlgorithm
from ..core.wfg import WFGDetector
from ..core.recovery import RecoveryManager
from ..core.models import SystemSnapshot, WaitForGraph, Process, Resource
from ..data.config import ConfigManager
from ..data.logging import AppLogger
from ..sysif.ps_reader import PsutilReader
from ..sysif.normalize import Normalizer


class DeadlockApp(tk.Tk):
	"""Tkinter app entry point: wires GUI controls to core engine and views."""

	def __init__(self) -> None:
		super().__init__()
		self.title("Deadlock Tool - Prediction, Detection, Recovery")
		self.geometry("1280x800")
		self.minsize(1024, 700)

		self._init_theme()

		self.logger = AppLogger()
		self.config_manager = ConfigManager()
		self.bankers = BankersAlgorithm()
		self.wfg_detector = WFGDetector()
		self.recovery = RecoveryManager()
		self.reader = PsutilReader()
		self.normalizer = Normalizer()

		self.view_mode = tk.StringVar(value="RAG")  # RAG or WFG
		self.auto_refresh_ms = 0  # disabled by default

		self._build_ui()

		# Initial snapshot
		self.snapshot: Optional[SystemSnapshot] = self._demo_snapshot()
		self._refresh_views()

	def _init_theme(self) -> None:
		style = ttk.Style(self)
		for candidate in ("vista", "xpnative", "clam", "alt", "default"):
			if candidate in style.theme_names():
				style.theme_use(candidate)
				break
		style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0b3b59")
		style.configure("Section.TLabelframe", padding=10)
		style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
		style.configure("TButton", padding=(10, 6))

	def _gradient_bar(self, parent: tk.Widget, height: int = 56, start="#0ea5e9", end="#10b981") -> tk.Canvas:
		canvas = tk.Canvas(parent, height=height, highlightthickness=0, bd=0)
		# Draw simple left-to-right gradient by rectangles
		steps = 256
		width = 1200
		for i in range(steps):
			r = i / (steps - 1)
			color = _lerp_hex(start, end, r)
			x0 = int(i * (width / steps))
			x1 = int((i + 1) * (width / steps))
			canvas.create_rectangle(x0, 0, x1, height, outline="", fill=color)
		return canvas

	def _build_ui(self) -> None:
		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, weight=1)

		# Header with gradient
		header = ttk.Frame(self)
		header.grid(row=0, column=0, sticky="ew")
		grad = self._gradient_bar(header, height=60)
		grad.pack(fill="x")
		title = ttk.Label(header, text="Deadlock Prediction, Detection, and Recovery", style="Title.TLabel", background="")
		title.place(x=16, y=16)

		# Body
		body = ttk.Frame(self, padding=(8, 8))
		body.grid(row=1, column=0, sticky="nsew")
		body.columnconfigure(0, weight=0)
		body.columnconfigure(1, weight=1)
		body.rowconfigure(0, weight=1)

		# Sidebar controls
		controls = ttk.Labelframe(body, text="Controls", style="Section.TLabelframe")
		controls.grid(row=0, column=0, sticky="nsw", padx=(0, 10))

		row = 0
		toolbar = ttk.Frame(controls)
		toolbar.grid(row=row, column=0, sticky="ew", pady=(0, 8))
		row += 1

		predict_btn = ttk.Button(toolbar, text="Predict (Banker)", command=self.on_predict)
		predict_btn.grid(row=0, column=0, padx=(0, 6))
		detect_btn = ttk.Button(toolbar, text="Detect (WFG)", command=self.on_detect)
		detect_btn.grid(row=0, column=1, padx=(0, 6))
		recover_btn = ttk.Button(toolbar, text="Recover", command=self.on_recover)
		recover_btn.grid(row=0, column=2, padx=(0, 6))

		# Load/Auto
		actions = ttk.Frame(controls)
		actions.grid(row=row, column=0, sticky="ew")
		row += 1
		load_btn = ttk.Button(actions, text="Load System Snapshot", command=self.on_load_system)
		load_btn.grid(row=0, column=0, pady=(0, 6), sticky="ew")
		self.auto_var = tk.IntVar(value=0)
		auto_chk = ttk.Checkbutton(actions, text="Auto-Refresh (2s)", variable=self.auto_var, command=self.on_toggle_auto)
		auto_chk.grid(row=1, column=0, sticky="w")

		# View toggle
		sep = ttk.Separator(controls, orient="horizontal")
		sep.grid(row=row, column=0, sticky="ew", pady=8)
		row += 1
		view_frame = ttk.Frame(controls)
		view_frame.grid(row=row, column=0, sticky="ew")
		row += 1
		rag_radio = ttk.Radiobutton(view_frame, text="Resource Allocation Graph", value="RAG", variable=self.view_mode, command=self._refresh_views)
		rag_radio.grid(row=0, column=0, sticky="w")
		wfg_radio = ttk.Radiobutton(view_frame, text="Wait-for Graph", value="WFG", variable=self.view_mode, command=self._refresh_views)
		wfg_radio.grid(row=1, column=0, sticky="w")

		# Status label
		self.status_var = tk.StringVar(value="Ready")
		status_label = ttk.Label(controls, textvariable=self.status_var, wraplength=240, justify="left")
		status_label.grid(row=row, column=0, sticky="ew", pady=(8, 0))

		# Graph area
		graph_container = ttk.Frame(body)
		graph_container.grid(row=0, column=1, sticky="nsew")
		graph_container.rowconfigure(0, weight=1)
		graph_container.columnconfigure(0, weight=1)

		self.graph_view = GraphView(graph_container)
		self.graph_view.grid(row=0, column=0, sticky="nsew")

		# Footer gradient
		footer = ttk.Frame(self)
		footer.grid(row=2, column=0, sticky="ew")
		grad2 = self._gradient_bar(footer, height=18, start="#10b981", end="#0ea5e9")
		grad2.pack(fill="x")

		self.footer_var = tk.StringVar(value="Idle")
		# Overlay footer text on top-left
		lbl = ttk.Label(footer, textvariable=self.footer_var)
		lbl.place(x=12, y=0)

	def _demo_snapshot(self) -> SystemSnapshot:
		p0 = Process(pid=1, name="P0")
		p1 = Process(pid=2, name="P1")
		resources = {
			"R": Resource(rid="R", total=3)
		}
		allocation = {(1, "R"): 1, (2, "R"): 1}
		request = {(1, "R"): 1, (2, "R"): 2}
		return SystemSnapshot(processes=[p0, p1], resources=resources, allocation=allocation, request=request)

	def _refresh_views(self) -> None:
		if self.snapshot is None:
			return
		if self.view_mode.get() == "RAG":
			self.graph_view.render_snapshot(self.snapshot)
		else:
			wfg = self._build_wfg(self.snapshot)
			cycles = self.wfg_detector.find_cycles(wfg)
			self.graph_view.render_wfg(wfg, cycles)

	def _build_wfg(self, snapshot: SystemSnapshot) -> WaitForGraph:
		edges = {}
		for (pid_r, rid), need in snapshot.request.items():
			if need <= 0:
				continue
			blockers = [pid for (pid, r), alloc in snapshot.allocation.items() if r == rid and alloc > 0 and pid != pid_r]
			if blockers:
				edges.setdefault(pid_r, set()).update(blockers)
		return WaitForGraph(edges)

	def on_predict(self) -> None:
		if self.snapshot is None:
			return
		safe = self.bankers.is_safe(self.snapshot)
		self.status_var.set(f"Prediction: {'SAFE' if safe else 'UNSAFE'}")
		self.footer_var.set("Ran Banker's prediction")
		self.logger.info(f"Banker safe={safe}")

	def on_detect(self) -> None:
		if self.snapshot is None:
			return
		wfg = self._build_wfg(self.snapshot)
		cycles = self.wfg_detector.find_cycles(wfg)
		self.status_var.set("Detection: " + ("No cycles" if not cycles else f"Cycles: {cycles}"))
		self.footer_var.set("Ran WFG detection")
		self.logger.info(f"WFG cycles={cycles}")
		if self.view_mode.get() == "WFG":
			self.graph_view.render_wfg(wfg, cycles)

	def on_recover(self) -> None:
		if self.snapshot is None:
			return
		wfg = self._build_wfg(self.snapshot)
		cycles = self.wfg_detector.find_cycles(wfg)
		victims = self.recovery.choose_victims(cycles)
		self.snapshot = self.recovery.apply_preemption(self.snapshot, victims)
		self._refresh_views()
		self.status_var.set(f"Recovery: preempted {victims if victims else 'none'}")
		self.footer_var.set("Applied recovery simulation")
		self.logger.info(f"Recovered victims={victims}")

	def on_load_system(self) -> None:
		data = self.reader.snapshot()
		self.snapshot = self.normalizer.to_snapshot(data)
		self._refresh_views()
		self.status_var.set("Loaded live system snapshot (limited demo mapping)")
		self.footer_var.set("Loaded system state via psutil")
		self.logger.info("Loaded psutil snapshot")

	def on_toggle_auto(self) -> None:
		self.auto_refresh_ms = 2000 if self.auto_var.get() else 0
		if self.auto_refresh_ms:
			self._schedule_auto_refresh()

	def _schedule_auto_refresh(self) -> None:
		if self.auto_refresh_ms <= 0:
			return
		self.on_load_system()
		self.after(self.auto_refresh_ms, self._schedule_auto_refresh)


def _lerp_hex(a: str, b: str, t: float) -> str:
	def h2rgb(h: str) -> tuple[int, int, int]:
		h = h.lstrip('#')
		return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
	ar, ag, ab = h2rgb(a)
	br, bg, bb = h2rgb(b)
	r = int(ar + (br - ar) * t)
	g = int(ag + (bg - ag) * t)
	b2 = int(ab + (bb - ab) * t)
	return f"#{r:02x}{g:02x}{b2:02x}"


def main() -> None:
	app = DeadlockApp()
	app.mainloop()


if __name__ == "__main__":
	main()
