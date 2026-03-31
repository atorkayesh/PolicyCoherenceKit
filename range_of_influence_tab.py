# =============================================================================
# Policy Coherence Kit -- range_of_influence_tab.py
# RangeOfInfluenceTab: Shannon entropy of outgoing influence per policy.
#
# For each policy Pi:
#   1. Take non-zero outgoing scores from row i (absolute values)
#   2. Normalise to probabilities: pj = |sj| / sum(|sj|)
#   3. Shannon entropy: H(i) = -sum(pj * log2(pj))
#   4. Categorise using equal-band thresholds based on log2(n-1):
#        Low          : 0     <= H < 0.25 * Hmax
#        Low2Medium   : 0.25  <= H < 0.50 * Hmax
#        Medium2High  : 0.50  <= H < 0.75 * Hmax
#        High         : 0.75  <= H
#   If all outgoing scores are zero -> H = 0, category = "Low"
# =============================================================================

import math
import tkinter as tk
import tkinter.font as tkfont
from typing import List, Tuple

from aggregator import AggregationResult
from aggregation_tab import _PillScrollbar
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_PAGE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_PAGE_TITLE,
)
from theme import (
    COHERENCE_SCORES_TABLE_PADX,
    COHERENCE_SCORES_TABLE_PADY_BOTTOM,
    COHERENCE_SCORES_TABLE_SCROLL_GAP,
    COHERENCE_SCORES_SCROLL_STEP,
    COHERENCE_SCORES_SCROLL_DECAY,
    COHERENCE_SCORES_SCROLL_CUTOFF,
    COHERENCE_SCORES_SCROLL_FRAME_MS,
    COHERENCE_SCORES_POLICY_COL_MIN,
    COHERENCE_SCORES_WOI_COL_MIN,
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

# Category colours
_CAT_COLORS = {
    "Low":          ("#a3a3a3", "#ffffff"),
    "Low2Medium":   ("#a7f3d0", "#2d2d2d"),
    "Medium2High":  ("#34d399", "#ffffff"),
    "High":         ("#059669", "#ffffff"),
}

_CATEGORIES = ["Low", "Low2Medium", "Medium2High", "High"]


def _round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# =============================================================================
# Entropy calculation
# =============================================================================

def compute_entropy(result: AggregationResult) -> List[dict]:
    """
    Compute Shannon entropy of outgoing influence for every policy.
    Returns a list of dicts (one per policy).
    Results are cached in result._cached_entropy for reuse.
    """
    # Return cached result if available
    if result._cached_entropy is not None:
        return result._cached_entropy

    n      = result.n
    scores = result.scores

    # Maximum possible entropy for this matrix size
    hmax = math.log2(n - 1) if n > 2 else (1.0 if n == 2 else 0.0)

    rows = []
    for i in range(n):
        # Collect absolute non-zero outgoing values
        abs_vals = [
            abs(scores.get((i, j), 0.0) or 0.0)
            for j in range(n)
            if j != i and (scores.get((i, j), 0.0) or 0.0) != 0.0
        ]

        if not abs_vals or sum(abs_vals) == 0.0:
            entropy  = 0.0
            category = "Low"
        else:
            total = sum(abs_vals)
            probs = [v / total for v in abs_vals]
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)
            entropy = round(entropy, 4)
            category = _categorise(entropy, hmax)

        rows.append({
            "code":     result.codes[i],
            "policy":   result.policies[i],
            "entropy":  entropy,
            "category": category,
            "hmax":     round(hmax, 4),
        })

    # Cache the result
    result._cached_entropy = rows
    return rows


def _categorise(h: float, hmax: float) -> str:
    """Map an entropy value to one of the four category labels."""
    if hmax == 0.0:
        return "Low"
    ratio = h / hmax
    if ratio < 0.25:
        return "Low"
    if ratio < 0.50:
        return "Low2Medium"
    if ratio < 0.75:
        return "Medium2High"
    return "High"


# =============================================================================
# RangeOfInfluenceTab
# =============================================================================

