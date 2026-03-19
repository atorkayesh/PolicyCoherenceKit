# =============================================================================
# Policy Coherence Kit -- network_tab.py
# NetworkTab: directed weighted network + centrality report.
#
# Layout options (pure Python, no networkx):
#   Circular           - evenly spaced on a circle
#   Force-directed     - Fruchterman-Reingold spring model
#   Spectral           - eigenvector-based, groups similar policies
#   Shell              - high-betweenness nodes in centre ring
# =============================================================================

import math
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Tuple, Optional

from .aggregator import AggregationResult
from .constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
)

_NODE_RADIUS   = 18
_EDGE_OFFSET   = 9
_COLOR_POS     = "#1a6e3c"
_COLOR_NEG     = "#b71c1c"
_COLOR_NODE    = "#2c4a6e"
_COLOR_ISOLATE = "#aaaaaa"
_MARGIN        = 80

LAYOUTS = ["Circular", "Force-Directed", "Spectral", "Shell"]


def _thickness(score: float) -> float:
    a = abs(score)
    if a >= 2.5: return 4.0
    if a >= 1.5: return 2.5
    return 1.0


# =============================================================================
# Graph helpers
# =============================================================================

def _build_graph(result: AggregationResult) -> Dict:
    n, scores = result.n, result.scores
    edges, weights, dist = [], {}, {}
    for i in range(n):
        for j in range(n):
            if i == j: continue
            s = scores.get((i, j), 0.0) or 0.0
            if s != 0.0:
                edges.append((i, j, s))
                weights[(i, j)] = s
                dist[(i, j)]    = 1.0 / abs(s)
    return {"edges": edges, "weights": weights, "dist": dist}


def _dijkstra(n: int, dist: Dict, source: int) -> List[float]:
    INF = float("inf")
    d   = [INF] * n
    d[source] = 0.0
    visited   = [False] * n
    for _ in range(n):
        u = min((i for i in range(n) if not visited[i]), key=lambda i: d[i], default=None)
        if u is None or d[u] == INF: break
        visited[u] = True
        for (ui, v), w in dist.items():
            if ui == u and not visited[v] and d[u] + w < d[v]:
                d[v] = d[u] + w
    return d


def _all_shortest_paths_counts(n: int, dist: Dict) -> Dict:
    btw = {i: 0.0 for i in range(n)}
    rev_dist = {(j, i): w for (i, j), w in dist.items()}
    for s in range(n):
        d_s = _dijkstra(n, dist, s)
        for t in range(n):
            if t == s or d_s[t] == float("inf"): continue
            d_rev_t = _dijkstra(n, rev_dist, t)
            for v in range(n):
                if v == s or v == t: continue
                if (d_s[v] != float("inf") and d_rev_t[v] != float("inf") and
                        abs(d_s[v] + d_rev_t[v] - d_s[t]) < 1e-9):
                    btw[v] += 1.0
    return btw


def compute_centrality(result: AggregationResult) -> List[dict]:
    n     = result.n
    dist  = _build_graph(result)["dist"]
    btw_raw = _all_shortest_paths_counts(n, dist)
    norm_btw = (n-1)*(n-2) if n > 2 else 1
    btw = {i: round(btw_raw[i]/norm_btw, 4) for i in range(n)}
    INF = float("inf")
    clo = {}
    for i in range(n):
        d_i    = _dijkstra(n, dist, i)
        finite = [d for j, d in enumerate(d_i) if j != i and d != INF]
        if not finite: clo[i] = 0.0
        else:
            avg = sum(finite) / len(finite)
            clo[i] = round((len(finite)/(n-1))/avg if avg > 0 else 0.0, 4)
    return [{"code": result.codes[i], "policy": result.policies[i],
             "betweenness": btw[i], "closeness": clo[i]} for i in range(n)]


# =============================================================================
# Layout algorithms  (all return list of (x, y) in [0,1] normalised space)
# =============================================================================

def _layout_circular(n: int, **kwargs) -> List[Tuple[float, float]]:
    """Evenly spaced around a unit circle."""
    return [
        (0.5 + 0.5 * math.cos(2*math.pi*i/n - math.pi/2),
         0.5 + 0.5 * math.sin(2*math.pi*i/n - math.pi/2))
        for i in range(n)
    ]


