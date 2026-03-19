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
from tkinter import ttk
from typing import List, Tuple

from .aggregator import AggregationResult
from .constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
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
        return "#1a6e3c", "#ffffff"
    if val > 0.5:
        return "#4caf7d", "#ffffff"
    if val > 0.0:
        return "#a8d5b5", "#2d2d2d"
    if val == 0.0:
        return "#d9d9d9", "#555555"
    if val >= -0.5:
        return "#f5c07a", "#2d2d2d"
    if val >= -1.5:
        return "#e07b39", "#ffffff"
    return "#b71c1c", "#ffffff"

def _count_color(val: int, n: int) -> Tuple[str, str]:
    """Colour for OI / II based on fraction of total policies affected."""
    if n <= 1:
        return "#d9d9d9", "#555555"
    ratio = val / (n - 1)
    if ratio >= 0.75:
        return "#2c4a6e", "#ffffff"
    if ratio >= 0.5:
        return "#5a7fa8", "#ffffff"
    if ratio >= 0.25:
        return "#c8d8ea", "#1e1e1e"
    return "#eae7e0", "#666666"


# =============================================================================
# Score calculation
# =============================================================================

def compute_scores(result: AggregationResult) -> List[dict]:
    """
    Compute OI, II, WOI, WII for every policy in the result.
    Returns a list of dicts (one per policy), sorted by policy index.
    """
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
            text=f"Coherence Scores  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
        ).pack(side="left", padx=16)

        tk.Label(
            bar,
            text=f"{self._result.n} policies",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------------

    def _build_legend(self):
        leg = tk.Frame(self, bg=COLOR_BG)
        leg.pack(fill="x", padx=16, pady=6)

        items = [
            ("OI",  "Outgoing Influence — number of policies this policy affects (non-zero row cells)"),
            ("II",  "Incoming Influence — number of policies that affect this policy (non-zero col cells)"),
            ("WOI", "Weighted Outgoing — sum of scores in the row (strength of influence exerted)"),
            ("WII", "Weighted Incoming — sum of scores in the column (strength of influence received)"),
        ]
        for abbr, desc in items:
            row = tk.Frame(leg, bg=COLOR_BG)
            row.pack(anchor="w", pady=1)
            tk.Label(
                row,
                text=f"{abbr}:",
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg=COLOR_BG, fg=COLOR_ACCENT,
                width=5, anchor="w",
            ).pack(side="left")
            tk.Label(
                row,
                text=desc,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            ).pack(side="left")

    # ------------------------------------------------------------------

    def _build_table(self):
        # Scrollable canvas
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
        n   = self._result.n
        pad = 2

        col_widths = [6, 6, 6, 10, 10]   # characters

        # ---- Header row ----
        headers    = ["Policy", "OI", "II", "WOI", "WII"]
        full_names = [
            "Policy code",
            "Outgoing Influence\n(non-zero row count)",
            "Incoming Influence\n(non-zero col count)",
            "Weighted Outgoing\n(row sum)",
            "Weighted Incoming\n(col sum)",
        ]
        for col, (hdr, width, full) in enumerate(zip(headers, col_widths, full_names)):
            lbl = tk.Label(
                frame,
                text=hdr,
                width=width,
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg=COLOR_ACCENT, fg="#ffffff",
                relief="flat", padx=8, pady=8,
                anchor="center",
            )
            lbl.grid(row=0, column=col, padx=pad, pady=(8, pad), sticky="nsew")
            _Tooltip(lbl, full)

        # ---- Full name column header ----
        tk.Label(
            frame,
            text="Full Policy Name",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_ACCENT, fg="#ffffff",
            relief="flat", padx=8, pady=8,
            anchor="w",
        ).grid(row=0, column=5, padx=pad, pady=(8, pad), sticky="nsew")

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
                relief="groove", borderwidth=1, padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=0, padx=pad, pady=pad, sticky="nsew")

            # OI
            oi_bg, oi_fg = _count_color(row["oi"], n)
            tk.Label(
                frame,
                text=str(row["oi"]),
                width=col_widths[1],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=oi_bg, fg=oi_fg,
                relief="groove", borderwidth=1,
                padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=1, padx=pad, pady=pad, sticky="nsew")

            # II
            ii_bg, ii_fg = _count_color(row["ii"], n)
            tk.Label(
                frame,
                text=str(row["ii"]),
                width=col_widths[2],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=ii_bg, fg=ii_fg,
                relief="groove", borderwidth=1,
                padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=2, padx=pad, pady=pad, sticky="nsew")

            # WOI
            woi_bg, woi_fg = _value_color(row["woi"])
            tk.Label(
                frame,
                text=f"{row['woi']:+.2f}",
                width=col_widths[3],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=woi_bg, fg=woi_fg,
                relief="groove", borderwidth=1,
                padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=3, padx=pad, pady=pad, sticky="nsew")

            # WII
            wii_bg, wii_fg = _value_color(row["wii"])
            tk.Label(
                frame,
                text=f"{row['wii']:+.2f}",
                width=col_widths[4],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=wii_bg, fg=wii_fg,
                relief="groove", borderwidth=1,
                padx=8, pady=7,
                anchor="center",
            ).grid(row=r + 1, column=4, padx=pad, pady=pad, sticky="nsew")

            # Full policy name
            tk.Label(
                frame,
                text=row["policy"],
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=bg_row, fg=COLOR_TEXT,
                relief="groove", borderwidth=1,
                padx=12, pady=7,
                anchor="w",
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
