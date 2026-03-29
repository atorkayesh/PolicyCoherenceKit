# =============================================================================
# Policy Coherence Kit -- matrix_widget.py
# MatrixWidget: canvas-based interactive n x n coherence grid.
# All cells are drawn as canvas items (not individual Label widgets) so that
# tab switching remains fast regardless of matrix size.
# =============================================================================

import tkinter as tk
from typing import Callable, Optional

from models import PolicyMatrix
from constants import (
    COHERENCE_RATINGS, DIAGONAL_VALUE,
    RATING_COLORS, RATING_TEXT_COLORS,
    FONT_FAMILY,
    COLOR_BG, COLOR_TEXT, COLOR_TEXT_LIGHT,
    COLOR_BORDER,
    MATRIX_PADX,
)

# ---------------------------------------------------------------------------
# Canvas cell pixel dimensions
# ---------------------------------------------------------------------------
_CELL_H       = 40    # cell and header height in pixels
_HDR_W        = 120   # row-header (P1, P2…) width in pixels
_CELL_W_LARGE = 200   # cell width when n > 5
_GAP          = 6     # gap between cells / headers
_AXIS_H       = 40    # height of "Influencing / Influenced" label row
_COL_HDR_H    = 44    # column-header row height (same as _CELL_H)
_PADX         = 5             # internal left/right buffer inside cell canvas
_HDR_LEFT_PAD = 28           # px — space between left sidebar and row-header column
_CELL_RADIUS  = 8     # border radius for all matrix cells and headers

# Header label styling (P1, P2 … boxes)
_HDR_BG        = "#426387"
_HDR_FG        = "#f5f7fa"
_HDR_FONT_SIZE  = 10    # pt, not bold
_CELL_FONT_SIZE = 12    # pt — text inside matrix cells and cell input

