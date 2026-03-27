# =============================================================================
# Policy Coherence Kit -- aggregation_tab.py
# AggregationTab: read-only numeric result tab added to the main notebook.
# =============================================================================

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from aggregator import AggregationResult
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
    RATING_SCORES, CELL_WIDTH, HEADER_WIDTH,
)

# Colour scale for numeric cells: maps score range [-3, 3] to colours
# Same semantic palette as RATING_COLORS but applied to float values
_SCORE_COLORS = {
    3:  ("#1a6e3c", "#ffffff"),   # Indivisible  deep green / white text
    2:  ("#4caf7d", "#ffffff"),   # Reinforcing
    1:  ("#a8d5b5", "#2d2d2d"),   # Enabling
    0:  ("#d9d9d9", "#555555"),   # Neutral
   -1:  ("#f5c07a", "#2d2d2d"),   # Constraining
   -2:  ("#e07b39", "#ffffff"),   # Counteracting
   -3:  ("#b71c1c", "#ffffff"),   # Cancelling
}


def _score_to_color(score: float):
    """
    Map a float score to (bg, fg) colours.
    Clamps to [-3, 3] and picks the nearest integer bucket.
    """
    if score is None:
        return "#f9f9f9", COLOR_TEXT_LIGHT
    clamped = max(-3.0, min(3.0, score))
    # Find nearest integer key
    nearest = min(_SCORE_COLORS.keys(), key=lambda k: abs(k - clamped))
    return _SCORE_COLORS[nearest]


# =============================================================================
# AggregationTab
# =============================================================================

class AggregationTab(tk.Frame):
    """
    A read-only frame that displays an AggregationResult as a numeric matrix.

    - Diagonal cells show 0 (grey).
    - Off-diagonal cells show the float score (2 dp), colour-coded.
    - No click handlers — purely for viewing.
    - Includes a summary panel: per-policy row total and column total.
    """

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result = result
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)
        self._build_legend()
        self._build_scrollable_matrix()

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
            text=f"Aggregated Matrix  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
        ).pack(side="left", padx=16)

        tk.Label(
            bar,
            text=f"{self._result.n} policies  |  scores range: -3 to +3  |  diagonal = 0",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------------

    def _build_legend(self):
        legend = tk.Frame(self, bg=COLOR_BG)
        legend.pack(fill="x", padx=12, pady=(4, 0))

        tk.Label(
            legend,
            text="Score scale:",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(side="left", padx=(4, 10))

        # Show integer anchors from +3 to -3
        from constants import COHERENCE_RATINGS
        ratings_asc = list(reversed(COHERENCE_RATINGS))   # -3 ... +3
        scores_asc  = list(range(-3, 4))

        for rating, score in zip(COHERENCE_RATINGS, range(3, -4, -1)):
            bg, fg = _SCORE_COLORS[score]
            tk.Label(
                legend,
                text=f"{score:+d}  {rating}",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=bg, fg=fg,
                padx=7, pady=3,
                relief="flat",
            ).pack(side="left", padx=2)

    # ------------------------------------------------------------------

    def _build_scrollable_matrix(self):
        canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
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

        self._draw_matrix(inner)

    # ------------------------------------------------------------------

    def _draw_matrix(self, frame: tk.Frame):
        result   = self._result
        n        = result.n
        codes    = result.codes
        policies = result.policies
        pad      = 2

        # ---- empty corner ----
        tk.Label(frame, text="", width=HEADER_WIDTH, bg=COLOR_BG).grid(
            row=0, column=0, padx=pad, pady=(8, pad))

        # ---- column headers ----
        for j, code in enumerate(codes):
            lbl = tk.Label(
                frame,
                text=code,
                width=CELL_WIDTH,
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg=COLOR_ACCENT, fg="#ffffff",
                relief="flat", padx=4, pady=6,
                anchor="center",
            )
            lbl.grid(row=0, column=j + 1, padx=pad, pady=(8, pad))
            _Tooltip(lbl, f"{code}:  {policies[j]}")

        # ---- data rows ----
        for i in range(n):
            row_lbl = tk.Label(
                frame,
                text=codes[i],
                width=HEADER_WIDTH,
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg=COLOR_ACCENT, fg="#ffffff",
                relief="flat", padx=4, pady=6,
                anchor="center",
            )
            row_lbl.grid(row=i + 1, column=0, padx=pad, pady=pad)
            _Tooltip(row_lbl, f"{codes[i]}:  {policies[i]}")

            for j in range(n):
                score   = result.scores.get((i, j), 0.0)
                is_diag = (i == j)

                if is_diag:
                    text   = "0"
                    bg, fg = _SCORE_COLORS[0]
                else:
                    text   = f"{score:.2f}" if score is not None else "?"
                    bg, fg = _score_to_color(score)

                tk.Label(
                    frame,
                    text=text,
                    width=CELL_WIDTH,
                    font=(FONT_FAMILY, FONT_SIZE_SMALL),
                    bg=bg, fg=fg,
                    relief="groove", borderwidth=1,
                    padx=2, pady=7,
                    anchor="center",
                ).grid(row=i + 1, column=j + 1, padx=pad, pady=pad, sticky="nsew")


# =============================================================================
# Internal tooltip (same as matrix_widget but self-contained)
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
