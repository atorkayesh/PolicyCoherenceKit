# =============================================================================
# Policy Coherence Kit -- coherence_scores_tab.py
# CoherenceScoresTab: read-only tab showing four influence scores per policy.
#
# For each policy Pi in the aggregated score matrix S (n x n, diagonal = 0):
#
#   Outgoing Influence (OI)   = count of non-zero cells in row i
#   Incoming Influence (II)   = count of non-zero cells in column i
#   Weighted Outgoing  (WOI)  = sum of values in row i    (excl. diagonal)
#   Weighted Incoming  (WII)  = sum of values in column i (excl. diagonal)
# =============================================================================

import tkinter as tk
from typing import List, Tuple

from aggregator import AggregationResult
from aggregation_tab import _PillScrollbar
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE, FONT_SIZE_PAGE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_PAGE_TITLE,
)
from theme import (
    COHERENCE_SCORES_METRIC_COLOR,
    COHERENCE_SCORES_METRIC_SIZE,
    COHERENCE_SCORES_DESC_COLOR,
    COHERENCE_SCORES_DESC_SIZE,
    COHERENCE_SCORES_LEGEND_TOP_PADY,
    COHERENCE_SCORES_LEGEND_PADX_LEFT,
    COHERENCE_SCORES_LEGEND_ROW_GAP,
    COHERENCE_SCORES_LEGEND_LABEL_WIDTH,
    COHERENCE_SCORES_LEGEND_TEXT_GAP,
    COHERENCE_SCORES_DIVIDER_PADY_TOP,
    COHERENCE_SCORES_DIVIDER_PADY_BOTTOM,
    COHERENCE_SCORES_TABLE_PADX,
    COHERENCE_SCORES_TABLE_PADY_BOTTOM,
    COHERENCE_SCORES_TABLE_SCROLL_GAP,
    COHERENCE_SCORES_SCROLL_STEP,
    COHERENCE_SCORES_SCROLL_DECAY,
    COHERENCE_SCORES_SCROLL_CUTOFF,
    COHERENCE_SCORES_SCROLL_FRAME_MS,
    COHERENCE_SCORES_POLICY_COL_MIN,
    COHERENCE_SCORES_OI_COL_MIN,
    COHERENCE_SCORES_II_COL_MIN,
    COHERENCE_SCORES_WOI_COL_MIN,
    COHERENCE_SCORES_WII_COL_MIN,
    COHERENCE_SCORES_FULL_NAME_COL_MIN,
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
    TOPBAR_DIVIDER_COLOR,
)

# Column definitions: (header, description, key)
_COLUMNS = [
    ("Policy",  "Policy code",                           "code"),
    ("OI",      "Outgoing Influence\n(non-zero row count)",  "oi"),
    ("II",      "Incoming Influence\n(non-zero col count)",  "ii"),
    ("WOI",     "Weighted Outgoing\n(row sum)",              "woi"),
    ("WII",     "Weighted Incoming\n(col sum)",              "wii"),
]

# Colour thresholds for WOI / WII (same green-grey-red palette)
def _value_color(val: float) -> Tuple[str, str]:
    """Return (bg, fg) for a numeric score cell."""
    if val > 1.5:
        return "#177e40", "#ffffff"
    if val > 0.5:
        return "#25c263", "#ffffff"
    if val > 0.0:
        return "#88edaf", "#2d2d2d"
    if val == 0.0:
        return "#d9d9d9", "#555555"
    if val >= -0.5:
        return "#f5c07a", "#2d2d2d"
    if val >= -1.5:
        return "#e07b39", "#ffffff"
    return "#ef4444", "#ffffff"

def _count_color(val: int, n: int) -> Tuple[str, str]:
    """Colour for OI / II based on fraction of total policies affected."""
    if n <= 1:
        return "#d9d9d9", "#555555"
    ratio = val / (n - 1)
    if ratio >= 0.75:
        return "#7799b9", "#ffffff"
    if ratio >= 0.5:
        return "#a6bcd3", "#1f2937"
    if ratio >= 0.25:
        return "#d0dbe7", "#1f2937"
    return "#eae7e0", "#666666"


