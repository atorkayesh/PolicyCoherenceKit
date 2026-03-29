# =============================================================================
# Policy Coherence Kit -- matrix_widget.py
# MatrixWidget: canvas-based interactive n x n coherence grid.
# All cells are drawn as canvas items (not individual Label widgets) so that
# tab switching remains fast regardless of matrix size.
# =============================================================================

import math
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from models import PolicyMatrix
from constants import (
    COHERENCE_RATINGS, DIAGONAL_VALUE,
    RATING_COLORS, RATING_TEXT_COLORS,
    FONT_FAMILY,
    COLOR_BG, COLOR_TEXT, COLOR_TEXT_LIGHT,
    COLOR_BORDER,
)

# ---------------------------------------------------------------------------
# Canvas cell pixel dimensions
# ---------------------------------------------------------------------------
_CELL_H       = 40    # cell and header height in pixels
_HDR_W        = 120   # row-header (P1, P2…) width in pixels
_CELL_W_LARGE = 200   # cell width when n > 5
_GAP          = 4     # gap between cells / headers
_AXIS_H       = 40    # height of "Influencing / Influenced" label row
_COL_HDR_H    = 40    # column-header row height (same as _CELL_H)
_PADX         = 24    # left / right padding around the grid block
_CELL_RADIUS  = 8     # border radius for all matrix cells and headers

# Header label styling (P1, P2 … boxes)
_HDR_BG        = "#426387"
_HDR_FG        = "#f5f7fa"
_HDR_FONT_SIZE = 10    # pt, not bold

# Legend strip (drawn on canvas above the grid)
_LEGEND_H         = 40    # total height of the legend row
_LEGEND_GAP       = 16    # empty space between legend and matrix grid
_BADGE_H          = 25    # height of each rating badge rectangle
_BADGE_PAD_X      = 10    # horizontal inner padding inside each badge (drives width)
_BADGE_FONT_SIZE  = 10    # pt — badge label font size
_BADGE_GAP        = 3     # gap between consecutive badges
_BADGE_RADIUS     = 4     # border radius of each rating badge


def _round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """Draw a rounded rectangle on canvas using a smooth polygon."""
    points = [
        x1 + r, y1,  x2 - r, y1,
        x2,     y1,  x2,     y1 + r,
        x2,     y2 - r,  x2, y2,
        x2 - r, y2,  x1 + r, y2,
        x1,     y2,  x1,     y2 - r,
        x1,     y1 + r,  x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class _PillScrollbar(tk.Canvas):
    """Canvas scrollbar with fully-rounded (pill) thumb ends."""

    _THICK     = 10    # track thickness in pixels
    _TROUGH    = "#eaeef4"
    _THUMB     = "#d0dbe7"
    _THUMB_HOV = "#b8c8d8"
    _MIN_THUMB = 28    # minimum thumb length in pixels

    def __init__(self, parent, orient: str = "vertical", command=None, **kwargs):
        self._orient   = orient
        self._command  = command
        self._first    = 0.0
        self._last     = 1.0
        self._drag_ref = None   # (mouse_coord, first_at_press)
        self._hovered  = False

        kw: dict = dict(highlightthickness=0, bg=self._TROUGH, bd=0)
        if orient == "vertical":
            kw["width"] = self._THICK
        else:
            kw["height"] = self._THICK
        super().__init__(parent, **kw, **kwargs)

        self.bind("<Configure>",       self._redraw)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))

    # ── public scrollbar interface ──────────────────────────────────────

    def set(self, first, last):
        self._first = float(first)
        self._last  = float(last)
        self._redraw()

    # ── drawing ─────────────────────────────────────────────────────────

    def _redraw(self, _event=None):
        self.delete("thumb")
        W = self.winfo_width()
        H = self.winfo_height()
        if W <= 1 or H <= 1:
            return

        t = self._THICK
        r = t // 2   # full radius → circular ends

        if self._orient == "vertical":
            track = H
            tlen  = max(self._MIN_THUMB, int(track * (self._last - self._first)))
            tpos  = int(track * self._first)
            tpos  = min(tpos, track - tlen)
            x1, y1, x2, y2 = 0, tpos, t, tpos + tlen
        else:
            track = W
            tlen  = max(self._MIN_THUMB, int(track * (self._last - self._first)))
            tpos  = int(track * self._first)
            tpos  = min(tpos, track - tlen)
            x1, y1, x2, y2 = tpos, 0, tpos + tlen, t

        color = self._THUMB_HOV if self._hovered else self._THUMB
        pts = [
            x1 + r, y1,     x2 - r, y1,
            x2,     y1,     x2,     y1 + r,
            x2,     y2 - r, x2,     y2,
            x2 - r, y2,     x1 + r, y2,
            x1,     y2,     x1,     y2 - r,
            x1,     y1 + r, x1,     y1,
        ]
        self.create_polygon(pts, smooth=True, fill=color, outline="", tags="thumb")

    # ── interaction ──────────────────────────────────────────────────────

    def _on_press(self, event):
        coord = event.y if self._orient == "vertical" else event.x
        self._drag_ref = (coord, self._first)

    def _on_drag(self, event):
        if self._drag_ref is None or self._command is None:
            return
        start, first0 = self._drag_ref
        coord = event.y if self._orient == "vertical" else event.x
        size  = self.winfo_height() if self._orient == "vertical" else self.winfo_width()
        delta = (coord - start) / size
        new_first = max(0.0, min(1.0 - (self._last - self._first), first0 + delta))
        self._command("moveto", str(new_first))

    def _on_release(self, _event):
        self._drag_ref = None

    def _set_hover(self, state: bool):
        self._hovered = state
        self._redraw()