class RangeOfInfluenceTab(tk.Frame):
    """
    Read-only tab showing Shannon entropy and influence category per policy.
    """

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result = result
        self._rows   = compute_entropy(result)
        self._scroll_canvas = None
        self._scroll_vy = 0.0
        self._scroll_anim = None
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        self._build_legend()
        tk.Frame(self, bg=TOPBAR_DIVIDER_COLOR, height=1).pack(fill="x", pady=4)
        self._build_table()

    # ------------------------------------------------------------------

    def _build_info_bar(self):
        bar = tk.Frame(self, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")
        content = tk.Frame(bar, bg=COLOR_BG)
        content.pack(anchor="w", padx=16)

        method_label = {
            "average":  "Average",
            "majority": "Majority Rule",
            "weighted": "Weighted",
        }.get(self._result.method, self._result.method.title())

        tk.Label(
            content,
            text=f"Range of Influence  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_PAGE_TITLE, "normal"),
            bg=COLOR_BG, fg=COLOR_PAGE_TITLE,
        ).pack(side="left")

        hmax = self._rows[0]["hmax"] if self._rows else 0.0
        tk.Label(
            content,
            text=f"max entropy = {hmax:.4f}",
            font=(FONT_FAMILY, 11, "italic"),
            bg=COLOR_BG, fg="#a3a3a3",
        ).pack(side="left", padx=(18, 0))

    # ------------------------------------------------------------------

    def _build_legend(self):
        leg = tk.Frame(self, bg=COLOR_BG)
        leg.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(
            leg,
            text="Entropy measures how evenly a policy distributes its "
                 "outgoing influence. High = spread across many policies. "
                 "Low = concentrated on few.",
            font=(FONT_FAMILY, 11, "italic"),
            bg=COLOR_BG, fg="#a3a3a3",
            wraplength=800, justify="left",
        ).pack(anchor="w", pady=(4, 14))

        cat_row = tk.Frame(leg, bg=COLOR_BG)
        cat_row.pack(fill="x", pady=(0, 4))

        tk.Label(
            cat_row,
            text="Categories:",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "normal"),
            bg=COLOR_BG, fg="#2c3b4e",
        ).grid(row=0, column=0, sticky="w", padx=(0, 16))

        thresholds = [
            ("Low",         "H < 25% of max"),
            ("Low2Medium",  "25% ≤ H < 50% of max"),
            ("Medium2High", "50% ≤ H < 75% of max"),
            ("High",        "H ≥ 75% of max"),
        ]
        cat_row.grid_columnconfigure(0, weight=0)
        for idx, (cat, desc) in enumerate(thresholds, start=1):
            cat_row.grid_columnconfigure(idx, weight=1, uniform="entropy-cats")
            item = tk.Frame(cat_row, bg=COLOR_BG)
            item.grid(row=0, column=idx, sticky="ew", padx=(0, 12 if idx < len(thresholds) else 0))

            bg, fg = _CAT_COLORS[cat]
            self._build_category_badge(item, cat, bg, fg).pack(side="left", padx=(0, 8))
            tk.Label(
                item,
                text=desc,
                font=(FONT_FAMILY, 10),
                bg=COLOR_BG, fg="#a3a3a3",
            ).pack(side="left")

    def _build_category_badge(self, parent: tk.Misc, text: str, bg: str, fg: str) -> tk.Canvas:
        font = tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE_SMALL, weight="bold")
        pad_x = 12
        width = font.measure(text) + (pad_x * 2)
        height = 25
        radius = 3

        badge = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=COLOR_BG,
            highlightthickness=0,
            bd=0,
        )
        _round_rect(badge, 0, 0, width, height, radius, fill=bg, outline=bg)
        badge.create_text(
            width / 2,
            height / 2,
            text=text,
            fill=fg,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
        )
        return badge

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
        pad = COHERENCE_SCORES_TABLE_CELL_GAP
        col_widths = [10, 10, 14]
        col_weights = [1, 1, 1, 4]
        col_mins = [
            COHERENCE_SCORES_POLICY_COL_MIN,
            COHERENCE_SCORES_WOI_COL_MIN,
            COHERENCE_SCORES_WOI_COL_MIN,
            COHERENCE_SCORES_FULL_NAME_COL_MIN,
        ]

        for col, (weight, minsize) in enumerate(zip(col_weights, col_mins)):
            frame.grid_columnconfigure(col, weight=weight, minsize=minsize)

        headers = [
            ("Policy", "Policy code"),
            ("Entropy", "Shannon entropy H (base 2)\n0 = fully concentrated\nlog2(n-1) = perfectly distributed"),
            ("Category", "Influence distribution category\nbased on fraction of max entropy"),
        ]

        for col, ((hdr, tip), width) in enumerate(zip(headers, col_widths)):
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
            lbl.configure(width=width)
            lbl.grid(row=0, column=col, padx=pad, pady=(8, pad), sticky="nsew")
            _Tooltip(lbl, tip)

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
        ).grid(row=0, column=3, padx=pad, pady=(8, pad), sticky="nsew")

        for r, row in enumerate(self._rows):
            bg_row = COHERENCE_SCORES_TABLE_ROW_EVEN_BG if r % 2 == 0 else COHERENCE_SCORES_TABLE_ROW_ODD_BG
            frame.grid_rowconfigure(r + 1, weight=0)

            tk.Label(
                frame,
                text=row["code"],
                width=col_widths[0],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                bg=bg_row, fg=COHERENCE_SCORES_TABLE_POLICY_FG,
                relief="flat", bd=0,
                padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=0, padx=pad, pady=pad, sticky="nsew")

            tk.Label(
                frame,
                text=f"{row['entropy']:.4f}",
                width=col_widths[1],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=bg_row, fg=COHERENCE_SCORES_TABLE_BODY_FG,
                relief="flat", bd=0,
                padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=1, padx=pad, pady=pad, sticky="nsew")

            cat_bg, cat_fg = _CAT_COLORS[row["category"]]
            tk.Label(
                frame,
                text=row["category"],
                width=col_widths[2],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                bg=cat_bg, fg=cat_fg,
                relief="flat", bd=0,
                padx=8, pady=COHERENCE_SCORES_TABLE_BODY_PADY,
                anchor="center",
                highlightthickness=1,
                highlightbackground=COHERENCE_SCORES_TABLE_BORDER,
                highlightcolor=COHERENCE_SCORES_TABLE_BORDER,
            ).grid(row=r + 1, column=2, padx=pad, pady=pad, sticky="nsew")

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
            ).grid(row=r + 1, column=3, padx=pad, pady=pad, sticky="nsew")


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
