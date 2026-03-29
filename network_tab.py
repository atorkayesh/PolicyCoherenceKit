# =============================================================================
# Policy Coherence Kit -- network_tab.py
# NetworkTab: directed weighted network visualisation + centrality report.
#
# Nodes    : policies, arranged in a circle
# Edges    : non-zero cells in the aggregated matrix
#            - green for positive values, red for negative
#            - thickness mapped to |score|: 1->1px, 2->2.5px, 3->4px
#            - two arrows between a pair are offset (slight parallel shift)
# Centrality report:
#            - Betweenness: fraction of shortest paths passing through node
#            - Closeness  : inverse of mean shortest distance to all others
#            - Distance   : 1 / |score| for each edge
# =============================================================================

import math
import heapq
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Tuple, Optional

from aggregator import AggregationResult
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
    CURSOR_HAND,
)

# Visual constants
_NODE_RADIUS   = 18
_EDGE_OFFSET   = 9      # px perpendicular offset for parallel arrows
_COLOR_POS     = "#1a6e3c"   # green  (positive score)
_COLOR_NEG     = "#b71c1c"   # red    (negative score)
_COLOR_NODE    = "#2c4a6e"
_COLOR_ISOLATE = "#aaaaaa"   # grey for isolated nodes
_MARGIN        = 80

LAYOUTS = ["Circular", "Force-Directed", "Spectral", "Shell"]

def _thickness(score: float) -> float:
    """Map |score| to line width: 1->1.0, 2->2.5, 3->4.0."""
    a = abs(score)
    if a >= 2.5:  return 4.0
    if a >= 1.5:  return 2.5
    return 1.0


# =============================================================================
# Graph / centrality helpers  (pure Python, no networkx)
# Optimized with heapq priority queue and Brandes algorithm
# =============================================================================

def _build_graph(result: AggregationResult) -> Dict:
    """
    Build adjacency structure from aggregated scores.
    Returns dict with keys:
      edges   : list of (i, j, score)
      weights : dict (i,j) -> score   (non-zero only)
      dist    : dict (i,j) -> 1/|score|  (directed distances)
      adj     : adjacency list dict node -> [(neighbor, distance), ...]
      adj_rev : reversed adjacency list for backward traversal
    Results are cached in result._cached_graph for reuse.
    """
    # Return cached graph if available
    if result._cached_graph is not None:
        return result._cached_graph

    n      = result.n
    scores = result.scores
    edges, weights, dist = [], {}, {}
    adj = {i: [] for i in range(n)}
    adj_rev = {i: [] for i in range(n)}

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            s = scores.get((i, j), 0.0) or 0.0
            if s != 0.0:
                edges.append((i, j, s))
                weights[(i, j)] = s
                d = 1.0 / abs(s)
                dist[(i, j)] = d
                adj[i].append((j, d))
                adj_rev[j].append((i, d))

    graph = {
        "edges": edges,
        "weights": weights,
        "dist": dist,
        "adj": adj,
        "adj_rev": adj_rev,
        "n": n,
    }

    # Cache the graph
    result._cached_graph = graph
    return graph


def _dijkstra_with_paths(n: int, adj: Dict, source: int) -> Tuple[List[float], List[List[int]], List[int]]:
    """
    Optimized Dijkstra using heapq priority queue.
    Returns:
      d     : list of distances (inf if unreachable)
      pred  : list of predecessor lists for each node (for path counting)
      sigma : list of shortest path counts from source to each node
    """
    INF = float("inf")
    d = [INF] * n
    d[source] = 0.0
    sigma = [0] * n  # number of shortest paths
    sigma[source] = 1
    pred = [[] for _ in range(n)]  # predecessors on shortest paths

    # Priority queue: (distance, node)
    pq = [(0.0, source)]
    visited = [False] * n

    while pq:
        dist_u, u = heapq.heappop(pq)

        if visited[u]:
            continue
        visited[u] = True

        for v, w in adj.get(u, []):
            new_dist = d[u] + w
            if new_dist < d[v]:
                d[v] = new_dist
                pred[v] = [u]
                sigma[v] = sigma[u]
                heapq.heappush(pq, (new_dist, v))
            elif abs(new_dist - d[v]) < 1e-9:
                # Another shortest path found
                pred[v].append(u)
                sigma[v] += sigma[u]

    return d, pred, sigma