class MatrixWidget(tk.Frame):
    """
    Renders the full n x n coherence matrix on a single Canvas.
    No scrollbars — the content block (legend + grid) is centered
    vertically and horizontally in the available space.

    Cell width rules:
      n ≤ 5 → cells expand to fill the canvas width (full-width layout)
      n > 5 → each cell is _CELL_W_LARGE (160 px) wide; block is centered
    """

    def __init__(
        self,
        parent,
        matrix: PolicyMatrix,
        on_change: Callable = None,
        **kwargs,
    ):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._matrix    = matrix
        self._on_change = on_change or (lambda r, c, v: None)
        self._n         = len(matrix.policies)

        # canvas item IDs
        self._cell_rects: dict[tuple, int] = {}
        self._cell_texts: dict[tuple, int] = {}

        self._canvas: Optional[tk.Canvas] = None
        self._combo:  Optional[ttk.Combobox] = None
        self._tooltip_win: Optional[tk.Toplevel] = None

        # Centering offsets (updated on every redraw)
        self._ox: int = 0   # horizontal offset for the grid block
        self._oy: int = 0   # vertical offset for the whole block

        # Current computed cell width
        self._cell_w: int = _CELL_W_LARGE

        # Smooth-scroll state
        self._scroll_vy:   float         = 0.0   # vertical velocity (fraction/frame)
        self._scroll_anim: Optional[str] = None  # after() id

        self._build()

    # ------------------------------------------------------------------
    # Dynamic cell width
    # ------------------------------------------------------------------

    def _compute_cell_w(self, canvas_w: int) -> int:
        n = self._n
        if n > 5:
            return _CELL_W_LARGE
        # Expand cells to fill canvas width minus left/right padding
        available = canvas_w - 2 * _PADX - _HDR_W - _GAP * (n + 1)
        return max(60, available // n)

    # ------------------------------------------------------------------
    # Block dimension helpers
    # ------------------------------------------------------------------

    def _block_w(self) -> int:
        return _HDR_W + _GAP + self._n * (self._cell_w + _GAP)

    def _block_h(self) -> int:
        return _LEGEND_H + _LEGEND_GAP + _AXIS_H + _COL_HDR_H + _GAP + self._n * (_CELL_H + _GAP)

    # ------------------------------------------------------------------
    # Geometry helpers (use instance offsets + current cell_w)
    # ------------------------------------------------------------------

    def _cell_bbox(self, i: int, j: int):
        """Canvas coordinates (x1, y1, x2, y2) of data cell (i, j)."""
        ox, oy = self._ox, self._oy
        x1 = ox + _HDR_W + _GAP + j * (self._cell_w + _GAP)
        y1 = oy + _LEGEND_H + _LEGEND_GAP + _AXIS_H + _COL_HDR_H + _GAP + i * (_CELL_H + _GAP)
        return x1, y1, x1 + self._cell_w, y1 + _CELL_H

    def _col_hdr_bbox(self, j: int):
        """Canvas coordinates of column header j."""
        ox, oy = self._ox, self._oy
        x1 = ox + _HDR_W + _GAP + j * (self._cell_w + _GAP)
        y1 = oy + _LEGEND_H + _LEGEND_GAP + _AXIS_H
        return x1, y1, x1 + self._cell_w, y1 + _COL_HDR_H - _GAP

    def _row_hdr_bbox(self, i: int):
        """Canvas coordinates of row header i."""
        ox, oy = self._ox, self._oy
        x1 = ox
        y1 = oy + _LEGEND_H + _LEGEND_GAP + _AXIS_H + _COL_HDR_H + _GAP + i * (_CELL_H + _GAP)
        return x1, y1, x1 + _HDR_W - _GAP, y1 + _CELL_H

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self._canvas = canvas

        # ── Pill scrollbars (canvas children, overlay) ──────────────────
        self._vbar = _PillScrollbar(canvas, orient="vertical",   command=canvas.yview)
        self._hbar = _PillScrollbar(canvas, orient="horizontal",  command=canvas.xview)

        canvas.configure(
            yscrollcommand=lambda f, l: self._on_scrollcmd(self._vbar, f, l, vertical=True),
            xscrollcommand=lambda f, l: self._on_scrollcmd(self._hbar, f, l, vertical=False),
        )

        # Smooth mouse-wheel scrolling
        canvas.bind("<MouseWheel>",
                    lambda e: self._add_scroll_velocity(-e.delta / 120))
        canvas.bind("<Button-4>", lambda e: self._add_scroll_velocity(-1))
        canvas.bind("<Button-5>", lambda e: self._add_scroll_velocity( 1))

        canvas.bind("<Configure>", self._on_configure)
        canvas.bind("<Button-1>", self._on_canvas_click)

        # Initial draw once the widget is laid out
        self.after_idle(self._redraw)

    def _on_scrollcmd(self, bar, first, last, *, vertical: bool):
        """Auto-show / auto-hide a scrollbar based on whether scrolling is needed."""
        bar.set(first, last)
        needs_scroll = not (float(first) <= 0.0 and float(last) >= 1.0)
        if needs_scroll:
            if vertical:
                bar.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne",
                          width=_PillScrollbar._THICK, x=-8)
            else:
                bar.place(relx=0.0, rely=1.0, relwidth=1.0, anchor="sw",
                          height=_PillScrollbar._THICK)
        else:
            bar.place_forget()

    # ------------------------------------------------------------------
    # Smooth scrolling
    # ------------------------------------------------------------------

    _SCROLL_STEP    = 0.006   # fraction of view added per wheel tick
    _SCROLL_DECAY   = 0.82    # velocity multiplied each frame (< 1 = friction)
    _SCROLL_CUTOFF  = 0.0001  # stop animating below this velocity
    _SCROLL_FRAME   = 16      # ms per animation frame (~60 fps)

    def _add_scroll_velocity(self, ticks: float):
        self._scroll_vy += ticks * self._SCROLL_STEP
        self._scroll_vy = max(-0.06, min(0.06, self._scroll_vy))
        if self._scroll_anim is None:
            self._scroll_tick()

    def _scroll_tick(self):
        if abs(self._scroll_vy) < self._SCROLL_CUTOFF:
            self._scroll_vy  = 0.0
            self._scroll_anim = None
            return
        canvas = self._canvas
        current = float(canvas.yview()[0])
        canvas.yview_moveto(max(0.0, min(1.0, current + self._scroll_vy)))
        self._scroll_vy  *= self._SCROLL_DECAY
        self._scroll_anim = self.after(self._SCROLL_FRAME, self._scroll_tick)

    # ------------------------------------------------------------------
    # Redraw (called on resize and after build)
    # ------------------------------------------------------------------

    def _on_configure(self, event):
        self._redraw(event.width, event.height)

    def _redraw(self, canvas_w: int = None, canvas_h: int = None):
        canvas = self._canvas
        if canvas_w is None:
            canvas_w = canvas.winfo_width()
        if canvas_h is None:
            canvas_h = canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        canvas.delete("all")
        self._cell_rects.clear()
        self._cell_texts.clear()

        n = self._n

        # Compute dynamic cell width
        self._cell_w = self._compute_cell_w(canvas_w)

        # Compute centering offsets
        block_h = self._block_h()
        if n > 5:
            block_w = self._block_w()
            self._ox = max(_PADX, (canvas_w - block_w) // 2)
        else:
            self._ox = _PADX   # full-width layout: respect left/right padding

        self._oy = max(0, (canvas_h - block_h) // 2)

        # Configure scroll region: only enable scrolling for n > 5
        if n > 5:
            sr_w = max(canvas_w, _PADX + self._block_w() + _PADX)
            sr_h = max(canvas_h, block_h + 16)
            self._canvas.configure(scrollregion=(0, 0, sr_w, sr_h))
        else:
            self._canvas.configure(scrollregion=(0, 0, canvas_w, canvas_h))

        self._draw_legend(canvas_w)
        self._draw_canvas_grid()

    # ------------------------------------------------------------------
    # Legend (drawn on canvas, centered over full canvas width)
    # ------------------------------------------------------------------

    def _draw_legend(self, canvas_w: int):
        canvas = self._canvas
        oy     = self._oy
        label_y = oy + _LEGEND_H // 2

        # --- measure label width ---
        lbl_text = "Click a cell to rate it:"
        _tmp = canvas.create_text(0, -1000, text=lbl_text,
                                   font=(FONT_FAMILY, 9, "italic"), anchor="w")
        lbl_w = canvas.bbox(_tmp)[2] - canvas.bbox(_tmp)[0]
        canvas.delete(_tmp)

        # --- measure badge widths ---
        badge_widths = []
        for rating in COHERENCE_RATINGS:
            _tmp = canvas.create_text(0, -1000, text=rating,
                                       font=(FONT_FAMILY, _BADGE_FONT_SIZE), anchor="w")
            tw = canvas.bbox(_tmp)[2] - canvas.bbox(_tmp)[0]
            canvas.delete(_tmp)
            badge_widths.append(tw + 2 * _BADGE_PAD_X)

        total_legend_w = (lbl_w + 10
                          + sum(badge_widths)
                          + _BADGE_GAP * (len(badge_widths) - 1))
        start_x = max(0, (canvas_w - total_legend_w) // 2)

        # --- draw label ---
        canvas.create_text(start_x, label_y,
                           text=lbl_text,
                           font=(FONT_FAMILY, 9, "italic"),
                           fill="#a3a3a3", anchor="w", tags="legend")

        # --- draw rating badges ---
        x = start_x + lbl_w + 10
        badge_y1 = label_y - _BADGE_H // 2
        badge_y2 = badge_y1 + _BADGE_H

        for rating, bw in zip(COHERENCE_RATINGS, badge_widths):
            bg = RATING_COLORS[rating]
            fg = RATING_TEXT_COLORS[rating]
            _round_rect(canvas, x, badge_y1, x + bw, badge_y2,
                        _BADGE_RADIUS, fill=bg, outline="", tags="legend")
            canvas.create_text(x + bw // 2, label_y, text=rating,
                               font=(FONT_FAMILY, _BADGE_FONT_SIZE), fill=fg, tags="legend")
            x += bw + _BADGE_GAP

    # ------------------------------------------------------------------
    # Grid (axis label + column headers + row headers + cells)
    # ------------------------------------------------------------------

    def _draw_canvas_grid(self):
        canvas   = self._canvas
        n        = self._n
        codes    = self._matrix.codes
        policies = self._matrix.policies
        ox, oy   = self._ox, self._oy

        # ── Axis label ──────────────────────────────────────────────────
        axis_y = oy + _LEGEND_H + _LEGEND_GAP + _AXIS_H // 2
        canvas.create_text(
            ox + _HDR_W + _GAP + 4, axis_y,
            text="<-- Influencing  |  Influenced -->",
            font=(FONT_FAMILY, 9, "italic"),
            fill="#a3a3a3",
            anchor="w",
        )

        # ── Column headers ───────────────────────────────────────────────
        for j, code in enumerate(codes):
            x1, y1, x2, y2 = self._col_hdr_bbox(j)
            tag = f"chdr_{j}"
            _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS,
                        fill=_HDR_BG, outline="", tags=tag)
            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                text=code,
                                font=(FONT_FAMILY, _HDR_FONT_SIZE),
                                fill=_HDR_FG, tags=tag)

            tip = f"{code}:  {policies[j]}"
            canvas.tag_bind(tag, "<Enter>",
                            lambda e, t=tip, bx=x1, by=y2: self._show_tooltip(t, bx, by))
            canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

        # ── Row headers + cells ──────────────────────────────────────────
        for i in range(n):
            # Row header
            x1, y1, x2, y2 = self._row_hdr_bbox(i)
            tag = f"rhdr_{i}"
            _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS,
                        fill=_HDR_BG, outline="", tags=tag)
            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                text=codes[i],
                                font=(FONT_FAMILY, _HDR_FONT_SIZE),
                                fill=_HDR_FG, tags=tag)

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

                rid = _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS,
                                  fill=bg, outline="")
                tid = canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                         text=text,
                                         font=(FONT_FAMILY, 9),
                                         fill=fg)
                self._cell_rects[(i, j)] = rid
                self._cell_texts[(i, j)] = tid

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _on_canvas_click(self, event):
        canvas = self._canvas
        cx = canvas.canvasx(event.x)
        cy = canvas.canvasy(event.y)
        n  = self._n
        ox, oy = self._ox, self._oy

        col_start = ox + _HDR_W + _GAP
        row_start = oy + _LEGEND_H + _AXIS_H + _COL_HDR_H + _GAP

        if cx < col_start or cy < row_start:
            return

        j = int((cx - col_start) / (self._cell_w + _GAP))
        i = int((cy - row_start) / (_CELL_H + _GAP))

        if not (0 <= i < n and 0 <= j < n):
            return
        if i == j:
            return

        # Confirm the click landed inside the cell (not in the gap)
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
                             font=(FONT_FAMILY, 9))
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
            font=(FONT_FAMILY, 9),
            padx=8, pady=4,
            wraplength=320,
        ).pack()
        self._tooltip_win = tw

    def _hide_tooltip(self):
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None

    # ------------------------------------------------------------------
    # Public / cell refresh
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