# Legend strip (drawn on a separate canvas above the grid)
_LEGEND_H         = 40    # total height of the legend row
_BADGE_H          = 25    # height of each rating badge rectangle
_BADGE_PAD_X      = 10    # horizontal inner padding inside each badge
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

    _THICK     = 5     # track thickness in pixels
    _TROUGH    = "#eaeef4"
    _THUMB     = "#d0dbe7"
    _THUMB_HOV = "#b8c8d8"
    _MIN_THUMB = 28    # minimum thumb length in pixels

    def __init__(self, parent, orient: str = "vertical", command=None, **kwargs):
        self._orient   = orient
        self._command  = command
        self._first    = 0.0
        self._last     = 1.0
        self._drag_ref = None
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

    def set(self, first, last):
        self._first = float(first)
        self._last  = float(last)
        self._redraw()

    def _redraw(self, _event=None):
        self.delete("thumb")
        W = self.winfo_width()
        H = self.winfo_height()
        if W <= 1 or H <= 1:
            return

        t = self._THICK
        r = t // 2

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
    Renders the full n x n coherence matrix using four coordinated canvases
    so that row and column headers stay fixed while cells scroll.

    Layout:
      row 0 : legend canvas  (spans full width, non-scrollable)
      row 1 : corner | col_hdr_canvas (scrolls X)
      row 2 : row_hdr_canvas (scrolls Y) | main_canvas (scrolls X+Y) | vbar
      row 3 :                              hbar

    Cell width rules:
      n ≤ 5 → cells expand to fill main_canvas width
      n > 5 → each cell is _CELL_W_LARGE (200 px) wide; block is centered
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

        # canvas item IDs (main_canvas only)
        self._cell_rects:    dict[tuple, int] = {}
        self._cell_texts:    dict[tuple, int] = {}
        self._cell_chevrons: dict[tuple, tuple] = {}  # (line1_id, line2_id)

        # canvas handles
        self._canvas:      Optional[tk.Canvas] = None   # main (cells)
        self._col_canvas:  Optional[tk.Canvas] = None   # column headers
        self._row_canvas:  Optional[tk.Canvas] = None   # row headers
        self._legend_cvs:  Optional[tk.Canvas] = None   # legend strip

        self._combo:            Optional[tk.Toplevel] = None
        self._combo_close_fn                        = None
        self._tooltip_win: Optional[tk.Toplevel]    = None

        # x offset within col/main canvases (centering for n > 5)
        self._ox: int = _PADX

        # Current computed cell width
        self._cell_w: int = _CELL_W_LARGE

        # Smooth-scroll state
        self._scroll_vy:   float         = 0.0
        self._scroll_anim: Optional[str] = None

        self._build()

    # ------------------------------------------------------------------
    # Dynamic cell width
    # ------------------------------------------------------------------

    def _compute_cell_w(self, main_canvas_w: int) -> int:
        n = self._n
        if n > 5:
            return _CELL_W_LARGE
        # Expand cells to fill main canvas width (no row header here)
        available = main_canvas_w - 2 * _PADX - (n - 1) * _GAP
        return max(60, available // n)

    # ------------------------------------------------------------------
    # Geometry helpers  (coordinates within their respective canvases)
    # ------------------------------------------------------------------

    def _cell_bbox(self, i: int, j: int):
        """main_canvas coords of cell (i, j)."""
        x1 = self._ox + j * (self._cell_w + _GAP)
        y1 = _GAP + i * (_CELL_H + _GAP)
        return x1, y1, x1 + self._cell_w, y1 + _CELL_H

    def _col_hdr_bbox(self, j: int):
        """col_canvas coords of column header j."""
        x1 = self._ox + j * (self._cell_w + _GAP)
        y1 = _AXIS_H
        return x1, y1, x1 + self._cell_w, y1 + _COL_HDR_H - _GAP

    def _row_hdr_bbox(self, i: int):
        """row_canvas coords of row header i."""
        x1 = 2
        y1 = _GAP + i * (_CELL_H + _GAP)
        return x1, y1, _HDR_W - _GAP, y1 + _COL_HDR_H - _GAP

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Legend strip (spans full width, non-scrollable) ──────────
        leg = tk.Canvas(self, bg=COLOR_BG, height=_LEGEND_H,
                        highlightthickness=0)
        leg.grid(row=0, column=0, columnspan=3, sticky="ew")
        leg.bind("<Configure>", lambda e: self._draw_legend(e.width))
        self._legend_cvs = leg

        # ── Corner (axis label, fixed) ────────────────────────────────
        corner_h = _AXIS_H + _COL_HDR_H
        corner = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0,
                           width=_HDR_W + _GAP, height=corner_h)
        corner.grid(row=1, column=0, sticky="nsew", padx=(_HDR_LEFT_PAD, 0))
        self._corner = corner

        # ── Column headers (scrolls X, synced with main) ─────────────
        col_cvs = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0,
                            height=corner_h)
        col_cvs.grid(row=1, column=1, sticky="ew", padx=(0, MATRIX_PADX))
        self._col_canvas = col_cvs

        # ── Row headers (scrolls Y, synced with main) ─────────────────
        row_cvs = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0,
                            width=_HDR_W + _GAP)
        row_cvs.grid(row=2, column=0, sticky="ns", padx=(_HDR_LEFT_PAD, 0))
        self._row_canvas = row_cvs

        # ── Main canvas (cells, scrolls X+Y) ─────────────────────────
        main = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        main.grid(row=2, column=1, sticky="nsew", padx=(0, MATRIX_PADX))
        self._canvas = main

        # ── Pill scrollbars ───────────────────────────────────────────
        self._vbar  = _PillScrollbar(self, orient="vertical",   command=main.yview)
        self._hbar  = _PillScrollbar(self, orient="horizontal", command=main.xview)
        self._hbar_shown = False

        main.configure(
            xscrollcommand=self._on_x_scroll,
            yscrollcommand=self._on_y_scroll,
        )

        # Mouse-wheel scrolls when hovering the scrollbars
        self._vbar.bind("<MouseWheel>", lambda e: self._add_scroll_velocity(-e.delta / 120))
        self._vbar.bind("<Button-4>",   lambda e: self._add_scroll_velocity(-1))
        self._vbar.bind("<Button-5>",   lambda e: self._add_scroll_velocity( 1))
        self._hbar.bind("<MouseWheel>", lambda e: self._add_scroll_velocity(-e.delta / 120))
        self._hbar.bind("<Button-4>",   lambda e: self._add_scroll_velocity(-1))
        self._hbar.bind("<Button-5>",   lambda e: self._add_scroll_velocity( 1))

        for w in (main, row_cvs, col_cvs):
            w.bind("<MouseWheel>", lambda e: self._add_scroll_velocity(-e.delta / 120))
            w.bind("<Button-4>",   lambda e: self._add_scroll_velocity(-1))
            w.bind("<Button-5>",   lambda e: self._add_scroll_velocity( 1))

        main.bind("<Configure>", self._on_configure)
        main.bind("<Button-1>",  self._on_canvas_click)

        for cvs in (row_cvs, col_cvs):
            cvs.bind("<Button-1>",
                     lambda e: self._close_active_combo() or "break", add="+")

        self.after_idle(self._redraw)

    # ------------------------------------------------------------------
    # Scroll sync
    # ------------------------------------------------------------------

    def _on_x_scroll(self, first, last):
        self._col_canvas.xview_moveto(first)
        needs = not (float(first) <= 0.0 and float(last) >= 1.0)
        self._hbar.set(first, last)
        self._hbar_shown = needs
        if needs:
            self._hbar.grid(row=3, column=1, sticky="ew",
                            padx=(0, MATRIX_PADX), pady=(4, 0))
        else:
            self._hbar.grid_remove()

    def _on_y_scroll(self, first, last):
        self._row_canvas.yview_moveto(first)
        needs = not (float(first) <= 0.0 and float(last) >= 1.0)
        self._vbar.set(first, last)
        if needs:
            self._vbar.grid(row=2, column=2, sticky="ns", padx=(20, 4))
        else:
            self._vbar.grid_remove()

    # ------------------------------------------------------------------
    # Smooth scrolling
    # ------------------------------------------------------------------

    _SCROLL_STEP   = 0.15
    _SCROLL_DECAY  = 0.85
    _SCROLL_CUTOFF = 0.0002
    _SCROLL_FRAME  = 16         # ~60 fps

    def _add_scroll_velocity(self, ticks: float):
        self._scroll_vy += ticks * self._SCROLL_STEP
        self._scroll_vy = max(-0.5, min(0.5, self._scroll_vy))
        if self._scroll_anim is None:
            self._scroll_tick()

    def _scroll_tick(self):
        if abs(self._scroll_vy) < self._SCROLL_CUTOFF:
            self._scroll_vy   = 0.0
            self._scroll_anim = None
            return
        canvas  = self._canvas
        current = float(canvas.yview()[0])
        canvas.yview_moveto(max(0.0, min(1.0, current + self._scroll_vy)))
        self._scroll_vy  *= self._SCROLL_DECAY
        self._scroll_anim = self.after(self._SCROLL_FRAME, self._scroll_tick)

    # ------------------------------------------------------------------
    # Redraw
    # ------------------------------------------------------------------

    def _on_configure(self, event):
        self._redraw(event.width, event.height)

    def _redraw(self, canvas_w: int = None, canvas_h: int = None):
        main = self._canvas
        if canvas_w is None:
            canvas_w = main.winfo_width()
        if canvas_h is None:
            canvas_h = main.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        n = self._n
        self._cell_w = self._compute_cell_w(canvas_w)
        cw = self._cell_w

        # x offset (centering for n > 5)
        if n > 5:
            total_cells_w = n * (cw + _GAP)
            self._ox = max(0, (canvas_w - total_cells_w) // 2)
        else:
            self._ox = 0

        # Scroll regions
        content_w = self._ox + n * (cw + _GAP) + _PADX
        content_h = _GAP + n * (_CELL_H + _GAP) + _GAP
        hdr_h     = _AXIS_H + _COL_HDR_H

        if n > 5:
            sr_w = max(canvas_w, content_w)
            sr_h = max(canvas_h, content_h)
        else:
            sr_w = canvas_w
            sr_h = canvas_h

        main.configure(scrollregion=(0, 0, sr_w, sr_h))
        self._col_canvas.configure(scrollregion=(0, 0, sr_w, hdr_h))
        self._row_canvas.configure(scrollregion=(0, 0, _HDR_W + _GAP, sr_h))

        # Clear all
        main.delete("all")
        self._col_canvas.delete("all")
        self._row_canvas.delete("all")
        self._corner.delete("all")
        self._cell_rects.clear()
        self._cell_texts.clear()

        self._draw_legend(self._legend_cvs.winfo_width())
        self._draw_col_hdrs()
        self._draw_row_hdrs()
        self._draw_cells()

    # ------------------------------------------------------------------
    # Legend
    # ------------------------------------------------------------------

    def _draw_legend(self, canvas_w: int):
        canvas = self._legend_cvs
        if canvas_w <= 1:
            return
        canvas.delete("all")
        label_y = _LEGEND_H // 2

        lbl_text = "Click a cell to rate it:"
        _tmp = canvas.create_text(0, -1000, text=lbl_text,
                                  font=(FONT_FAMILY, 9, "italic"), anchor="w")
        lbl_w = canvas.bbox(_tmp)[2] - canvas.bbox(_tmp)[0]
        canvas.delete(_tmp)

        badge_widths = []
        for rating in COHERENCE_RATINGS:
            _tmp = canvas.create_text(0, -1000, text=rating,
                                      font=(FONT_FAMILY, _BADGE_FONT_SIZE), anchor="w")
            tw = canvas.bbox(_tmp)[2] - canvas.bbox(_tmp)[0]
            canvas.delete(_tmp)
            badge_widths.append(tw + 2 * _BADGE_PAD_X)

        total_w = lbl_w + 10 + sum(badge_widths) + _BADGE_GAP * (len(badge_widths) - 1)
        start_x = max(0, (canvas_w - total_w) // 2)

        canvas.create_text(start_x, label_y,
                           text=lbl_text,
                           font=(FONT_FAMILY, 9, "italic"),
                           fill="#a3a3a3", anchor="w")

        x = start_x + lbl_w + 10
        badge_y1 = label_y - _BADGE_H // 2
        badge_y2 = badge_y1 + _BADGE_H
        for rating, bw in zip(COHERENCE_RATINGS, badge_widths):
            bg = RATING_COLORS[rating]
            fg = RATING_TEXT_COLORS[rating]
            _round_rect(canvas, x, badge_y1, x + bw, badge_y2,
                        _BADGE_RADIUS, fill=bg, outline="")
            canvas.create_text(x + bw // 2, label_y, text=rating,
                               font=(FONT_FAMILY, _BADGE_FONT_SIZE), fill=fg)
            x += bw + _BADGE_GAP

    # ------------------------------------------------------------------
    # Column headers  (drawn on _col_canvas)
    # ------------------------------------------------------------------

    def _draw_col_hdrs(self):
        canvas   = self._col_canvas
        codes    = self._matrix.codes
        policies = self._matrix.policies

        # Axis label
        canvas.create_text(
            self._ox + 4, _AXIS_H // 2,
            text="<-- Influencing  |  Influenced -->",
            font=(FONT_FAMILY, 9, "italic"),
            fill="#a3a3a3",
            anchor="w",
        )

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
                lambda e, t=tip, bx=x1, by=y2:
                    self._show_tooltip(t, bx, by, self._col_canvas))
            canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

    # ------------------------------------------------------------------
    # Row headers  (drawn on _row_canvas)
    # ------------------------------------------------------------------

    def _draw_row_hdrs(self):
        canvas   = self._row_canvas
        codes    = self._matrix.codes
        policies = self._matrix.policies

        for i, code in enumerate(codes):
            x1, y1, x2, y2 = self._row_hdr_bbox(i)
            tag = f"rhdr_{i}"
            _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS,
                        fill=_HDR_BG, outline="", tags=tag)
            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                               text=code,
                               font=(FONT_FAMILY, _HDR_FONT_SIZE),
                               fill=_HDR_FG, tags=tag)

            tip = f"{code}:  {policies[i]}"
            canvas.tag_bind(tag, "<Enter>",
                lambda e, t=tip, bx=x2, by=y2:
                    self._show_tooltip(t, bx, by, self._row_canvas))
            canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

    # ------------------------------------------------------------------
    # Cells  (drawn on _canvas / main_canvas)
    # ------------------------------------------------------------------

    def _draw_cells(self):
        canvas = self._canvas
        n      = self._n

        for i in range(n):
            for j in range(n):
                is_diag = (i == j)
                value   = self._matrix.get_rating(i, j)
                x1, y1, x2, y2 = self._cell_bbox(i, j)

                if is_diag:
                    bg   = "#f5f5f5"
                    fg   = "#a3a3a3"
                    text = DIAGONAL_VALUE
                elif value:
                    bg   = RATING_COLORS.get(value, "#ffffff")
                    fg   = RATING_TEXT_COLORS.get(value, COLOR_TEXT)
                    text = value
                else:
                    bg   = "#ffffff"
                    fg   = "#a3a3a3"
                    text = "--"

                if is_diag:
                    outline = "#e6e6e6"
                elif value:
                    outline = "#f5f5f5"
                else:
                    outline = "#f5f5f5"
                rid = _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS,
                                  fill=bg, outline=outline)
                tid = canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                        text=text,
                                        font=(FONT_FAMILY, _CELL_FONT_SIZE),
                                        fill=fg)
                # Chevron-down icon at right of cell (all selectable/non-diagonal cells)
                if not is_diag:
                    cw, ch  = 8, 4          # chevron width and height
                    pad     = 12            # distance from right edge
                    cx      = x2 - pad
                    cy      = (y1 + y2) // 2
                    c1 = canvas.create_line(cx - cw//2, cy - ch//2,
                                            cx,          cy + ch//2,
                                            fill="#a3a3a3", width=1.35,
                                            capstyle="round", joinstyle="round")
                    c2 = canvas.create_line(cx,          cy + ch//2,
                                            cx + cw//2,  cy - ch//2,
                                            fill="#a3a3a3", width=1.35,
                                            capstyle="round", joinstyle="round")
                    self._cell_chevrons[(i, j)] = (c1, c2)
                self._cell_rects[(i, j)] = rid
                self._cell_texts[(i, j)] = tid

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _on_canvas_click(self, event):
        if self._combo is not None:
            self._close_active_combo()
            return "break"

        main = self._canvas
        cx   = main.canvasx(event.x)
        cy   = main.canvasy(event.y)
        n    = self._n

        j = int((cx - self._ox) / (self._cell_w + _GAP))
        i = int((cy - _GAP)     / (_CELL_H     + _GAP))

        if not (0 <= i < n and 0 <= j < n):
            return
        if i == j:
            return

        x1, y1, x2, y2 = self._cell_bbox(i, j)
        if not (x1 <= cx <= x2 and y1 <= cy <= y2):
            return

        self._open_cell_dropdown(i, j)

    def _open_cell_dropdown(self, i: int, j: int):
        if self._combo is not None:
            return

        canvas = self._canvas
        matrix = self._matrix
        x1, y1, x2, y2 = self._cell_bbox(i, j)
        cell_w = x2 - x1

        _ITEM_H = 38
        _PAD    = 1
        popup_h = len(COHERENCE_RATINGS) * _ITEM_H + _PAD * 2

        cell_top_screen_y = canvas.winfo_rooty() + int(y1 - canvas.canvasy(0))
        cell_bot_screen_y = canvas.winfo_rooty() + int(y2 - canvas.canvasy(0))
        screen_x          = canvas.winfo_rootx() + int(x1 - canvas.canvasx(0))
        screen_h          = self.winfo_screenheight()

        # Show above the cell if not enough room below
        if cell_bot_screen_y + popup_h + 4 > screen_h - 20:
            screen_y = cell_top_screen_y - popup_h - 4
        else:
            screen_y = cell_bot_screen_y + 4

        # Highlight active cell
        canvas.itemconfig(self._cell_rects[(i, j)], outline="#426387")

        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True)
        popup.configure(bg="#e0e0e0")
        popup.wm_geometry(f"{cell_w}x{popup_h}+{screen_x}+{screen_y}")

        for idx, rating in enumerate(COHERENCE_RATINGS):
            lbl = tk.Label(popup, text=rating, bg="white", fg=COLOR_TEXT,
                           font=(FONT_FAMILY, _CELL_FONT_SIZE),
                           anchor="w", padx=12)
            lbl.place(x=_PAD, y=_PAD + idx * _ITEM_H,
                      width=cell_w - _PAD * 2, height=_ITEM_H)

            def _on_enter(e, b=lbl):  b.configure(bg="#f0f4f8")
            def _on_leave(e, b=lbl):  b.configure(bg="white")
            def _on_pick(e, r=rating):
                matrix.set_rating(i, j, r)
                self._on_change(i, j, r)
                self._update_cell_display(i, j, r)
                _close()

            lbl.bind("<Enter>",     _on_enter)
            lbl.bind("<Leave>",     _on_leave)
            lbl.bind("<Button-1>",  _on_pick)

        root    = self.winfo_toplevel()
        _bid    = [None]

        def _close(e=None):
            if self._combo is not None:
                if _bid[0]:
                    root.unbind("<Button-1>", _bid[0])
                    _bid[0] = None
                canvas.itemconfig(self._cell_rects[(i, j)], outline="#f5f5f5")
                try:
                    self._combo.destroy()
                except Exception:
                    pass
                self._combo          = None
                self._combo_close_fn = None
            if self._canvas:
                self._canvas.focus_set()

        self._combo          = popup
        self._combo_close_fn = _close

        _bid[0] = root.bind("<Button-1>", lambda e: _close(), "+")

        popup.bind("<Escape>", _close)

    def _close_active_combo(self, e=None):
        if self._combo_close_fn is not None:
            self._combo_close_fn()
        elif self._combo is not None:
            try:
                self._combo.grab_release()
                self._combo.destroy()
            except Exception:
                pass
            self._combo = None
            if self._canvas:
                self._canvas.focus_set()

    # ------------------------------------------------------------------
    # Tooltip
    # ------------------------------------------------------------------

    def _show_tooltip(self, text: str, canvas_x: int, canvas_y: int,
                      src: tk.Canvas = None):
        self._hide_tooltip()
        src      = src or self._canvas
        screen_x = src.winfo_rootx() + int(canvas_x - src.canvasx(0))
        screen_y = src.winfo_rooty() + int(canvas_y - src.canvasy(0)) + 4

        tw = tk.Toplevel(src)
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
        canvas = self._canvas
        bg = RATING_COLORS.get(value, "#ffffff")
        fg = RATING_TEXT_COLORS.get(value, COLOR_TEXT)
        canvas.itemconfig(self._cell_rects[(i, j)], fill=bg, outline="#f5f5f5")
        canvas.itemconfig(self._cell_texts[(i, j)], text=value, fill=fg)

    def refresh_cell(self, row: int, col: int):
        """Re-read the model and repaint a single cell (call after external edits)."""
        value = self._matrix.get_rating(row, col)
        if value:
            self._update_cell_display(row, col, value)
        else:
            canvas = self._canvas
            canvas.itemconfig(self._cell_rects[(row, col)], fill="#fafafa", outline="#f5f5f5")
            canvas.itemconfig(self._cell_texts[(row, col)],
                              text="--", fill="#a3a3a3")
