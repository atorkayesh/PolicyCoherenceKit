# =============================================================================
# Policy Coherence Kit -- matrix_widget.py
# MatrixWidget: scrollable, interactive n x n coherence grid.
# Tooltip: hover-over label showing full policy name.
# CellDropdown: in-place combobox for rating selection.
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


# =============================================================================
# Tooltip
# =============================================================================

class Tooltip:
    """
    Shows a small popup label when the pointer hovers over a widget.
    Used to display full policy names on P1 / P2 ... header cells.
    """

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self._window: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        if self._window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#fffbe6",
            foreground="#1e1e1e",
            relief="solid",
            borderwidth=1,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            padx=8, pady=4,
            wraplength=320,
        ).pack()

    def _hide(self, event=None):
        if self._window:
            self._window.destroy()
            self._window = None


# =============================================================================
# CellDropdown
# =============================================================================

class CellDropdown:
    """
    Manages an in-place Combobox that opens when the user clicks a cell label.
    On selection the model is updated and the label is recoloured immediately.
    """

    def __init__(
        self,
        parent_frame: tk.Frame,
        matrix: PolicyMatrix,
        row: int,
        col: int,
        label: tk.Label,
        on_change: Callable,
    ):
        self._parent = parent_frame
        self._matrix = matrix
        self._row = row
        self._col = col
        self._label = label
        self._on_change = on_change
        self._combo: Optional[ttk.Combobox] = None

        label.bind("<Button-1>", self._open)

    # ------------------------------------------------------------------

    def _open(self, event=None):
        if self._combo is not None:
            return   # already open

        var = tk.StringVar(value=self._matrix.get_rating(self._row, self._col))

        combo = ttk.Combobox(
            self._parent,
            textvariable=var,
            values=COHERENCE_RATINGS,
            state="readonly",
            width=CELL_WIDTH,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        )
        # Overlay the combobox exactly on top of the cell label
        combo.place(in_=self._label, relx=0, rely=0, relwidth=1, relheight=1)
        combo.focus_set()
        combo.event_generate("<Button-1>")   # pop the list open immediately

        def _commit(e=None):
            selected = var.get()
            if selected:
                self._matrix.set_rating(self._row, self._col, selected)
                self._apply_color(selected)
                self._on_change(self._row, self._col, selected)
            _close()

        def _close(e=None):
            if self._combo is not None:
                self._combo.destroy()
                self._combo = None

        combo.bind("<<ComboboxSelected>>", _commit)
        combo.bind("<FocusOut>", _close)
        combo.bind("<Escape>", _close)
        self._combo = combo

    def _apply_color(self, value: str):
        bg = RATING_COLORS.get(value, "#f9f9f9")
        fg = RATING_TEXT_COLORS.get(value, COLOR_TEXT)
        self._label.config(text=value, background=bg, foreground=fg)


# =============================================================================
# MatrixWidget
# =============================================================================

class MatrixWidget(tk.Frame):
    """
    A scrollable frame that renders the full n x n coherence matrix.

    Layout
    ------
    Row 0  : colour-coded rating legend strip
    Row 1  : axis direction label  ("Influencing / Influenced")
    Row 2  : column headers  (P1, P2, ...)  with tooltips
    Row 3+ : row header + cells

    Diagonal cells are rendered as locked (grey, no click handler).
    All other cells open a CellDropdown on click.
    """

    def __init__(
        self,
        parent,
        matrix: PolicyMatrix,
        on_change: Callable = None,
        **kwargs,
    ):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._matrix = matrix
        self._on_change = on_change or (lambda r, c, v: None)
        self._cell_labels: dict[tuple, tk.Label] = {}
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        # Outer scrollable canvas (scrollbars hidden; mouse-wheel still works)
        canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Mouse-wheel scrolling (Windows / macOS)
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )
        # Mouse-wheel scrolling (Linux)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll( 1, "units"))

        self._draw_grid(inner)

    # ------------------------------------------------------------------

    def _draw_grid(self, frame: tk.Frame):
        n       = len(self._matrix.policies)
        codes   = self._matrix.codes
        policies = self._matrix.policies
        pad = 2

        # ---- Row 0: legend strip ----------------------------------------
        legend = tk.Frame(frame, bg=COLOR_BG)
        legend.grid(row=0, column=0, columnspan=n + 2,
                    sticky="w", padx=6, pady=(6, 10))

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

        # ---- Row 1: axis label ------------------------------------------
        tk.Label(
            frame,
            text="",
            width=HEADER_WIDTH,
            bg=COLOR_BG,
        ).grid(row=1, column=0, padx=pad, pady=pad)

        tk.Label(
            frame,
            text="<-- Influencing  |  Influenced -->",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).grid(row=1, column=1, columnspan=n, padx=pad, pady=pad)

        # ---- Row 2: column headers (P1, P2, ...) ------------------------
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
            lbl.grid(row=2, column=j + 1, padx=pad, pady=pad)
            Tooltip(lbl, f"{code}:  {policies[j]}")

        # ---- Rows 3+: row header + cells --------------------------------
        for i in range(n):
            # Row header
            row_lbl = tk.Label(
                frame,
                text=codes[i],
                width=HEADER_WIDTH,
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg=COLOR_ACCENT, fg="#ffffff",
                relief="flat", padx=4, pady=6,
                anchor="center",
            )
            row_lbl.grid(row=i + 3, column=0, padx=pad, pady=pad)
            Tooltip(row_lbl, f"{codes[i]}:  {policies[i]}")

            # Cells
            for j in range(n):
                is_diag = (i == j)
                value   = self._matrix.get_rating(i, j)

                if is_diag:
                    bg, fg, text, cursor = (
                        RATING_COLORS[DIAGONAL_VALUE],
                        RATING_TEXT_COLORS[DIAGONAL_VALUE],
                        DIAGONAL_VALUE,
                        "arrow",
                    )
                elif value:
                    bg, fg, text, cursor = (
                        RATING_COLORS.get(value, "#f9f9f9"),
                        RATING_TEXT_COLORS.get(value, COLOR_TEXT),
                        value,
                        "hand2",
                    )
                else:
                    bg, fg, text, cursor = (
                        "#f9f9f9",
                        COLOR_TEXT_LIGHT,
                        "--",
                        "hand2",
                    )

                cell = tk.Label(
                    frame,
                    text=text,
                    width=CELL_WIDTH,
                    font=(FONT_FAMILY, FONT_SIZE_SMALL),
                    bg=bg, fg=fg,
                    relief="groove",
                    borderwidth=1,
                    padx=2, pady=7,
                    anchor="center",
                    cursor=cursor,
                )
                cell.grid(row=i + 3, column=j + 1, padx=pad, pady=pad, sticky="nsew")
                self._cell_labels[(i, j)] = cell

                if not is_diag:
                    CellDropdown(frame, self._matrix, i, j, cell, self._cell_changed)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _cell_changed(self, row: int, col: int, value: str):
        self._on_change(row, col, value)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def refresh_cell(self, row: int, col: int):
        """Re-read the model and repaint a single cell (call after external edits)."""
        lbl = self._cell_labels.get((row, col))
        if lbl is None:
            return
        value = self._matrix.get_rating(row, col)
        if value:
            lbl.config(
                text=value,
                background=RATING_COLORS.get(value, "#f9f9f9"),
                foreground=RATING_TEXT_COLORS.get(value, COLOR_TEXT),
            )
        else:
            lbl.config(text="--", background="#f9f9f9", foreground=COLOR_TEXT_LIGHT)