def _dijkstra_simple(n: int, adj: Dict, source: int) -> List[float]:
    """
    Simple optimized Dijkstra for closeness centrality.
    Returns list of distances (inf if unreachable).
    """
    INF = float("inf")
    d = [INF] * n
    d[source] = 0.0

    pq = [(0.0, source)]
    visited = [False] * n

    while pq:
        dist_u, u = heapq.heappop(pq)

        if visited[u]:
            continue
        visited[u] = True

        for v, w in adj.get(u, []):
            new_dist = d[u] + w
            if new_dist < d[v]:
                d[v] = new_dist
                heapq.heappush(pq, (new_dist, v))

    return d


def _brandes_betweenness(n: int, adj: Dict) -> Dict[int, float]:
    """
    Brandes algorithm for betweenness centrality.
    Complexity: O(VE) instead of O(V^3) or worse.
    Returns dict node -> betweenness count (unnormalised).
    """
    btw = {i: 0.0 for i in range(n)}

    for s in range(n):
        # Single-source shortest paths
        d, pred, sigma = _dijkstra_with_paths(n, adj, s)

        # Dependency accumulation (Brandes)
        delta = [0.0] * n

        # Get nodes sorted by distance (descending) for back-propagation
        INF = float("inf")
        nodes_by_dist = [(d[v], v) for v in range(n) if d[v] < INF and v != s]
        nodes_by_dist.sort(reverse=True)

        for _, w in nodes_by_dist:
            for v in pred[w]:
                # Fraction of shortest paths through v
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                btw[w] += delta[w]

    return btw


def compute_centrality(result: AggregationResult) -> List[dict]:
    """
    Compute betweenness and closeness centrality for every policy.
    Uses optimized Brandes algorithm for betweenness (O(VE) complexity).
    Returns a list of dicts (one per policy).
    Results are cached in result._cached_centrality for reuse.
    """
    # Return cached result if available
    if result._cached_centrality is not None:
        return result._cached_centrality

    n     = result.n
    graph = _build_graph(result)
    adj   = graph["adj"]

    # ---- Betweenness (using optimized Brandes algorithm) ----
    btw_raw = _brandes_betweenness(n, adj)
    # Normalise: divide by (n-1)(n-2) for directed graphs
    norm_btw = (n - 1) * (n - 2) if n > 2 else 1
    btw = {i: round(btw_raw[i] / norm_btw, 4) for i in range(n)}

    # ---- Closeness (using optimized Dijkstra) ----
    INF = float("inf")
    clo = {}
    for i in range(n):
        d_i    = _dijkstra_simple(n, adj, i)
        finite = [d for j, d in enumerate(d_i) if j != i and d != INF]
        if not finite:
            clo[i] = 0.0
        else:
            avg    = sum(finite) / len(finite)
            # Normalise by reachability fraction
            clo[i] = round((len(finite) / (n - 1)) / avg if avg > 0 else 0.0, 4)

    rows = []
    for i in range(n):
        rows.append({
            "code":        result.codes[i],
            "policy":      result.policies[i],
            "betweenness": btw[i],
            "closeness":   clo[i],
        })

    # Cache the result
    result._cached_centrality = rows
    return rows


# =============================================================================
# NetworkTab
# =============================================================================

