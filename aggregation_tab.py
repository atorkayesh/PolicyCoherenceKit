# =============================================================================
# Policy Coherence Kit -- aggregation_tab.py
# AggregationTab: read-only aggregated matrix styled like the editable matrix.
# =============================================================================

import tkinter as tk
from typing import Optional

from aggregator import AggregationResult
from constants import (
    COHERENCE_RATINGS,
    FONT_FAMILY,
    COLOR_BG,
    COLOR_TEXT,
    COLOR_TEXT_LIGHT,
    MATRIX_PADX,
    RATING_COLORS,
    RATING_TEXT_COLORS,
)
from theme import (
    MATRIX_SCROLLBAR_THUMB,
    MATRIX_SCROLLBAR_THUMB_HOVER,
    MATRIX_SCROLLBAR_TROUGH,
    MATRIX_SCROLLBAR_W,
)


_CELL_H = 40
_HDR_W = 120
_CELL_W = 200
_GAP = 6
_AXIS_H = 40
_COL_HDR_H = 44
_PADX = 5
_HDR_LEFT_PAD = 28
_CELL_RADIUS = 8

_HDR_BG = "#426387"
_HDR_FG = "#f5f7fa"
_HDR_FONT_SIZE = 10
_CELL_FONT_SIZE = 12

_LEGEND_H = 40
_BADGE_H = 25
_BADGE_PAD_X = 10
_BADGE_FONT_SIZE = 10
_BADGE_GAP = 3
_BADGE_RADIUS = 4

_SCORE_COLORS = {
    3: ("#0B6E6E", "#ffffff"),
    2: ("#2A9D8F", "#ffffff"),
    1: ("#6BAF92", "#2d2d2d"),
    0: ("#B0B7C3", "#555555"),
    -1: ("#E9C46A", "#2d2d2d"),
    -2: ("#E76F51", "#ffffff"),
    -3: ("#9B2226", "#ffffff"),
}
_SCORE_TO_RATING = {
    3: "Indivisible",
    2: "Reinforcing",
    1: "Enabling",
    0: "Neutral",
    -1: "Constraining",
    -2: "Counteracting",
    -3: "Cancelling",
}


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


def _score_bucket(score: Optional[float]) -> int:
    if score is None:
        return 0
    clamped = max(-3.0, min(3.0, score))
    return min(_SCORE_TO_RATING, key=lambda bucket: abs(bucket - clamped))


class _PillScrollbar(tk.Canvas):
    _THICK = MATRIX_SCROLLBAR_W
    _TROUGH = MATRIX_SCROLLBAR_TROUGH
    _THUMB = MATRIX_SCROLLBAR_THUMB
    _THUMB_HOV = MATRIX_SCROLLBAR_THUMB_HOVER
    _MIN_THUMB = 28

    def __init__(self, parent, orient="vertical", command=None, **kwargs):
        self._orient = orient
        self._command = command
        self._first = 0.0
        self._last = 1.0
        self._drag_ref = None
        self._hovered = False

        setup = dict(highlightthickness=0, bg=self._TROUGH, bd=0)
        if orient == "vertical":
            setup["width"] = self._THICK
        else:
            setup["height"] = self._THICK
        super().__init__(parent, **setup, **kwargs)

        self.bind("<Configure>", self._redraw)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))

    def set(self, first, last):
        self._first = float(first)
        self._last = float(last)
        self._redraw()

    def _redraw(self, _event=None):
        self.delete("thumb")
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1:
            return

        thick = self._THICK
        radius = thick // 2
        if self._orient == "vertical":
            track = height
            thumb_len = max(self._MIN_THUMB, int(track * (self._last - self._first)))
            thumb_pos = min(int(track * self._first), track - thumb_len)
            x1, y1, x2, y2 = 0, thumb_pos, thick, thumb_pos + thumb_len
        else:
            track = width
            thumb_len = max(self._MIN_THUMB, int(track * (self._last - self._first)))
            thumb_pos = min(int(track * self._first), track - thumb_len)
            x1, y1, x2, y2 = thumb_pos, 0, thumb_pos + thumb_len, thick

        color = self._THUMB_HOV if self._hovered else self._THUMB
        points = [
            x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
        ]
        self.create_polygon(points, smooth=True, fill=color, outline="", tags="thumb")

    def _on_press(self, event):
        coord = event.y if self._orient == "vertical" else event.x
        self._drag_ref = (coord, self._first)

    def _on_drag(self, event):
        if self._drag_ref is None or self._command is None:
            return
        start, first0 = self._drag_ref
        coord = event.y if self._orient == "vertical" else event.x
        size = self.winfo_height() if self._orient == "vertical" else self.winfo_width()
        delta = (coord - start) / size
        new_first = max(0.0, min(1.0 - (self._last - self._first), first0 + delta))
        self._command("moveto", str(new_first))

    def _on_release(self, _event):
        self._drag_ref = None

    def _set_hover(self, state: bool):
        self._hovered = state
        self._redraw()