# =============================================================================
# Score calculation
# =============================================================================

def compute_scores(result: AggregationResult) -> List[dict]:
    """
    Compute OI, II, WOI, WII for every policy in the result.
    Returns a list of dicts (one per policy), sorted by policy index.
    Results are cached in result._cached_scores for reuse.
    """
    # Return cached result if available
    if result._cached_scores is not None:
        return result._cached_scores

    n      = result.n
    scores = result.scores

    rows = []
    for i in range(n):
        oi  = sum(1   for j in range(n) if j != i
                  and scores.get((i, j), 0.0) not in (None, 0.0))
        ii  = sum(1   for j in range(n) if j != i
                  and scores.get((j, i), 0.0) not in (None, 0.0))
        woi = sum(scores.get((i, j), 0.0) or 0.0
                  for j in range(n) if j != i)
        wii = sum(scores.get((j, i), 0.0) or 0.0
                  for j in range(n) if j != i)

        rows.append({
            "code":   result.codes[i],
            "policy": result.policies[i],
            "oi":     oi,
            "ii":     ii,
            "woi":    round(woi, 2),
            "wii":    round(wii, 2),
        })

    # Cache the result
    result._cached_scores = rows
    return rows


# =============================================================================
# CoherenceScoresTab
# =============================================================================

