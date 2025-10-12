from __future__ import annotations

import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
from typing import Dict, Tuple, List, Set

from ..core.models import SystemSnapshot, WaitForGraph


class GraphView(tk.Frame):
	"""Embeds a Matplotlib figure and renders graphs (RAG and WFG)."""

	def __init__(self, master: tk.Misc) -> None:
		super().__init__(master)
		self.figure = Figure(figsize=(6, 5), dpi=100)
		self.ax = self.figure.add_subplot(111)
		self.canvas = FigureCanvasTkAgg(self.figure, master=self)
		toolbar = NavigationToolbar2Tk(self.canvas, self)
		toolbar.update()
		self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

	def render_snapshot(self, snapshot: SystemSnapshot) -> None:
		g = nx.DiGraph()
		proc_nodes = []
		res_nodes = []
		for p in snapshot.processes:
			name = f"P{p.pid}"
			g.add_node(name, kind="proc")
			proc_nodes.append(name)
		for rid, _ in snapshot.resources.items():
			name = f"R{rid}"
			g.add_node(name, kind="res")
			res_nodes.append(name)
		for (pid, rid), alloc in snapshot.allocation.items():
			if alloc > 0:
				g.add_edge(f"P{pid}", f"R{rid}", weight=alloc, etype="alloc")
		for (pid, rid), req in snapshot.request.items():
			if req > 0:
				g.add_edge(f"R{rid}", f"P{pid}", weight=req, etype="request")

		self.ax.clear()
		pos = nx.spring_layout(g, seed=42)

		# Draw nodes with distinct shapes/colors
		nx.draw_networkx_nodes(g, pos=pos, nodelist=proc_nodes, node_color="#2563eb", node_shape="o", node_size=700, ax=self.ax)
		nx.draw_networkx_nodes(g, pos=pos, nodelist=res_nodes, node_color="#10b981", node_shape="s", node_size=700, ax=self.ax)
		nx.draw_networkx_labels(g, pos=pos, font_color="white", ax=self.ax)

		# Separate edge types with different colors
		alloc_edges = [(u, v) for u, v, d in g.edges(data=True) if d.get("etype") == "alloc"]
		req_edges = [(u, v) for u, v, d in g.edges(data=True) if d.get("etype") == "request"]
		nx.draw_networkx_edges(g, pos=pos, edgelist=alloc_edges, edge_color="#1f2937", arrows=True, width=2, ax=self.ax)
		nx.draw_networkx_edges(g, pos=pos, edgelist=req_edges, edge_color="#ef4444", arrows=True, width=2, style="dashed", ax=self.ax)

		edge_labels: Dict[Tuple[str, str], str] = {(u, v): str(d.get('weight', '')) for u, v, d in g.edges(data=True)}
		nx.draw_networkx_edge_labels(g, pos=pos, edge_labels=edge_labels, ax=self.ax, font_color="#111827")

		self.ax.set_title("Resource Allocation Graph", loc="left")
		self.ax.axis('off')
		self.canvas.draw()

	def render_wfg(self, wfg: WaitForGraph, cycles: List[Set[int]] | None = None) -> None:
		g = nx.DiGraph()
		for src, nbrs in wfg.edges.items():
			src_n = f"P{src}"
			g.add_node(src_n)
			for dst in nbrs:
				dst_n = f"P{dst}"
				g.add_node(dst_n)
				g.add_edge(src_n, dst_n)

		cycle_nodes: Set[str] = set()
		if cycles:
			for cyc in cycles:
				for pid in cyc:
					cycle_nodes.add(f"P{pid}")

		self.ax.clear()
		pos = nx.spring_layout(g, seed=24)
		nodes = list(g.nodes())
		colors = ["#ef4444" if n in cycle_nodes else "#2563eb" for n in nodes]
		nx.draw_networkx_nodes(g, pos=pos, nodelist=nodes, node_color=colors, node_size=700, ax=self.ax)
		nx.draw_networkx_labels(g, pos=pos, font_color="white", ax=self.ax)
		nx.draw_networkx_edges(g, pos=pos, arrows=True, width=2, edge_color="#1f2937", ax=self.ax)
		self.ax.set_title("Wait-for Graph (red = in cycle)", loc="left")
		self.ax.axis('off')
		self.canvas.draw()


def plt_proxy(marker: str, color: str):
	from matplotlib.lines import Line2D
	return Line2D([0], [0], marker=marker, color="w", markerfacecolor=color, markersize=10)


def line_proxy(color: str, dashed: bool = False):
	from matplotlib.lines import Line2D
	return Line2D([0], [0], color=color, linewidth=2, linestyle="--" if dashed else "-")