def _layout_force_directed(n: int, edges: List, iterations: int = 200,
                            **kwargs) -> List[Tuple[float, float]]:
    """
    Fruchterman-Reingold spring-embedder.
    Repulsion between all pairs, attraction along edges.
    """
    import random
    random.seed(42)

    if n == 1:
        return [(0.5, 0.5)]

    # Initialise on a small circle to avoid symmetry collapse
    pos = [
        (0.5 + 0.3*math.cos(2*math.pi*i/n),
         0.5 + 0.3*math.sin(2*math.pi*i/n))
        for i in range(n)
    ]

    area = 1.0
    k    = math.sqrt(area / n)   # ideal edge length

    for iteration in range(iterations):
        temp = 0.1 * (1 - iteration / iterations)  # cooling

        disp = [(0.0, 0.0)] * n

        # Repulsion between every pair
        for u in range(n):
            dx_sum, dy_sum = 0.0, 0.0
            for v in range(n):
                if u == v: continue
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist_ = math.hypot(dx, dy) or 0.001
                force = k*k / dist_
                dx_sum += (dx/dist_) * force
                dy_sum += (dy/dist_) * force
            disp[u] = (disp[u][0]+dx_sum, disp[u][1]+dy_sum)

        # Attraction along edges (both directions for directed graph)
        for (i, j, score) in edges:
            dx = pos[i][0] - pos[j][0]
            dy = pos[i][1] - pos[j][1]
            dist_ = math.hypot(dx, dy) or 0.001
            force  = dist_*dist_ / k
            fx, fy = (dx/dist_)*force, (dy/dist_)*force
            disp[i] = (disp[i][0]-fx, disp[i][1]-fy)
            disp[j] = (disp[j][0]+fx, disp[j][1]+fy)

        # Apply displacements with temperature cap
        new_pos = []
        for u in range(n):
            dx, dy  = disp[u]
            dist_   = math.hypot(dx, dy) or 0.001
            capped  = min(dist_, temp)
            nx = pos[u][0] + (dx/dist_)*capped
            ny = pos[u][1] + (dy/dist_)*capped
            # Clamp to [0.05, 0.95]
            nx = max(0.05, min(0.95, nx))
            ny = max(0.05, min(0.95, ny))
            new_pos.append((nx, ny))
        pos = new_pos

    return pos


def _layout_spectral(n: int, weights: Dict, **kwargs) -> List[Tuple[float, float]]:
    """
    Spectral layout using the two smallest non-trivial eigenvectors
    of the graph Laplacian. Falls back to circular for n < 3.
    """
    if n < 3:
        return _layout_circular(n)

    try:
        import numpy as np
    except ImportError:
        return _layout_force_directed(n, **kwargs)

    # Build symmetric adjacency (undirected, |score| as weight)
    A = np.zeros((n, n))
    for (i, j), s in weights.items():
        A[i, j] += abs(s)
        A[j, i] += abs(s)

    # Laplacian L = D - A
    D = np.diag(A.sum(axis=1))
    L = D - A

    # Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    # Use eigenvectors 1 and 2 (skip 0 which is constant)
    idx = np.argsort(eigenvalues)
    v1  = eigenvectors[:, idx[1]]
    v2  = eigenvectors[:, idx[2]] if n > 2 else np.zeros(n)

    # Normalise to [0.05, 0.95]
    def norm(v):
        mn, mx = v.min(), v.max()
        if mx == mn: return np.full(n, 0.5)
        return 0.05 + 0.9 * (v - mn) / (mx - mn)

    x = norm(v1)
    y = norm(v2)
    return [(float(x[i]), float(y[i])) for i in range(n)]