class AggregationTab(tk.Frame):
    """Read-only aggregated matrix rendered with the same visual system as MatrixWidget."""

    _SCROLL_STEP = 0.15
    _SCROLL_DECAY = 0.85
    _SCROLL_CUTOFF = 0.0002
    _SCROLL_FRAME = 16

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result = result
        self._n = result.n

        self._canvas: Optional[tk.Canvas] = None
        self._col_canvas: Optional[tk.Canvas] = None
        self._row_canvas: Optional[tk.Canvas] = None
        self._legend_cvs: Optional[tk.Canvas] = None
        self._corner: Optional[tk.Canvas] = None
        self._tooltip_win: Optional[tk.Toplevel] = None

        self._scroll_vy = 0.0
        self._scroll_anim: Optional[str] = None
        self._ox = _PADX

        self._build()

    def _build(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

        legend = tk.Canvas(self, bg=COLOR_BG, height=_LEGEND_H, highlightthickness=0)
        legend.grid(row=0, column=0, columnspan=3, sticky="ew")
        legend.bind("<Configure>", lambda e: self._draw_legend(e.width))
        self._legend_cvs = legend

        corner_h = _AXIS_H + _COL_HDR_H
        corner = tk.Canvas(
            self, bg=COLOR_BG, highlightthickness=0, width=_HDR_W + _GAP, height=corner_h
        )
        corner.grid(row=1, column=0, sticky="nsew", padx=(_HDR_LEFT_PAD, 0))
        self._corner = corner

        col_cvs = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0, height=corner_h)
        col_cvs.grid(row=1, column=1, sticky="ew", padx=(0, MATRIX_PADX))
        self._col_canvas = col_cvs

        row_cvs = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0, width=_HDR_W + _GAP)
        row_cvs.grid(row=2, column=0, sticky="ns", padx=(_HDR_LEFT_PAD, 0))
        self._row_canvas = row_cvs

        main = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        main.grid(row=2, column=1, sticky="nsew", padx=(0, MATRIX_PADX))
        self._canvas = main

        self._vbar = _PillScrollbar(self, orient="vertical", command=main.yview)
        self._hbar = _PillScrollbar(self, orient="horizontal", command=main.xview)

        main.configure(xscrollcommand=self._on_x_scroll, yscrollcommand=self._on_y_scroll)

        for widget in (main, row_cvs, col_cvs, self._vbar, self._hbar):
            widget.bind("<MouseWheel>", lambda e: self._add_scroll_velocity(-e.delta / 120))
            widget.bind("<Button-4>", lambda e: self._add_scroll_velocity(-1))
            widget.bind("<Button-5>", lambda e: self._add_scroll_velocity(1))

        for widget in (main, row_cvs, col_cvs):
            widget.bind("<Button-1>", lambda e: self._hide_tooltip(), add="+")

        main.bind("<Configure>", self._on_configure)
        self.after_idle(self._redraw)

    def _on_x_scroll(self, first, last):
        self._col_canvas.xview_moveto(first)
        self._hbar.set(first, last)
        needs = not (float(first) <= 0.0 and float(last) >= 1.0)
        if needs:
            self._hbar.grid(row=3, column=1, sticky="ew", padx=(0, MATRIX_PADX), pady=(4, 0))
        else:
            self._hbar.grid_remove()

    def _on_y_scroll(self, first, last):
        self._row_canvas.yview_moveto(first)
        self._vbar.set(first, last)
        needs = not (float(first) <= 0.0 and float(last) >= 1.0)
        if needs:
            self._vbar.grid(row=2, column=2, sticky="ns", padx=(20, 4))
        else:
            self._vbar.grid_remove()

    def _add_scroll_velocity(self, ticks: float):
        self._scroll_vy += ticks * self._SCROLL_STEP
        self._scroll_vy = max(-0.5, min(0.5, self._scroll_vy))
        if self._scroll_anim is None:
            self._scroll_tick()

    def _scroll_tick(self):
        if abs(self._scroll_vy) < self._SCROLL_CUTOFF:
            self._scroll_vy = 0.0
            self._scroll_anim = None
            return
        current = float(self._canvas.yview()[0])
        self._canvas.yview_moveto(max(0.0, min(1.0, current + self._scroll_vy)))
        self._scroll_vy *= self._SCROLL_DECAY
        self._scroll_anim = self.after(self._SCROLL_FRAME, self._scroll_tick)

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

        total_cells_w = self._n * (_CELL_W + _GAP)
        self._ox = max(0, (canvas_w - total_cells_w) // 2)

        content_w = self._ox + total_cells_w + _PADX
        content_h = _GAP + self._n * (_CELL_H + _GAP) + _GAP
        hdr_h = _AXIS_H + _COL_HDR_H
        scroll_w = max(canvas_w, content_w)
        scroll_h = max(canvas_h, content_h)

        main.configure(scrollregion=(0, 0, scroll_w, scroll_h))
        self._col_canvas.configure(scrollregion=(0, 0, scroll_w, hdr_h))
        self._row_canvas.configure(scrollregion=(0, 0, _HDR_W + _GAP, scroll_h))

        for canvas in (main, self._col_canvas, self._row_canvas, self._corner):
            canvas.delete("all")

        self._draw_legend(self._legend_cvs.winfo_width())
        self._draw_col_headers()
        self._draw_row_headers()
        self._draw_cells()

    def _draw_legend(self, canvas_w: int):
        canvas = self._legend_cvs
        if canvas_w <= 1:
            return
        canvas.delete("all")

        label_text = "Aggregated ratings:"
        label_y = _LEGEND_H // 2
        temp = canvas.create_text(0, -1000, text=label_text, font=(FONT_FAMILY, 9, "italic"))
        label_box = canvas.bbox(temp)
        canvas.delete(temp)
        label_w = label_box[2] - label_box[0]

        badge_widths = []
        for rating in COHERENCE_RATINGS:
            temp = canvas.create_text(0, -1000, text=rating, font=(FONT_FAMILY, _BADGE_FONT_SIZE))
            box = canvas.bbox(temp)
            canvas.delete(temp)
            badge_widths.append((box[2] - box[0]) + 2 * _BADGE_PAD_X)

        total_w = label_w + 10 + sum(badge_widths) + _BADGE_GAP * (len(badge_widths) - 1)
        start_x = max(0, (canvas_w - total_w) // 2)
        canvas.create_text(
            start_x,
            label_y,
            text=label_text,
            font=(FONT_FAMILY, 9, "italic"),
            fill=COLOR_TEXT_LIGHT,
            anchor="w",
        )

        x = start_x + label_w + 10
        y1 = label_y - _BADGE_H // 2
        y2 = y1 + _BADGE_H
        for rating, width in zip(COHERENCE_RATINGS, badge_widths):
            _round_rect(canvas, x, y1, x + width, y2, _BADGE_RADIUS, fill=RATING_COLORS[rating], outline="")
            canvas.create_text(
                x + width // 2,
                label_y,
                text=rating,
                font=(FONT_FAMILY, _BADGE_FONT_SIZE),
                fill=RATING_TEXT_COLORS[rating],
            )
            x += width + _BADGE_GAP

    def _draw_col_headers(self):
        canvas = self._col_canvas
        canvas.create_text(
            self._ox + 4,
            _AXIS_H // 2,
            text="<-- Influencing  |  Influenced -->",
            font=(FONT_FAMILY, 9, "italic"),
            fill=COLOR_TEXT_LIGHT,
            anchor="w",
        )

        for j, code in enumerate(self._result.codes):
            x1 = self._ox + j * (_CELL_W + _GAP)
            y1 = _AXIS_H
            x2 = x1 + _CELL_W
            y2 = y1 + _COL_HDR_H - _GAP
            tag = f"col_{j}"
            _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS, fill=_HDR_BG, outline="", tags=tag)
            canvas.create_text(
                (x1 + x2) // 2,
                (y1 + y2) // 2,
                text=code,
                font=(FONT_FAMILY, _HDR_FONT_SIZE),
                fill=_HDR_FG,
                tags=tag,
            )
            tip = f"{code}: {self._result.policies[j]}"
            canvas.tag_bind(
                tag,
                "<Enter>",
                lambda e, t=tip, bx=x1, by=y2: self._show_tooltip(t, bx, by, self._col_canvas),
            )
            canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

    def _draw_row_headers(self):
        canvas = self._row_canvas
        for i, code in enumerate(self._result.codes):
            x1 = 2
            y1 = _GAP + i * (_CELL_H + _GAP)
            x2 = _HDR_W - _GAP
            y2 = y1 + _COL_HDR_H - _GAP
            tag = f"row_{i}"
            _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS, fill=_HDR_BG, outline="", tags=tag)
            canvas.create_text(
                (x1 + x2) // 2,
                (y1 + y2) // 2,
                text=code,
                font=(FONT_FAMILY, _HDR_FONT_SIZE),
                fill=_HDR_FG,
                tags=tag,
            )
            tip = f"{code}: {self._result.policies[i]}"
            canvas.tag_bind(
                tag,
                "<Enter>",
                lambda e, t=tip, bx=x2, by=y2: self._show_tooltip(t, bx, by, self._row_canvas),
            )
            canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

    def _draw_cells(self):
        canvas = self._canvas
        for i in range(self._n):
            for j in range(self._n):
                score = self._result.scores.get((i, j), 0.0)
                bucket = 0 if i == j else _score_bucket(score)
                label = _SCORE_TO_RATING[bucket]
                bg, fg = _SCORE_COLORS[bucket]

                x1 = self._ox + j * (_CELL_W + _GAP)
                y1 = _GAP + i * (_CELL_H + _GAP)
                x2 = x1 + _CELL_W
                y2 = y1 + _CELL_H
                tag = f"cell_{i}_{j}"
                _round_rect(canvas, x1, y1, x2, y2, _CELL_RADIUS, fill=bg, outline="#f5f5f5", tags=tag)
                canvas.create_text(
                    (x1 + x2) // 2,
                    (y1 + y2) // 2,
                    text=label,
                    font=(FONT_FAMILY, _CELL_FONT_SIZE),
                    fill=fg,
                    tags=tag,
                )

                if i != j:
                    tip = (
                        f"{self._result.codes[i]} -> {self._result.codes[j]}\n"
                        f"{label} ({score:.2f})"
                    )
                else:
                    tip = f"{self._result.codes[i]} -> {self._result.codes[j]}\nNeutral (diagonal)"
                canvas.tag_bind(
                    tag,
                    "<Enter>",
                    lambda e, t=tip, bx=x1, by=y2: self._show_tooltip(t, bx, by, self._canvas),
                )
                canvas.tag_bind(tag, "<Leave>", lambda e: self._hide_tooltip())

    def _show_tooltip(self, text: str, base_x: int, base_y: int, canvas: tk.Canvas):
        self._hide_tooltip()
        x = canvas.winfo_rootx() + int(base_x) + 10
        y = canvas.winfo_rooty() + int(base_y) + 8
        self._tooltip_win = win = tk.Toplevel(self)
        win.wm_overrideredirect(True)
        win.wm_geometry(f"+{x}+{y}")
        tk.Label(
            win,
            text=text,
            justify="left",
            background="#fffbe6",
            foreground=COLOR_TEXT,
            relief="solid",
            borderwidth=1,
            font=(FONT_FAMILY, 9),
            padx=8,
            pady=4,
            wraplength=320,
        ).pack()

    def _hide_tooltip(self, _event=None):
        if self._tooltip_win is not None:
            self._tooltip_win.destroy()
            self._tooltip_win = None