class CoherenceScoresTab(tk.Frame):
    """
    Read-only tab displaying OI, II, WOI, WII for each policy.
    """

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result = result
        self._rows   = compute_scores(result)
        self._scroll_canvas = None
        self._scroll_vy = 0.0
        self._scroll_anim = None
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        self._build_legend()
        tk.Frame(self, bg=TOPBAR_DIVIDER_COLOR, height=1).pack(
            fill="x",
            padx=COHERENCE_SCORES_TABLE_PADX,
            pady=(COHERENCE_SCORES_DIVIDER_PADY_TOP, COHERENCE_SCORES_DIVIDER_PADY_BOTTOM),
        )
        self._build_table()

    # ------------------------------------------------------------------

    def _build_info_bar(self):
        bar = tk.Frame(self, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")

        method_label = {
            "average":  "Average",
            "majority": "Majority Rule",
            "weighted": "Weighted",
        }.get(self._result.method, self._result.method.title())

        tk.Label(
            bar,
            text=f"Coherence Scores  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_PAGE_TITLE, "normal"),
            bg=COLOR_BG, fg=COLOR_PAGE_TITLE,
        ).pack(side="left", padx=16)

    # ------------------------------------------------------------------

    def _build_legend(self):
        leg = tk.Frame(self, bg=COLOR_BG)
        leg.pack(fill="x", padx=(COHERENCE_SCORES_LEGEND_PADX_LEFT, COHERENCE_SCORES_TABLE_PADX), pady=(COHERENCE_SCORES_LEGEND_TOP_PADY, 0))

        items = [
            ("OI:",  "Outgoing Influence — number of policies this policy affects (non-zero row cells)"),
            ("II:",  "Incoming Influence — number of policies that affect this policy (non-zero col cells)"),
            ("WOI:", "Weighted Outgoing — sum of scores in the row (strength of influence exerted)"),
            ("WII:", "Weighted Incoming — sum of scores in the column (strength of influence received)"),
        ]
        for abbr, desc in items:
            row = tk.Frame(leg, bg=COLOR_BG)
            row.pack(anchor="w", pady=(0, COHERENCE_SCORES_LEGEND_ROW_GAP))
            tk.Label(
                row,
                text=abbr,
                font=(FONT_FAMILY, COHERENCE_SCORES_METRIC_SIZE, "normal"),
                bg=COLOR_BG, fg=COHERENCE_SCORES_METRIC_COLOR,
                width=COHERENCE_SCORES_LEGEND_LABEL_WIDTH,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                row,
                text=desc,
                font=(FONT_FAMILY, COHERENCE_SCORES_DESC_SIZE, "normal"),
                bg=COLOR_BG, fg=COHERENCE_SCORES_DESC_COLOR,
                anchor="w",
            ).pack(side="left", padx=(COHERENCE_SCORES_LEGEND_TEXT_GAP, 0))

    # ------------------------------------------------------------------

    def _build_table(self):
        shell = tk.Frame(self, bg=COLOR_BG)
        shell.pack(fill="both", expand=True, padx=COHERENCE_SCORES_TABLE_PADX, pady=(0, COHERENCE_SCORES_TABLE_PADY_BOTTOM))

        canvas = tk.Canvas(shell, bg=COLOR_BG, highlightthickness=0)
        self._scroll_canvas = canvas
        v_scroll = _PillScrollbar(shell, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns", padx=(COHERENCE_SCORES_TABLE_SCROLL_GAP, 0))

        inner = tk.Frame(canvas, bg=COLOR_BG)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(window_id, width=max(e.width, inner.winfo_reqwidth())),
        )
        self._draw_table(inner)
        self._bind_scroll_targets(canvas, inner)

    def _bind_scroll_targets(self, canvas: tk.Canvas, inner: tk.Frame):
        def _wheel(event):
            if getattr(event, "state", 0) & 0x1:
                return
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return
            units = delta if abs(delta) < 40 else delta / 120.0
            self._queue_scroll(-units * COHERENCE_SCORES_SCROLL_STEP)
            return "break"

        def _wheel_up(_event):
            self._queue_scroll(-COHERENCE_SCORES_SCROLL_STEP)
            return "break"

        def _wheel_down(_event):
            self._queue_scroll(COHERENCE_SCORES_SCROLL_STEP)
            return "break"

        def _bind_widget_tree(widget):
            widget.bind("<MouseWheel>", _wheel)
            widget.bind("<Button-4>", _wheel_up)
            widget.bind("<Button-5>", _wheel_down)
            for child in widget.winfo_children():
                _bind_widget_tree(child)

        _bind_widget_tree(canvas)
        _bind_widget_tree(inner)

    def _queue_scroll(self, delta: float):
        if not self._scroll_canvas:
            return
        self._scroll_vy += delta
        if self._scroll_anim is None:
            self._scroll_tick()

    def _scroll_tick(self):
        canvas = self._scroll_canvas
        if canvas is None:
            self._scroll_anim = None
            return
        self._scroll_vy *= COHERENCE_SCORES_SCROLL_DECAY
        if abs(self._scroll_vy) < COHERENCE_SCORES_SCROLL_CUTOFF:
            self._scroll_vy = 0.0
            self._scroll_anim = None
            return
        y1, y2 = canvas.yview()
        span = y2 - y1
        if span >= 1.0:
            self._scroll_vy = 0.0
            self._scroll_anim = None
            return
        next_y = max(0.0, min(1.0 - span, y1 + self._scroll_vy))
        if abs(next_y - y1) < 1e-6:
            self._scroll_vy = 0.0
            self._scroll_anim = None
            return
        canvas.yview_moveto(next_y)
        self._scroll_anim = canvas.after(COHERENCE_SCORES_SCROLL_FRAME_MS, self._scroll_tick)

    # ------------------------------------------------------------------

    def _draw_table(self, frame: tk.Frame):
        n   = self._result.n
        pad = COHERENCE_SCORES_TABLE_CELL_GAP

        col_widths = [10, 8, 8, 10, 10]
        headers = ["Policy", "OI", "II", "WOI", "WII"]
        full_names = [
            "Policy code",
            "Outgoing Influence\n(non-zero row count)",
            "Incoming Influence\n(non-zero col count)",
            "Weighted Outgoing\n(row sum)",
            "Weighted Incoming\n(col sum)",
        ]
        col_weights = [1, 1, 1, 1, 1, 4]
        col_mins = [
            COHERENCE_SCORES_POLICY_COL_MIN,
            COHERENCE_SCORES_OI_COL_MIN,
            COHERENCE_SCORES_II_COL_MIN,
            COHERENCE_SCORES_WOI_COL_MIN,
            COHERENCE_SCORES_WII_COL_MIN,
            COHERENCE_SCORES_FULL_NAME_COL_MIN,
        ]

        for col, (weight, minsize) in enumerate(zip(col_weights, col_mins)):
            frame.grid_columnconfigure(col, weight=weight, minsize=minsize)

        # ---- Header row ----
        for col, (hdr, width, full) in enumerate(zip(headers, col_widths, full_names)):
            lbl = tk.Label(
                frame,
                text=hdr,
                font=(FONT_FAMILY, COHERENCE_SCORES_TABLE_HEADER_SIZE, "bold"),
                bg=COHERENCE_SCORES_TABLE_HEADER_BG, fg=COHERENCE_SCORES_TABLE_HEADER_FG,
                relief="flat", bd=0, padx=8, pady=COHERENCE_SCORES_TABLE_HEADER_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            )
            if width:
                lbl.configure(width=width)
            lbl.grid(row=0, column=col, padx=pad, pady=(0, pad), sticky="nsew")
            _Tooltip(lbl, full)

        # ---- Full name column header ----
        tk.Label(
            frame,
            text="Full Policy Name",
            font=(FONT_FAMILY, COHERENCE_SCORES_TABLE_HEADER_SIZE, "bold"),
            bg=COHERENCE_SCORES_TABLE_HEADER_BG, fg=COHERENCE_SCORES_TABLE_HEADER_FG,
            relief="flat", bd=0, padx=12, pady=COHERENCE_SCORES_TABLE_HEADER_PADY,
            anchor="w",
            highlightthickness=1,
            highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
            highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
        ).grid(row=0, column=5, padx=pad, pady=(0, pad), sticky="nsew")

        # ---- Data rows ----
        for r, row in enumerate(self._rows):
            bg_row = COHERENCE_SCORES_TABLE_ROW_EVEN_BG if r % 2 == 0 else COHERENCE_SCORES_TABLE_ROW_ODD_BG
            frame.grid_rowconfigure(r + 1, weight=0)

            # Policy code
            tk.Label(
                frame,
                text=row["code"],
                width=col_widths[0],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                bg=bg_row, fg=COHERENCE_SCORES_TABLE_POLICY_FG,
                relief="flat", bd=0, padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=0, padx=pad, pady=pad, sticky="nsew")

            # OI
            oi_bg, oi_fg = _count_color(row["oi"], n)
            tk.Label(
                frame,
                text=str(row["oi"]),
                width=col_widths[1],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=oi_bg, fg=oi_fg,
                relief="flat", bd=0,
                padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=1, padx=pad, pady=pad, sticky="nsew")

            # II
            ii_bg, ii_fg = _count_color(row["ii"], n)
            tk.Label(
                frame,
                text=str(row["ii"]),
                width=col_widths[2],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=ii_bg, fg=ii_fg,
                relief="flat", bd=0,
                padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=2, padx=pad, pady=pad, sticky="nsew")

            # WOI
            woi_bg, woi_fg = _value_color(row["woi"])
            tk.Label(
                frame,
                text=f"{row['woi']:+.2f}",
                width=col_widths[3],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=woi_bg, fg=woi_fg,
                relief="flat", bd=0,
                padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=3, padx=pad, pady=pad, sticky="nsew")

            # WII
            wii_bg, wii_fg = _value_color(row["wii"])
            tk.Label(
                frame,
                text=f"{row['wii']:+.2f}",
                width=col_widths[4],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=wii_bg, fg=wii_fg,
                relief="flat", bd=0,
                padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=4, padx=pad, pady=pad, sticky="nsew")

            # Full policy name
            tk.Label(
                frame,
                text=row["policy"],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=bg_row, fg=COHERENCE_SCORES_TABLE_BODY_FG,
                relief="flat", bd=0,
                padx=14, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="w",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=5, padx=pad, pady=pad, sticky="nsew")


# =============================================================================
# Internal tooltip
# =============================================================================

class _Tooltip:
    def __init__(self, widget: tk.Widget, text: str):
        self._widget = widget
        self._text   = text
        self._win    = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, e=None):
        if self._win:
            return
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._win = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self._text, justify="left",
            background="#fffbe6", foreground="#1e1e1e",
            relief="solid", borderwidth=1,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            padx=8, pady=4, wraplength=320,
        ).pack()

    def _hide(self, e=None):
        if self._win:
            self._win.destroy()
            self._win = None
