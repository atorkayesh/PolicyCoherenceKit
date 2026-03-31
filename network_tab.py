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
import tkinter.font as tkFont
from typing import List, Dict, Tuple, Optional

from aggregator import AggregationResult
from aggregation_tab import _PillScrollbar
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_PAGE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_PAGE_TITLE,
    CURSOR_HAND,
)
from theme import (
    TOPBAR_EXCEL_BG,
    TOPBAR_EXCEL_HOVER_BG,
    TOPBAR_EXCEL_BORDER,
    TOPBAR_EXCEL_FG,
    TOPBAR_EXCEL_HEIGHT,
    TOPBAR_EXCEL_RADIUS,
    TOPBAR_EXCEL_ICON_SIZE,
    TOPBAR_EXCEL_ICON_GAP,
    TOPBAR_EXCEL_PADX,
    COHERENCE_SCORES_TABLE_SCROLL_GAP,
    COHERENCE_SCORES_TABLE_CELL_GAP,
    COHERENCE_SCORES_TABLE_HEADER_BG,
    COHERENCE_SCORES_TABLE_HEADER_FG,
    COHERENCE_SCORES_TABLE_HEADER_PADY,
    COHERENCE_SCORES_TABLE_HEADER_SIZE,
    COHERENCE_SCORES_TABLE_ROW_EVEN_BG,
    COHERENCE_SCORES_TABLE_ROW_ODD_BG,
    COHERENCE_SCORES_TABLE_BODY_FG,
    COHERENCE_SCORES_TABLE_POLICY_FG,
    COHERENCE_SCORES_TABLE_BODY_PADY,
    COHERENCE_SCORES_TABLE_BORDER,
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


def _rrect_pts(x1, y1, x2, y2, r, steps=10):
    pts = []
    for cx, cy, a0 in [
        (x2 - r, y1 + r, -90),
        (x2 - r, y2 - r, 0),
        (x1 + r, y2 - r, 90),
        (x1 + r, y1 + r, 180),
    ]:
        for i in range(steps + 1):
            a = math.radians(a0 + 90 * i / steps)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts

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
        self._selector_popup = None
        self._selector_close_fn = None
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()

        content = tk.Frame(self, bg=COLOR_BG)
        content.pack(fill="both", expand=True, padx=8, pady=8)
        content.grid_columnconfigure(0, weight=2, uniform="network-layout")
        content.grid_columnconfigure(1, weight=1, uniform="network-layout")
        content.grid_rowconfigure(0, weight=1)

        net_frame = tk.Frame(content, bg=COLOR_BG)
        report_frame = tk.Frame(content, bg=COLOR_BG)
        net_frame.grid(row=0, column=0, sticky="nsew")
        report_frame.grid(row=0, column=1, sticky="nsew")

        self._build_network(net_frame)
        self._build_report(report_frame)

    def _build_info_bar(self):
        bar = tk.Frame(self, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_columnconfigure(1, weight=0)
        content = tk.Frame(bar, bg=COLOR_BG)
        content.grid(row=0, column=0, sticky="w", padx=16)

        method_label = {
            "average":  "Average",
            "majority": "Majority Rule",
            "weighted": "Weighted",
        }.get(self._result.method, self._result.method.title())

        tk.Label(
            content,
            text=f"Network Analysis  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_PAGE_TITLE, "normal"),
            bg=COLOR_BG, fg=COLOR_PAGE_TITLE,
        ).pack(side="left")

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
            content,
            text=stats_txt,
            font=(FONT_FAMILY, 11, "italic"),
            bg=COLOR_BG, fg="#a3a3a3",
        ).pack(side="left", padx=(18, 0))

        self._build_save_button(bar, layout="grid", padx=16)

    # ------------------------------------------------------------------

    def _build_network(self, parent: tk.Frame):
        # ---- Controls row ----
        ctrl = tk.Frame(parent, bg=COLOR_BG)
        ctrl.pack(fill="x", padx=8, pady=(4, 2))

        # Layout selector
        tk.Label(ctrl, text="Layout:",
                 font=(FONT_FAMILY, 10, "normal"),
                 bg=COLOR_BG, fg="#a3a3a3",
                 ).pack(side="left", padx=(0, 4))
        self._layout_selector = self._build_selector_field(
            ctrl,
            variable=self._layout_var,
            options=LAYOUTS,
            width=108,
            on_pick=lambda _value: self._on_view_change(),
        )
        self._layout_selector.pack(side="left", padx=(0, 16))

        # Ego policy selector
        tk.Label(ctrl, text="Focus Policy:",
                 font=(FONT_FAMILY, 10, "normal"),
                 bg=COLOR_BG, fg="#a3a3a3",
                 ).pack(side="left", padx=(0, 4))
        ego_options = ["Full Network"] + [
            f"{c}: {p}" for c, p in zip(
                self._result.codes, self._result.policies)
        ]
        self._ego_selector = self._build_selector_field(
            ctrl,
            variable=self._ego_var,
            options=ego_options,
            width=176,
            on_pick=lambda _value: self._on_view_change(),
        )
        self._ego_selector.pack(side="left", padx=(0, 16))

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

    def _build_selector_field(self, parent: tk.Misc, variable: tk.StringVar, options: List[str], width: int, on_pick):
        field = tk.Canvas(
            parent,
            width=width,
            height=30,
            bg=COLOR_BG,
            highlightthickness=0,
            cursor=CURSOR_HAND,
        )
        self._draw_selector_field(field, variable.get(), active=False)

        def _open(_event=None):
            self._open_selector_popup(field, variable, options, on_pick)
            return "break"

        field.bind("<Button-1>", _open)

        variable.trace_add("write", lambda *_args, c=field, v=variable: self._draw_selector_field(c, v.get(), active=False))
        return field

    def _draw_selector_field(self, canvas: tk.Canvas, text: str, active: bool):
        canvas.delete("all")
        width = int(canvas.cget("width"))
        height = int(canvas.cget("height"))
        outline = "#426387" if active else "#d3d3d3"
        pts = _rrect_pts(1, 1, width - 1, height - 1, 4)
        canvas.create_polygon(*pts, fill="#ffffff", outline=outline, width=1)
        canvas.create_text(
            10,
            height / 2,
            text=text,
            font=(FONT_FAMILY, 10),
            fill=COLOR_TEXT,
            anchor="w",
        )
        cx = width - 16
        cy = height / 2
        canvas.create_line(cx - 4, cy - 2, cx, cy + 2, fill="#a3a3a3", width=1.35, capstyle="round", joinstyle="round")
        canvas.create_line(cx, cy + 2, cx + 4, cy - 2, fill="#a3a3a3", width=1.35, capstyle="round", joinstyle="round")

    def _open_selector_popup(self, field: tk.Canvas, variable: tk.StringVar, options: List[str], on_pick):
        if self._selector_popup is not None:
            self._close_selector_popup()

        width = field.winfo_width()
        item_h = 34
        pad = 1
        visible = min(9, len(options))
        popup_h = visible * item_h + pad * 2

        field_x = field.winfo_rootx()
        field_y = field.winfo_rooty()
        field_h = field.winfo_height()
        screen_h = self.winfo_screenheight()
        popup_y = field_y + field_h + 4
        if popup_y + popup_h > screen_h - 20:
            popup_y = field_y - popup_h - 4

        self._draw_selector_field(field, variable.get(), active=True)

        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True)
        popup.configure(bg="#e0e0e0")
        popup.wm_geometry(f"{width}x{popup_h}+{field_x}+{popup_y}")

        shell = tk.Frame(popup, bg="#e0e0e0")
        shell.place(x=0, y=0, relwidth=1, relheight=1)

        canvas = tk.Canvas(shell, bg="#ffffff", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True, padx=(pad, 0), pady=pad)

        inner = tk.Frame(canvas, bg="#ffffff")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))

        needs_scroll = len(options) > visible
        if needs_scroll:
            scrollbar = _PillScrollbar(shell, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y", padx=(6, pad), pady=pad)

        for idx, option in enumerate(options):
            item = tk.Label(
                inner,
                text=option,
                bg="#ffffff",
                fg=COLOR_TEXT,
                font=(FONT_FAMILY, 10),
                anchor="w",
                padx=12,
            )
            item.place(x=0, y=idx * item_h, relwidth=1, height=item_h)

            def _enter(_e, w=item):
                w.configure(bg="#f0f4f8")

            def _leave(_e, w=item):
                w.configure(bg="#ffffff")

            def _choose(_e, value=option):
                variable.set(value)
                on_pick(value)
                self._close_selector_popup()

            item.bind("<Enter>", _enter)
            item.bind("<Leave>", _leave)
            item.bind("<Button-1>", _choose)

        inner.configure(height=len(options) * item_h)

        def _wheel(event):
            delta = getattr(event, "delta", 0)
            if delta:
                canvas.yview_scroll(int(-1 * (delta / 120)), "units")
                return "break"

        popup.bind("<MouseWheel>", _wheel)
        popup.bind("<Button-4>", lambda _e: (canvas.yview_scroll(-1, "units"), "break"))
        popup.bind("<Button-5>", lambda _e: (canvas.yview_scroll(1, "units"), "break"))

        root = self.winfo_toplevel()
        bind_id = [None]

        def _close(_event=None):
            if bind_id[0]:
                root.unbind("<Button-1>", bind_id[0])
                bind_id[0] = None
            self._draw_selector_field(field, variable.get(), active=False)
            try:
                popup.destroy()
            except Exception:
                pass
            self._selector_popup = None
            self._selector_close_fn = None

        self._selector_popup = popup
        self._selector_close_fn = _close
        bind_id[0] = root.bind("<Button-1>", lambda _e: _close(), "+")
        popup.bind("<Escape>", _close)

    def _close_selector_popup(self):
        if self._selector_close_fn is not None:
            self._selector_close_fn()

    def _build_save_button(self, parent: tk.Misc, layout: str = "pack", padx: int = 0):
        label = "Save as PNG"
        btn_font = tkFont.Font(family=FONT_FAMILY, size=11)
        text_w = btn_font.measure(label)
        btn_w = TOPBAR_EXCEL_PADX + TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP + text_w + TOPBAR_EXCEL_PADX

        btn = tk.Canvas(
            parent,
            width=btn_w + 2,
            height=TOPBAR_EXCEL_HEIGHT + 2,
            bg=COLOR_BG,
            highlightthickness=0,
            cursor=CURSOR_HAND,
        )
        if layout == "grid":
            btn.grid(row=0, column=1, sticky="e", padx=padx)
        else:
            btn.pack(side="right", padx=padx)

        hover = {"value": 0.0, "job": None}

        def _draw(color: str):
            btn.delete("all")
            pts = _rrect_pts(1, 1, btn_w + 1, TOPBAR_EXCEL_HEIGHT + 1, TOPBAR_EXCEL_RADIUS)
            btn.create_polygon(*pts, fill=color, outline=TOPBAR_EXCEL_BORDER, width=1)
            cy = 1 + TOPBAR_EXCEL_HEIGHT // 2
            content_w = TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP + text_w
            ix = 1 + (btn_w - content_w) // 2
            iy = 1 + (TOPBAR_EXCEL_HEIGHT - TOPBAR_EXCEL_ICON_SIZE) // 2
            self._draw_image_down_icon(btn, ix, iy, TOPBAR_EXCEL_FG)
            btn.create_text(
                ix + TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP,
                cy,
                text=label,
                fill=TOPBAR_EXCEL_FG,
                anchor="w",
                font=btn_font,
            )

        def _animate(target: float):
            if hover["job"]:
                btn.after_cancel(hover["job"])
                hover["job"] = None

            def _tick():
                diff = target - hover["value"]
                if abs(diff) < 0.02:
                    hover["value"] = target
                    _draw(TOPBAR_EXCEL_HOVER_BG if target else TOPBAR_EXCEL_BG)
                    hover["job"] = None
                    return
                hover["value"] += diff * 0.3
                mix = TOPBAR_EXCEL_HOVER_BG if hover["value"] >= 0.5 else TOPBAR_EXCEL_BG
                _draw(mix)
                hover["job"] = btn.after(16, _tick)

            _tick()

        btn.bind("<Enter>", lambda _e: _animate(1.0))
        btn.bind("<Leave>", lambda _e: _animate(0.0))
        btn.bind("<Button-1>", lambda _e: self._save_network())
        _draw(TOPBAR_EXCEL_BG)

    def _draw_image_down_icon(self, canvas: tk.Canvas, ox: int, oy: int, fg: str):
        s = TOPBAR_EXCEL_ICON_SIZE / 24.0
        lw = 1.35
        kw = dict(fill=fg, width=lw, capstyle="round", joinstyle="round")
        canvas.create_line(
            10.3*s+ox, 21*s+oy, 5*s+ox, 21*s+oy,
            3*s+ox, 19*s+oy, 3*s+ox, 5*s+oy,
            5*s+ox, 3*s+oy, 19*s+ox, 3*s+oy,
            21*s+ox, 5*s+oy, 21*s+ox, 15*s+oy,
            **kw,
        )
        canvas.create_line(
            21*s+ox, 15*s+oy, 17.9*s+ox, 11.9*s+oy,
            15.086*s+ox, 11.914*s+oy, 6*s+ox, 21*s+oy,
            **kw,
        )
        canvas.create_line(17*s+ox, 16.5*s+oy, 17*s+ox, 22*s+oy, **kw)
        canvas.create_line(14*s+ox, 19*s+oy, 17*s+ox, 22*s+oy, 20*s+ox, 19*s+oy, **kw)
        canvas.create_oval(7*s+ox, 7*s+oy, 11*s+ox, 11*s+oy, outline=fg, width=lw)

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
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(
            parent,
            text="Centrality Measures",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(4, 2))

        tk.Label(
            parent,
            text="Betweenness: broker role  |  Closeness: reachability",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG, fg="#808080",
        ).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 6))

        shell = tk.Frame(parent, bg=COLOR_BG)
        shell.grid(row=2, column=0, sticky="nsew")
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(shell, bg=COLOR_BG, highlightthickness=0)
        self._report_canvas = canvas
        v_scroll = _PillScrollbar(shell, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns", padx=(COHERENCE_SCORES_TABLE_SCROLL_GAP, 0))

        canvas.bind("<Configure>", lambda _e: self._draw_report())
        self._bind_report_scroll(canvas)
        self._draw_report()

    # ------------------------------------------------------------------

    def _bind_report_scroll(self, canvas: tk.Canvas):
        def _wheel(event):
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return
            units = delta if abs(delta) < 40 else delta / 120.0
            amount = max(1, int(abs(units)))
            canvas.yview_scroll(-amount if units > 0 else amount, "units")
            return "break"

        def _wheel_up(_event):
            canvas.yview_scroll(-1, "units")
            return "break"

        def _wheel_down(_event):
            canvas.yview_scroll(1, "units")
            return "break"

        canvas.bind("<MouseWheel>", _wheel)
        canvas.bind("<Button-4>", _wheel_up)
        canvas.bind("<Button-5>", _wheel_down)

    # ------------------------------------------------------------------

    def _draw_report(self):
        canvas = getattr(self, "_report_canvas", None)
        if canvas is None:
            return
        width = canvas.winfo_width()
        if width <= 1:
            return

        canvas.delete("all")

        pad = COHERENCE_SCORES_TABLE_CELL_GAP
        header_h = 34
        row_h = 34
        min_widths = [88, 122, 112, 240]
        weights = [1, 1, 1, 3]
        inner_w = max(width, sum(min_widths) + pad * 5)
        extra = max(0, inner_w - sum(min_widths) - pad * 5)
        total_weight = sum(weights)
        col_widths = [
            min_widths[i] + int(extra * weights[i] / total_weight)
            for i in range(len(min_widths))
        ]
        col_widths[-1] += inner_w - (sum(col_widths) + pad * 5)

        headers = ["Policy", "Betweenness", "Closeness", "Full Name"]
        rows = sorted(self._centrality, key=lambda r: r["betweenness"], reverse=True)
        total_h = pad + header_h + pad + len(rows) * (row_h + pad)
        canvas.configure(scrollregion=(0, 0, inner_w, total_h))

        x = pad
        y = pad
        header_font = (FONT_FAMILY, COHERENCE_SCORES_TABLE_HEADER_SIZE, "normal")
        body_font = (FONT_FAMILY, FONT_SIZE_SMALL)
        policy_font = (FONT_FAMILY, FONT_SIZE_SMALL, "bold")

        for idx, (hdr, col_w) in enumerate(zip(headers, col_widths)):
            x2 = x + col_w
            canvas.create_rectangle(
                x, y, x2, y + header_h,
                fill=COHERENCE_SCORES_TABLE_HEADER_BG,
                outline=COHERENCE_SCORES_TABLE_BORDER,
                width=1,
            )
            anchor = "w" if idx == 3 else "center"
            text_x = x + 12 if idx == 3 else x + col_w / 2
            canvas.create_text(
                text_x, y + header_h / 2,
                text=hdr,
                font=header_font,
                fill=COHERENCE_SCORES_TABLE_HEADER_FG,
                anchor=anchor,
            )
            x = x2 + pad

        y += header_h + pad
        for r, row in enumerate(rows):
            bg = COHERENCE_SCORES_TABLE_ROW_EVEN_BG if r % 2 == 0 else COHERENCE_SCORES_TABLE_ROW_ODD_BG
            values = [
                (row["code"], policy_font, COHERENCE_SCORES_TABLE_POLICY_FG, "center"),
                (f"{row['betweenness']:.4f}", body_font, COHERENCE_SCORES_TABLE_BODY_FG, "center"),
                (f"{row['closeness']:.4f}", body_font, COHERENCE_SCORES_TABLE_BODY_FG, "center"),
                (row["policy"], body_font, COHERENCE_SCORES_TABLE_BODY_FG, "w"),
            ]
            x = pad
            for idx, ((text, font, fg, anchor), col_w) in enumerate(zip(values, col_widths)):
                x2 = x + col_w
                canvas.create_rectangle(
                    x, y, x2, y + row_h,
                    fill=bg,
                    outline=COHERENCE_SCORES_TABLE_BORDER,
                    width=1,
                )
                text_x = x + 12 if idx == 3 else x + col_w / 2
                canvas.create_text(
                    text_x, y + row_h / 2,
                    text=text,
                    font=font,
                    fill=fg,
                    anchor=anchor,
                )
                x = x2 + pad
            y += row_h + pad

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