class NetworkTab(tk.Frame):
    """
    Directed weighted network diagram + centrality report table.
    """

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result      = result
        self._graph       = _build_graph(result)
        self._centrality  = compute_centrality(result)
        self._tooltip_win: Optional[tk.Toplevel] = None
        self._layout_var  = tk.StringVar(value='Force-Directed')
        self._ego_var     = tk.StringVar(value='Full Network')
        self._redraw_pending: Optional[str] = None  # Debounce timer ID
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)

        # Split: network on left, report on right
        pane = tk.PanedWindow(self, orient="horizontal",
                              bg=COLOR_BG, sashwidth=6,
                              sashrelief="flat", sashpad=2)
        pane.pack(fill="both", expand=True, padx=8, pady=8)

        net_frame    = tk.Frame(pane, bg=COLOR_BG)
        report_frame = tk.Frame(pane, bg=COLOR_BG)
        pane.add(net_frame,    minsize=300, stretch="always")
        pane.add(report_frame, minsize=260, stretch="never")

        self._build_network(net_frame)
        self._build_report(report_frame)

    # ------------------------------------------------------------------

    def _build_info_bar(self):
        bar = tk.Frame(self, bg=COLOR_PANEL, pady=8)
        bar.pack(fill="x")

        method_label = {
            "average":  "Average",
            "majority": "Majority Rule",
            "weighted": "Weighted",
        }.get(self._result.method, self._result.method.title())

        tk.Label(
            bar,
            text=f"Network Analysis  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
        ).pack(side="left", padx=16)

        n_edges  = len(self._graph["edges"])
        n_nodes  = self._result.n
        isolated = sum(
            1 for i in range(n_nodes)
            if not any(k[0] == i or k[1] == i for k in self._graph["weights"])
        )
        max_edges = n_nodes * (n_nodes - 1) if n_nodes > 1 else 1
        density   = round(n_edges / max_edges, 3)
        stats_txt = (
            f"{n_nodes} nodes  |  {n_edges} directed edges  "
            f"|  density: {density}"
            + (f"  |  {isolated} isolated" if isolated else "")
        )
        tk.Label(
            bar,
            text=stats_txt,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------------

    def _build_network(self, parent: tk.Frame):
        # ---- Controls row ----
        ctrl = tk.Frame(parent, bg=COLOR_BG)
        ctrl.pack(fill="x", padx=8, pady=(4, 2))

        # Layout selector
        tk.Label(ctrl, text="Layout:",
                 font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT,
                 ).pack(side="left", padx=(0, 4))
        layout_cb = ttk.Combobox(
            ctrl, textvariable=self._layout_var,
            values=LAYOUTS, state="readonly", width=15,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        )
        layout_cb.pack(side="left", padx=(0, 16))
        layout_cb.bind("<<ComboboxSelected>>",
                       lambda e: self._on_view_change())

        # Ego policy selector
        tk.Label(ctrl, text="Focus Policy:",
                 font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT,
                 ).pack(side="left", padx=(0, 4))
        ego_options = ["Full Network"] + [
            f"{c}: {p}" for c, p in zip(
                self._result.codes, self._result.policies)
        ]
        ego_cb = ttk.Combobox(
            ctrl, textvariable=self._ego_var,
            values=ego_options, state="readonly", width=28,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        )
        ego_cb.pack(side="left", padx=(0, 16))
        ego_cb.bind("<<ComboboxSelected>>",
                    lambda e: self._on_view_change())

        # Legend
        for color, label in [(_COLOR_POS, "Positive"),
                              (_COLOR_NEG, "Negative"),
                              (_COLOR_ISOLATE, "Isolated")]:
            tk.Label(ctrl, text="━━", fg=color, bg=COLOR_BG,
                     font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                     ).pack(side="left", padx=(0, 2))
            tk.Label(ctrl, text=label, fg=COLOR_TEXT_LIGHT, bg=COLOR_BG,
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     ).pack(side="left", padx=(0, 8))

        # Canvas
        self._canvas = tk.Canvas(parent, bg="#ffffff",
                                 highlightthickness=2,
                                 highlightbackground=COLOR_ACCENT)
        self._canvas.pack(fill="both", expand=True, padx=8, pady=(2, 4))
        self._canvas.bind("<Configure>", lambda e: self._on_view_change_debounced())

        # Save button
        save_row = tk.Frame(parent, bg=COLOR_BG)
        save_row.pack(anchor="e", padx=8, pady=(2, 6))
        tk.Button(
            save_row, text="Save as PNG",
            command=self._save_network,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
            relief="flat", padx=8, pady=3, cursor=CURSOR_HAND,
        ).pack(side="right")

    # ------------------------------------------------------------------

    def _redraw_network(self):
        canvas = self._canvas
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10 or h < 10:
            return

        n        = self._result.n
        codes    = self._result.codes
        policies = self._result.policies
        edges    = self._graph["edges"]
        weights  = self._graph["weights"]

        # Circular layout
        cx, cy = w / 2, h / 2
        r_layout = min(w, h) / 2 - _MARGIN

        angles = [2 * math.pi * i / n - math.pi / 2 for i in range(n)]
        node_pos = [
            (cx + r_layout * math.cos(a),
             cy + r_layout * math.sin(a))
            for a in angles
        ]

        # Determine isolated nodes
        connected = set()
        for (i, j, _) in edges:
            connected.add(i); connected.add(j)

        # ---- Draw edges ----
        # Track pairs to detect bi-directional edges
        pair_count: Dict[tuple, int] = {}
        for (i, j, _) in edges:
            key = (min(i,j), max(i,j))
            pair_count[key] = pair_count.get(key, 0) + 1

        drawn_pairs: Dict[tuple, int] = {}

        for (i, j, score) in edges:
            x1, y1 = node_pos[i]
            x2, y2 = node_pos[j]
            color  = _COLOR_POS if score > 0 else _COLOR_NEG
            width  = _thickness(score)
            key    = (min(i,j), max(i,j))

            bidirectional = pair_count[key] == 2
            drawn_pairs[key] = drawn_pairs.get(key, 0) + 1
            side = drawn_pairs[key]   # 1 or 2

            if bidirectional:
                # Perpendicular offset
                dx, dy  = x2 - x1, y2 - y1
                length  = math.hypot(dx, dy) or 1
                ox      = -dy / length * _EDGE_OFFSET
                oy      =  dx / length * _EDGE_OFFSET
                sign    = 1 if side == 1 else -1
                mx1, my1 = x1 + sign*ox, y1 + sign*oy
                mx2, my2 = x2 + sign*ox, y2 + sign*oy
            else:
                mx1, my1 = x1, y1
                mx2, my2 = x2, y2

            # Shorten line so it doesn't overlap the node circle
            ddx, ddy = mx2 - mx1, my2 - my1
            dist_    = math.hypot(ddx, ddy) or 1
            sx       = mx1 + ddx / dist_ * _NODE_RADIUS
            sy       = my1 + ddy / dist_ * _NODE_RADIUS
            ex       = mx2 - ddx / dist_ * _NODE_RADIUS
            ey       = my2 - ddy / dist_ * _NODE_RADIUS

            canvas.create_line(sx, sy, ex, ey,
                               fill=color, width=width,
                               arrow="last", arrowshape=(10, 12, 4))

        # ---- Draw nodes ----
        nr = _NODE_RADIUS
        for i, (nx_, ny_) in enumerate(node_pos):
            is_isolated = i not in connected
            fill  = _COLOR_ISOLATE if is_isolated else _COLOR_NODE
            oval  = canvas.create_oval(
                nx_-nr, ny_-nr, nx_+nr, ny_+nr,
                fill=fill, outline="#ffffff", width=1.5,
            )
            canvas.create_text(
                nx_, ny_,
                text=codes[i],
                font=(FONT_FAMILY, FONT_SIZE_SMALL - 1, "bold"),
                fill="#ffffff",
            )
            full_name = policies[i]
            canvas.tag_bind(oval, "<Enter>",
                lambda e, c=codes[i], p=full_name:
                    self._show_tooltip(e, f"{c}:  {p}"))
            canvas.tag_bind(oval, "<Leave>",
                lambda e: self._hide_tooltip())

    # ------------------------------------------------------------------

    def _save_network(self):
        """Export the network canvas to a PNG file."""
        from tkinter import filedialog
        try:
            from PIL import ImageGrab
        except ImportError:
            path = filedialog.asksaveasfilename(
                title="Save Network plot",
                defaultextension=".ps",
                filetypes=[("PostScript", "*.ps"), ("All files", "*.*")],
                initialfile="network_plot.ps",
            )
            if path:
                self._canvas.postscript(file=path, colormode="color")
                import tkinter.messagebox as mb
                mb.showinfo("Saved", f"Saved as PostScript:\n{path}\n\n"
                            "Open with any PS viewer or convert with Ghostscript.")
            return
        path = filedialog.asksaveasfilename(
            title="Save Network plot",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All files", "*.*")],
            initialfile="network_plot.png",
        )
        if not path:
            return
        x = self._canvas.winfo_rootx()
        y = self._canvas.winfo_rooty()
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        ImageGrab.grab(bbox=(x, y, x+w, y+h)).save(path)
        import tkinter.messagebox as mb
        mb.showinfo("Saved", f"Network plot saved to:\n{path}")

    def _on_view_change_debounced(self):
        """Debounced version of _on_view_change to prevent excessive redraws."""
        # Cancel any pending redraw
        if self._redraw_pending is not None:
            self.after_cancel(self._redraw_pending)
        # Schedule redraw after 50ms of no new events
        self._redraw_pending = self.after(50, self._on_view_change)

    def _on_view_change(self):
        """Dispatch to full network or ego view based on selector."""
        self._redraw_pending = None
        sel = self._ego_var.get()
        if sel == "Full Network":
            self._redraw_network()
        else:
            # Extract policy index from 'P1: Climate Policy'
            code = sel.split(":")[0].strip()
            idx  = next((i for i, c in enumerate(self._result.codes)
                         if c == code), None)
            if idx is not None:
                self._redraw_ego(idx)

    # ------------------------------------------------------------------

    def _redraw_ego(self, ego_idx: int):
        """Draw the ego network for a single policy."""
        canvas = self._canvas
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10 or h < 10:
            return

        codes    = self._result.codes
        policies = self._result.policies
        edges    = self._graph["edges"]

        # Collect only edges directly involving ego
        ego_edges = [(i, j, s) for (i, j, s) in edges
                     if i == ego_idx or j == ego_idx]

        # Neighbour indices (excluding ego itself)
        neighbour_set = set()
        for (i, j, _) in ego_edges:
            if i != ego_idx: neighbour_set.add(i)
            if j != ego_idx: neighbour_set.add(j)
        neighbours = sorted(neighbour_set)

        # ---- Node positions ----
        cx, cy    = w / 2, h / 2
        r_layout  = min(w, h) / 2 - _MARGIN
        m_nb      = len(neighbours)

        node_pos  = {}  # idx -> (x, y)
        node_pos[ego_idx] = (cx, cy)

        for k, nb in enumerate(neighbours):
            angle = 2 * math.pi * k / m_nb - math.pi / 2 if m_nb > 1 else 0
            node_pos[nb] = (
                cx + r_layout * math.cos(angle),
                cy + r_layout * math.sin(angle),
            )

        # ---- Canvas title ----
        canvas.create_text(
            w / 2, 18,
            text=f"Ego Network:  {codes[ego_idx]}  ({policies[ego_idx]})",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            fill=COLOR_TEXT_LIGHT,
        )

        if not neighbours:
            canvas.create_text(
                cx, cy,
                text=f"{codes[ego_idx]} has no direct connections.",
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
                fill=COLOR_TEXT_LIGHT,
            )
            # Still draw the isolated ego node
            nr = _NODE_RADIUS
            canvas.create_oval(cx-nr, cy-nr, cx+nr, cy+nr,
                               fill=_COLOR_ISOLATE, outline="#ffffff", width=1.5)
            canvas.create_text(cx, cy, text=codes[ego_idx],
                               font=(FONT_FAMILY, FONT_SIZE_SMALL-1, "bold"),
                               fill="#ffffff")
            return

        # ---- Draw edges ----
        # Check bidirectionality within ego edges only
        pair_count: Dict[tuple, int] = {}
        for (i, j, _) in ego_edges:
            key = (min(i,j), max(i,j))
            pair_count[key] = pair_count.get(key, 0) + 1
        drawn_pairs: Dict[tuple, int] = {}

        for (i, j, score) in ego_edges:
            if i not in node_pos or j not in node_pos:
                continue
            x1, y1 = node_pos[i]
            x2, y2 = node_pos[j]
            color   = _COLOR_POS if score > 0 else _COLOR_NEG
            width   = _thickness(score)
            key     = (min(i,j), max(i,j))
            bidirectional = pair_count[key] == 2
            drawn_pairs[key] = drawn_pairs.get(key, 0) + 1
            side = drawn_pairs[key]

            if bidirectional:
                dx, dy = x2-x1, y2-y1
                length = math.hypot(dx, dy) or 1
                ox = -dy/length * _EDGE_OFFSET
                oy =  dx/length * _EDGE_OFFSET
                sign = 1 if side == 1 else -1
                mx1, my1 = x1+sign*ox, y1+sign*oy
                mx2, my2 = x2+sign*ox, y2+sign*oy
            else:
                mx1, my1, mx2, my2 = x1, y1, x2, y2

            ddx, ddy = mx2-mx1, my2-my1
            dist_    = math.hypot(ddx, ddy) or 1
            sx = mx1 + ddx/dist_ * _NODE_RADIUS
            sy = my1 + ddy/dist_ * _NODE_RADIUS
            ex = mx2 - ddx/dist_ * _NODE_RADIUS
            ey = my2 - ddy/dist_ * _NODE_RADIUS
            canvas.create_line(sx, sy, ex, ey,
                               fill=color, width=width,
                               arrow="last", arrowshape=(10, 12, 4))

            # Score label on edge midpoint
            mid_x = (sx + ex) / 2
            mid_y = (sy + ey) / 2
            canvas.create_text(
                mid_x, mid_y - 8,
                text=f"{score:+.2f}",
                font=(FONT_FAMILY, FONT_SIZE_SMALL-1),
                fill=color,
            )

        # ---- Draw nodes ----
        nr = _NODE_RADIUS
        for idx_, (nx_, ny_) in node_pos.items():
            is_ego = (idx_ == ego_idx)
            fill   = COLOR_ACCENT2 if is_ego else _COLOR_NODE
            size   = nr + 4 if is_ego else nr
            oval   = canvas.create_oval(
                nx_-size, ny_-size, nx_+size, ny_+size,
                fill=fill, outline="#ffffff", width=2 if is_ego else 1.5,
            )
            canvas.create_text(
                nx_, ny_,
                text=codes[idx_],
                font=(FONT_FAMILY, FONT_SIZE_SMALL-1, "bold"),
                fill="#ffffff",
            )
            full_name = policies[idx_]
            canvas.tag_bind(oval, "<Enter>",
                lambda e, c=codes[idx_], p=full_name:
                    self._show_tooltip(e, f"{c}:  {p}"))
            canvas.tag_bind(oval, "<Leave>",
                lambda e: self._hide_tooltip())

    # ------------------------------------------------------------------

    def _build_report(self, parent: tk.Frame):
        tk.Label(
            parent,
            text="Centrality Measures",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).pack(anchor="w", padx=8, pady=(4, 2))

        tk.Label(
            parent,
            text="Betweenness: broker role  |  Closeness: reachability",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(anchor="w", padx=8, pady=(0, 6))

        # Scrollable table
        canvas   = tk.Canvas(parent, bg=COLOR_BG, highlightthickness=0)
        v_scroll = ttk.Scrollbar(parent, orient="vertical",
                                 command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(
                int(-1*(e.delta/120)), "units"))

        self._draw_report(inner)

    # ------------------------------------------------------------------

    def _draw_report(self, frame: tk.Frame):
        pad     = 2
        headers = ["Policy", "Betweenness", "Closeness", "Full Name"]
        widths  = [6, 13, 10, 20]

        for col, (hdr, w) in enumerate(zip(headers, widths)):
            tk.Label(
                frame, text=hdr, width=w,
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg=COLOR_ACCENT, fg="#ffffff",
                relief="flat", padx=6, pady=6, anchor="center",
            ).grid(row=0, column=col, padx=pad, pady=(6, pad), sticky="nsew")

        # Sort by betweenness descending for readability
        rows = sorted(self._centrality,
                      key=lambda r: r["betweenness"], reverse=True)

        for r, row in enumerate(rows):
            bg = "#ffffff" if r % 2 == 0 else "#f4f1ec"

            tk.Label(frame, text=row["code"], width=widths[0],
                     font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                     bg=bg, fg=COLOR_TEXT, relief="groove",
                     borderwidth=1, padx=6, pady=5, anchor="center",
                     ).grid(row=r+1, column=0, padx=pad, pady=pad,
                            sticky="nsew")

            tk.Label(frame, text=f"{row['betweenness']:.4f}",
                     width=widths[1],
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=bg, fg=COLOR_TEXT, relief="groove",
                     borderwidth=1, padx=6, pady=5, anchor="center",
                     ).grid(row=r+1, column=1, padx=pad, pady=pad,
                            sticky="nsew")

            tk.Label(frame, text=f"{row['closeness']:.4f}",
                     width=widths[2],
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=bg, fg=COLOR_TEXT, relief="groove",
                     borderwidth=1, padx=6, pady=5, anchor="center",
                     ).grid(row=r+1, column=2, padx=pad, pady=pad,
                            sticky="nsew")

            tk.Label(frame, text=row["policy"], width=widths[3],
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=bg, fg=COLOR_TEXT, relief="groove",
                     borderwidth=1, padx=8, pady=5, anchor="w",
                     ).grid(row=r+1, column=3, padx=pad, pady=pad,
                            sticky="nsew")

    # ------------------------------------------------------------------

    def _show_tooltip(self, event, text: str):
        self._hide_tooltip()
        x = event.widget.winfo_rootx() + event.x + 14
        y = event.widget.winfo_rooty() + event.y + 14
        tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=text, justify="left",
            background="#fffbe6", foreground="#1e1e1e",
            relief="solid", borderwidth=1,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            padx=8, pady=4,
        ).pack()
        self._tooltip_win = tw

    def _hide_tooltip(self):
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None
