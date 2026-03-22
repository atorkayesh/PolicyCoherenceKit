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
from tkinter import ttk
from typing import List, Tuple

from .aggregator import AggregationResult
from .constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
)

# Category colours
_CAT_COLORS = {
    "Low":          ("#d9d9d9", "#555555"),
    "Low2Medium":   ("#a8d5b5", "#2d2d2d"),
    "Medium2High":  ("#4caf7d", "#ffffff"),
    "High":         ("#1a6e3c", "#ffffff"),
}

_CATEGORIES = ["Low", "Low2Medium", "Medium2High", "High"]


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
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)
        self._build_legend()
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=2)
        self._build_table()

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
            text=f"Range of Influence  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
        ).pack(side="left", padx=16)

        n    = self._result.n
        hmax = self._rows[0]["hmax"] if self._rows else 0.0
        tk.Label(
            bar,
            text=f"{n} policies  |  max entropy = {hmax:.4f}",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------------

    def _build_legend(self):
        leg = tk.Frame(self, bg=COLOR_BG)
        leg.pack(fill="x", padx=16, pady=6)

        tk.Label(
            leg,
            text="Entropy measures how evenly a policy distributes its "
                 "outgoing influence. High = spread across many policies. "
                 "Low = concentrated on few.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            wraplength=800, justify="left",
        ).pack(anchor="w", pady=(0, 6))

        cat_row = tk.Frame(leg, bg=COLOR_BG)
        cat_row.pack(anchor="w")

        tk.Label(
            cat_row,
            text="Categories:",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(side="left", padx=(0, 10))

        thresholds = [
            ("Low",         "H < 25% of max"),
            ("Low2Medium",  "25% ≤ H < 50% of max"),
            ("Medium2High", "50% ≤ H < 75% of max"),
            ("High",        "H ≥ 75% of max"),
        ]
        for cat, desc in thresholds:
            bg, fg = _CAT_COLORS[cat]
            tk.Label(
                cat_row,
                text=f"  {cat}  ",
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg=bg, fg=fg,
                padx=6, pady=3, relief="flat",
            ).pack(side="left", padx=2)
            tk.Label(
                cat_row,
                text=desc,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            ).pack(side="left", padx=(2, 12))

    # ------------------------------------------------------------------

    def _build_table(self):
        canvas   = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical",   command=canvas.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right",  fill="y")
        h_scroll.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll( 1, "units"))

        self._draw_table(inner)

    # ------------------------------------------------------------------

    def _draw_table(self, frame: tk.Frame):
        pad        = 2
        col_widths = [6, 12, 18, 20]

        # ---- Header row ----
        headers = [
            ("Policy",    "Policy code",                          "Policy"),
            ("Entropy",   "Shannon entropy H (base 2)\n"
                          "0 = fully concentrated\n"
                          "log2(n-1) = perfectly distributed",    "Entropy"),
            ("Category",  "Influence distribution category\n"
                          "based on fraction of max entropy",     "Category"),
            ("Full Policy Name", "Full policy name",              "Full Policy Name"),
        ]

        for col, (hdr, tip, _) in enumerate(headers):
            lbl = tk.Label(
                frame,
                text=hdr,
                width=col_widths[col] if col < len(col_widths) else 20,
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg=COLOR_ACCENT, fg="#ffffff",
                relief="flat", padx=8, pady=8,
                anchor="center",
            )
            lbl.grid(row=0, column=col, padx=pad, pady=(8, pad), sticky="nsew")
            _Tooltip(lbl, tip)

        # ---- Data rows ----
        for r, row in enumerate(self._rows):
            bg_row = "#ffffff" if r % 2 == 0 else "#f4f1ec"

            # Policy code
            tk.Label(
                frame,
                text=row["code"],
                width=col_widths[0],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                bg=bg_row, fg=COLOR_TEXT,
                relief="groove", borderwidth=1,
                padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=0, padx=pad, pady=pad, sticky="nsew")

            # Entropy value
            tk.Label(
                frame,
                text=f"{row['entropy']:.4f}",
                width=col_widths[1],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=bg_row, fg=COLOR_TEXT,
                relief="groove", borderwidth=1,
                padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=1, padx=pad, pady=pad, sticky="nsew")

            # Category
            cat_bg, cat_fg = _CAT_COLORS[row["category"]]
            tk.Label(
                frame,
                text=row["category"],
                width=col_widths[2],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                bg=cat_bg, fg=cat_fg,
                relief="groove", borderwidth=1,
                padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=2, padx=pad, pady=pad, sticky="nsew")

            # Full policy name
            tk.Label(
                frame,
                text=row["policy"],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=bg_row, fg=COLOR_TEXT,
                relief="groove", borderwidth=1,
                padx=12, pady=7,
                anchor="w",
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