def _layout_shell(n: int, centrality_rows: List[dict],
                  weights: Dict, **kwargs) -> List[Tuple[float, float]]:
    """
    Shell layout: nodes sorted by betweenness centrality.
    Top 1/3 (most central) in inner ring, rest in outer ring.
    Isolated nodes placed in a separate outermost band.
    """
    if n == 1:
        return [(0.5, 0.5)]

    # Identify isolated nodes
    connected_set = set()
    for (i, j) in weights:
        connected_set.add(i); connected_set.add(j)
    isolated = [i for i in range(n) if i not in connected_set]
    connected = [i for i in range(n) if i in connected_set]

    # Sort connected by betweenness (high → inner)
    btw_map = {r["code"]: r["betweenness"] for r in centrality_rows}
    # Map back by index
    btw_by_idx = {}
    for r in centrality_rows:
        for i in range(n):
            pass   # build below

    # centrality_rows has codes; match to index
    code_to_idx = {}

    # We need the result object; pass via kwargs
    result = kwargs.get("result")
    if result:
        code_to_idx = {code: i for i, code in enumerate(result.codes)}

    connected_sorted = sorted(
        connected,
        key=lambda i: btw_map.get(
            result.codes[i] if result else "", 0.0),
        reverse=True
    )

    split    = max(1, len(connected_sorted) // 3)
    inner    = connected_sorted[:split]
    outer    = connected_sorted[split:]

    pos = [None] * n

    def ring(nodes, radius):
        m = len(nodes)
        for k, idx_ in enumerate(nodes):
            angle = 2*math.pi*k/m - math.pi/2 if m > 1 else 0
            pos[idx_] = (0.5 + radius*math.cos(angle),
                         0.5 + radius*math.sin(angle))

    ring(inner,   0.20)
    ring(outer,   0.40)
    ring(isolated, 0.48)

    # Fill any None (shouldn't happen)
    for i in range(n):
        if pos[i] is None:
            pos[i] = (0.5, 0.5)

    return pos


def _compute_layout(layout_name: str, n: int, graph: Dict,
                    centrality_rows: List, result) -> List[Tuple[float, float]]:
    """Dispatch to the correct layout algorithm."""
    edges   = graph["edges"]
    weights = graph["weights"]
    if layout_name == "Circular":
        return _layout_circular(n)
    elif layout_name == "Force-Directed":
        return _layout_force_directed(n, edges=edges)
    elif layout_name == "Spectral":
        return _layout_spectral(n, weights=weights, edges=edges)
    elif layout_name == "Shell":
        return _layout_shell(n, centrality_rows=centrality_rows,
                             weights=weights, edges=edges, result=result)
    return _layout_circular(n)


# =============================================================================
# NetworkTab
# =============================================================================

class NetworkTab(tk.Frame):

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result       = result
        self._graph        = _build_graph(result)
        self._centrality   = compute_centrality(result)
        self._layout_var   = tk.StringVar(value="Force-Directed")
        self._tooltip_win: Optional[tk.Toplevel] = None
        self._node_pos     = []
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)

        pane = tk.PanedWindow(self, orient="horizontal",
                              bg=COLOR_BG, sashwidth=6,
                              sashrelief="flat", sashpad=2)
        pane.pack(fill="both", expand=True, padx=8, pady=8)

        net_frame    = tk.Frame(pane, bg=COLOR_BG)
        report_frame = tk.Frame(pane, bg=COLOR_BG)
        pane.add(net_frame,    minsize=320, stretch="always")
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

        tk.Label(bar,
                 text=f"Network Analysis  —  {method_label}",
                 font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_ACCENT,
                 ).pack(side="left", padx=16)

        n_nodes  = self._result.n
        n_edges  = len(self._graph["edges"])
        max_edges = n_nodes * (n_nodes-1) if n_nodes > 1 else 1
        density   = round(n_edges / max_edges, 3)
        isolated  = sum(
            1 for i in range(n_nodes)
            if not any(k[0] == i or k[1] == i
                       for k in self._graph["weights"])
        )
        stats = (f"{n_nodes} nodes  |  {n_edges} directed edges  "
                 f"|  density: {density}"
                 + (f"  |  {isolated} isolated" if isolated else ""))
        tk.Label(bar, text=stats,
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
                 ).pack(side="left", padx=6)

    # ------------------------------------------------------------------

    def _build_network(self, parent: tk.Frame):
        # Controls row: layout selector + legend
        ctrl = tk.Frame(parent, bg=COLOR_BG)
        ctrl.pack(fill="x", padx=8, pady=(4, 2))

        tk.Label(ctrl, text="Layout:",
                 font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT,
                 ).pack(side="left", padx=(0, 6))

        layout_cb = ttk.Combobox(
            ctrl, textvariable=self._layout_var,
            values=LAYOUTS, state="readonly", width=16,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        )
        layout_cb.pack(side="left", padx=(0, 20))
        layout_cb.bind("<<ComboboxSelected>>",
                       lambda e: self._redraw_network())

        for color, label in [(_COLOR_POS, "Positive"),
                              (_COLOR_NEG, "Negative"),
                              (_COLOR_ISOLATE, "Isolated")]:
            tk.Label(ctrl, text="━━", fg=color, bg=COLOR_BG,
                     font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                     ).pack(side="left", padx=(0, 2))
            tk.Label(ctrl, text=label, fg=COLOR_TEXT_LIGHT, bg=COLOR_BG,
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     ).pack(side="left", padx=(0, 10))

        # Canvas
        self._canvas = tk.Canvas(parent, bg="#ffffff",
                                 highlightthickness=2,
                                 highlightbackground=COLOR_ACCENT)
        self._canvas.pack(fill="both", expand=True, padx=8, pady=(2, 4))
        self._canvas.bind("<Configure>", lambda e: self._redraw_network())

        # Save button
        save_row = tk.Frame(parent, bg=COLOR_BG)
        save_row.pack(anchor="e", padx=8, pady=(2, 6))
        tk.Button(save_row, text="Save as PNG",
                  command=self._save_network,
                  font=(FONT_FAMILY, FONT_SIZE_SMALL),
                  bg=COLOR_PANEL, fg=COLOR_ACCENT,
                  relief="flat", padx=8, pady=3, cursor="hand2",
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

        # Compute layout in normalised [0,1] space
        norm_pos = _compute_layout(
            self._layout_var.get(), n, self._graph,
            self._centrality, self._result
        )

        # Scale to canvas with margin
        m = _MARGIN
        node_pos = [
            (m + x * (w - 2*m), m + y * (h - 2*m))
            for (x, y) in norm_pos
        ]
        self._node_pos = node_pos

        # Isolated nodes
        connected = set()
        for (i, j, _) in edges:
            connected.add(i); connected.add(j)

        # ---- Edges ----
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
            side = drawn_pairs[key]

            if bidirectional:
                dx, dy  = x2 - x1, y2 - y1
                length  = math.hypot(dx, dy) or 1
                ox = -dy/length * _EDGE_OFFSET
                oy =  dx/length * _EDGE_OFFSET
                sign = 1 if side == 1 else -1
                mx1, my1 = x1 + sign*ox, y1 + sign*oy
                mx2, my2 = x2 + sign*ox, y2 + sign*oy
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

        # ---- Nodes ----
        nr = _NODE_RADIUS
        for i, (nx_, ny_) in enumerate(node_pos):
            is_isolated = i not in connected
            fill  = _COLOR_ISOLATE if is_isolated else _COLOR_NODE
            oval  = canvas.create_oval(
                nx_-nr, ny_-nr, nx_+nr, ny_+nr,
                fill=fill, outline="#ffffff", width=1.5,
            )
            canvas.create_text(nx_, ny_,
                               text=codes[i],
                               font=(FONT_FAMILY, FONT_SIZE_SMALL-1, "bold"),
                               fill="#ffffff")
            full_name = policies[i]
            canvas.tag_bind(oval, "<Enter>",
                lambda e, c=codes[i], p=full_name:
                    self._show_tooltip(e, f"{c}:  {p}"))
            canvas.tag_bind(oval, "<Leave>",
                lambda e: self._hide_tooltip())

    # ------------------------------------------------------------------

    def _build_report(self, parent: tk.Frame):
        tk.Label(parent, text="Centrality Measures",
                 font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                 bg=COLOR_BG, fg=COLOR_ACCENT,
                 ).pack(anchor="w", padx=8, pady=(4, 2))
        tk.Label(parent,
                 text="Betweenness: broker role  |  Closeness: reachability",
                 font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
                 bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
                 ).pack(anchor="w", padx=8, pady=(0, 6))

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
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._draw_report(inner)

    # ------------------------------------------------------------------

    def _draw_report(self, frame: tk.Frame):
        pad     = 2
        headers = ["Policy", "Betweenness", "Closeness", "Full Name"]
        widths  = [6, 13, 10, 20]

        for col, (hdr, w) in enumerate(zip(headers, widths)):
            tk.Label(frame, text=hdr, width=w,
                     font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                     bg=COLOR_ACCENT, fg="#ffffff",
                     relief="flat", padx=6, pady=6, anchor="center",
                     ).grid(row=0, column=col, padx=pad,
                            pady=(6, pad), sticky="nsew")

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

    def _save_network(self):
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
                mb.showinfo("Saved",
                            f"Saved as PostScript:\n{path}\n\n"
                            "Convert with Ghostscript or open in a PS viewer.")
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

    # ------------------------------------------------------------------

    def _show_tooltip(self, event, text: str):
        self._hide_tooltip()
        x = event.widget.winfo_rootx() + event.x + 14
        y = event.widget.winfo_rooty() + event.y + 14
        tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=text, justify="left",
                 background="#fffbe6", foreground="#1e1e1e",
                 relief="solid", borderwidth=1,
                 font=(FONT_FAMILY, FONT_SIZE_SMALL),
                 padx=8, pady=4).pack()
        self._tooltip_win = tw

    def _hide_tooltip(self):
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None
