# =============================================================================
# Policy Coherence Kit -- matrix_widget.py
# MatrixWidget: canvas-based interactive n x n coherence grid.
# All cells are drawn as canvas items (not individual Label widgets) so that
# tab switching remains fast regardless of matrix size.
# =============================================================================

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from models import PolicyMatrix
from constants import (
    COHERENCE_RATINGS, DIAGONAL_VALUE,
    RATING_COLORS, RATING_TEXT_COLORS,
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_HEADER,
    COLOR_ACCENT, COLOR_BG, COLOR_TEXT, COLOR_TEXT_LIGHT,
    COLOR_BORDER, CELL_WIDTH, HEADER_WIDTH,
)

# ---------------------------------------------------------------------------
# Canvas cell pixel dimensions
# ---------------------------------------------------------------------------
_CELL_W    = 82   # cell width in pixels
_CELL_H    = 30   # cell height in pixels
_HDR_W     = 82   # row-header width (matches cell width)
_GAP       = 2    # gap between cells
_AXIS_H    = 24   # height of the "Influencing / Influenced" label row
_COL_HDR_H = 34   # height of column-header row


class MatrixWidget(tk.Frame):
    """
    A scrollable frame that renders the full n x n coherence matrix on a
    single Canvas.  Using canvas items instead of individual Label widgets
    keeps the widget count at O(1) regardless of n, which makes notebook
    tab switching near-instant even for large matrices.

    Layout (canvas rows, top to bottom)
    ------------------------------------
    - Legend strip      (real tk widgets in a Frame above the canvas)
    - Axis label row    (canvas text, height = _AXIS_H)
    - Column headers    (P1, P2, …, height = _COL_HDR_H)
    - Matrix rows       (row header + cells, height = _CELL_H each)
    """

    def __init__(
        self,
        parent,
        matrix: PolicyMatrix,
        on_change: Callable = None,
        **kwargs,
    ):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._matrix   = matrix
        self._on_change = on_change or (lambda r, c, v: None)
        self._n        = len(matrix.policies)

        # canvas item IDs
        self._cell_rects: dict[tuple, int] = {}   # (i,j) -> rect id
        self._cell_texts: dict[tuple, int] = {}   # (i,j) -> text id

        self._canvas: Optional[tk.Canvas] = None
        self._combo:  Optional[ttk.Combobox] = None
        self._tooltip_win: Optional[tk.Toplevel] = None

        self._build()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _cell_bbox(self, i: int, j: int):
        """Canvas coordinates (x1, y1, x2, y2) of cell (i, j)."""
        x1 = _HDR_W + _GAP + j * (_CELL_W + _GAP)
        y1 = _AXIS_H + _COL_HDR_H + _GAP + i * (_CELL_H + _GAP)
        return x1, y1, x1 + _CELL_W, y1 + _CELL_H

    def _col_hdr_bbox(self, j: int):
        """Canvas coordinates of column header j."""
        x1 = _HDR_W + _GAP + j * (_CELL_W + _GAP)
        y1 = _AXIS_H
        return x1, y1, x1 + _CELL_W, y1 + _COL_HDR_H - _GAP

    def _row_hdr_bbox(self, i: int):
        """Canvas coordinates of row header i."""
        x1 = 0
        y1 = _AXIS_H + _COL_HDR_H + _GAP + i * (_CELL_H + _GAP)
        return x1, y1, x1 + _HDR_W - _GAP, y1 + _CELL_H

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        # ── Legend strip (real widgets — too complex to draw on canvas) ──
        legend = tk.Frame(self, bg=COLOR_BG)
        legend.pack(fill="x", padx=6, pady=(6, 4))

        tk.Label(
            legend,
            text="Click a cell to rate it:",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(side="left", padx=(0, 12))

        for rating in COHERENCE_RATINGS:
            tk.Label(
                legend,
                text=rating,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=RATING_COLORS[rating],
                fg=RATING_TEXT_COLORS[rating],
                padx=7, pady=3,
                relief="flat",
            ).pack(side="left", padx=2)

        # ── Canvas + scrollbars ──────────────────────────────────────────
        canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        vbar   = ttk.Scrollbar(self, orient="vertical",   command=canvas.yview)
        hbar   = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        hbar.pack(side="bottom", fill="x")
        vbar.pack(side="right",  fill="y")
        canvas.pack(fill="both", expand=True)

        self._canvas = canvas

        # Mouse-wheel scrolling (per-canvas bindings, not bind_all)
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll( 1, "units"))

        canvas.bind("<Button-1>", self._on_canvas_click)

        self._draw_canvas_grid()

    # ------------------------------------------------------------------

    def _draw_canvas_grid(self):
        canvas   = self._canvas
        n        = self._n
        codes    = self._matrix.codes
        policies = self._matrix.policies

        # ── Axis label ──────────────────────────────────────────────────
        canvas.create_text(
            _HDR_W + _GAP + 8, _AXIS_H // 2,
            text="<-- Influencing  |  Influenced -->",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            fill=COLOR_TEXT_LIGHT,
            anchor="w",
        )

        # ── Column headers ───────────────────────────────────────────────
        for j, code in enumerate(codes):
            x1, y1, x2, y2 = self._col_hdr_bbox(j)
            tag = f"chdr_{j}"
            canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_ACCENT,
                                    outline="", tags=tag)
            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                text=code,
                                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                                fill="#ffffff", tags=tag)

            tip = f"{code}:  {policies[j]}"
            canvas.tag_bind(tag, "<Enter>",
                            lambda e, t=tip, bx=x1, by=y2: self._show_tooltip(t, bx, by))
            canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

        # ── Row headers + cells ──────────────────────────────────────────
        for i in range(n):
            # Row header
            x1, y1, x2, y2 = self._row_hdr_bbox(i)
            tag = f"rhdr_{i}"
            canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_ACCENT,
                                    outline="", tags=tag)
            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                text=codes[i],
                                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                                fill="#ffffff", tags=tag)

            tip = f"{codes[i]}:  {policies[i]}"
            canvas.tag_bind(tag, "<Enter>",
                            lambda e, t=tip, bx=x2, by=y2: self._show_tooltip(t, bx, by))
            canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

            # Cells
            for j in range(n):
                is_diag = (i == j)
                value   = self._matrix.get_rating(i, j)
                x1, y1, x2, y2 = self._cell_bbox(i, j)

                if is_diag:
                    bg   = RATING_COLORS[DIAGONAL_VALUE]
                    fg   = RATING_TEXT_COLORS[DIAGONAL_VALUE]
                    text = DIAGONAL_VALUE
                elif value:
                    bg   = RATING_COLORS.get(value, "#f9f9f9")
                    fg   = RATING_TEXT_COLORS.get(value, COLOR_TEXT)
                    text = value
                else:
                    bg   = "#f9f9f9"
                    fg   = COLOR_TEXT_LIGHT
                    text = "--"

                rid = canvas.create_rectangle(x1, y1, x2, y2,
                                              fill=bg, outline=COLOR_BORDER)
                tid = canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                         text=text,
                                         font=(FONT_FAMILY, FONT_SIZE_SMALL),
                                         fill=fg)
                self._cell_rects[(i, j)] = rid
                self._cell_texts[(i, j)] = tid

        # ── Scroll region (fixed — no dynamic recalculation needed) ──────
        total_w = _HDR_W + _GAP + n * (_CELL_W + _GAP) + 8
        total_h = _AXIS_H + _COL_HDR_H + _GAP + n * (_CELL_H + _GAP) + 8
        canvas.configure(scrollregion=(0, 0, total_w, total_h))

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _on_canvas_click(self, event):
        canvas = self._canvas
        cx = canvas.canvasx(event.x)
        cy = canvas.canvasy(event.y)
        n  = self._n

        col_start = _HDR_W + _GAP
        row_start = _AXIS_H + _COL_HDR_H + _GAP

        if cx < col_start or cy < row_start:
            return

        j = int((cx - col_start) / (_CELL_W + _GAP))
        i = int((cy - row_start) / (_CELL_H + _GAP))

        if not (0 <= i < n and 0 <= j < n):
            return
        if i == j:
            return

        # Make sure the click landed inside the cell, not in the gap
        x1, y1, x2, y2 = self._cell_bbox(i, j)
        if not (x1 <= cx <= x2 and y1 <= cy <= y2):
            return

        self._open_cell_dropdown(i, j)

    def _open_cell_dropdown(self, i: int, j: int):
        if self._combo is not None:
            return

        canvas  = self._canvas
        matrix  = self._matrix
        x1, y1, x2, y2 = self._cell_bbox(i, j)

        # Translate canvas coords → widget-relative screen coords
        screen_x = int(x1 - canvas.canvasx(0))
        screen_y = int(y1 - canvas.canvasy(0))
        cell_w   = x2 - x1
        cell_h   = y2 - y1

        var   = tk.StringVar(value=matrix.get_rating(i, j))
        combo = ttk.Combobox(canvas, textvariable=var,
                             values=COHERENCE_RATINGS,
                             state="readonly",
                             font=(FONT_FAMILY, FONT_SIZE_SMALL))
        combo.place(x=screen_x, y=screen_y, width=cell_w, height=cell_h)
        combo.focus_set()
        combo.event_generate("<Button-1>")

        def _commit(e=None):
            selected = var.get()
            if selected:
                matrix.set_rating(i, j, selected)
                self._on_change(i, j, selected)
                self._update_cell_display(i, j, selected)
            _close()

        def _close(e=None):
            if self._combo is not None:
                self._combo.destroy()
                self._combo = None

        combo.bind("<<ComboboxSelected>>", _commit)
        combo.bind("<FocusOut>",           _close)
        combo.bind("<Escape>",             _close)
        self._combo = combo

    # ------------------------------------------------------------------
    # Tooltip
    # ------------------------------------------------------------------

    def _show_tooltip(self, text: str, canvas_x: int, canvas_y: int):
        self._hide_tooltip()
        canvas   = self._canvas
        screen_x = canvas.winfo_rootx() + int(canvas_x - canvas.canvasx(0))
        screen_y = canvas.winfo_rooty() + int(canvas_y - canvas.canvasy(0)) + 4

        tw = tk.Toplevel(canvas)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{screen_x}+{screen_y}")
        tk.Label(
            tw,
            text=text,
            justify="left",
            background="#fffbe6",
            foreground="#1e1e1e",
            relief="solid",
            borderwidth=1,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            padx=8, pady=4,
            wraplength=320,
        ).pack()
        self._tooltip_win = tw

    def _hide_tooltip(self):
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def _update_cell_display(self, i: int, j: int, value: str):
        """Update a cell's colour and text on the canvas."""
        canvas = self._canvas
        bg = RATING_COLORS.get(value, "#f9f9f9")
        fg = RATING_TEXT_COLORS.get(value, COLOR_TEXT)
        canvas.itemconfig(self._cell_rects[(i, j)], fill=bg)
        canvas.itemconfig(self._cell_texts[(i, j)], text=value, fill=fg)

    def refresh_cell(self, row: int, col: int):
        """Re-read the model and repaint a single cell (call after external edits)."""
        value = self._matrix.get_rating(row, col)
        if value:
            self._update_cell_display(row, col, value)
        else:
            canvas = self._canvas
            canvas.itemconfig(self._cell_rects[(row, col)], fill="#f9f9f9")
            canvas.itemconfig(self._cell_texts[(row, col)],
                              text="--", fill=COLOR_TEXT_LIGHT)
