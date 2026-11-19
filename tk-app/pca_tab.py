# =============================================================================
# Policy Coherence Kit -- pca_tab.py
# PCATab: 2D PCA scatter plot of policy influence profiles.
#
# Input  : AggregationResult  (n x n aggregated score matrix)
# Method : each policy = row vector (outgoing scores, diagonal excluded)
#          -> standardise -> SVD-based PCA -> project onto PC1, PC2
# Display: scatter plot on tkinter Canvas, policy codes as labels,
#          tooltips showing full name, optional entropy-based colouring.
# =============================================================================

import math
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from typing import List, Tuple, Optional

from aggregator import AggregationResult, aggregation_method_label
from range_of_influence_tab import compute_entropy, _CAT_COLORS
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_PAGE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_PAGE_TITLE,
    CURSOR_HAND,
)
from theme import (
    TOPBAR_EXCEL_BG,
    TOPBAR_EXCEL_HOVER_BG,
    TOPBAR_EXCEL_BORDER,
    TOPBAR_EXCEL_FG,
    TOPBAR_EXCEL_HEIGHT,
    TOPBAR_EXCEL_RADIUS,
    TOPBAR_EXCEL_ICON_SIZE,
    TOPBAR_EXCEL_ICON_GAP,
    TOPBAR_EXCEL_PADX,
)

# Default point colour (single-colour mode)
_POINT_COLOR   = "#2c4a6e"
_POINT_RADIUS  = 16
_CANVAS_W      = 680
_CANVAS_H      = 520
_MARGIN        = 60


def _rrect_pts(x1, y1, x2, y2, r, steps=10):
    pts = []
    for cx, cy, a0 in [
        (x2 - r, y1 + r, -90),
        (x2 - r, y2 - r, 0),
        (x1 + r, y2 - r, 90),
        (x1 + r, y1 + r, 180),
    ]:
        for i in range(steps + 1):
            a = math.radians(a0 + 90 * i / steps)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


# =============================================================================
# PCA calculation (pure numpy)
# =============================================================================

def compute_pca(result: AggregationResult):
    """
    Run PCA on the policy influence profiles.

    Returns
    -------
    coords        : list of (x, y) projected coordinates, one per policy
    explained     : (pct_pc1, pct_pc2) as floats 0-100
    valid         : True if PCA succeeded, False if n < 3
    """
    try:
        import numpy as np
    except ImportError:
        raise ImportError(
            "numpy is required for PCA.\n"
            "Install it with:  pip install numpy"
        )

    n      = result.n
    scores = result.scores

    if n < 3:
        return [], (0.0, 0.0), False

    # Build data matrix X: shape (n, n-1)
    # Each row = outgoing scores of policy i (diagonal excluded)
    X = np.array([
        [scores.get((i, j), 0.0) or 0.0 for j in range(n) if j != i]
        for i in range(n)
    ], dtype=float)

    # Standardise: subtract column mean, divide by std (avoid div by zero)
    means = X.mean(axis=0)
    stds  = X.std(axis=0)
    stds[stds == 0] = 1.0
    X_std = (X - means) / stds

    # SVD: X_std = U S Vt
    U, S, Vt = np.linalg.svd(X_std, full_matrices=False)

    # Explained variance
    var        = S ** 2
    total_var  = var.sum()
    if total_var == 0:
        explained = (0.0, 0.0)
    else:
        pct = (var / total_var * 100).tolist()
        explained = (
            round(pct[0], 1) if len(pct) > 0 else 0.0,
            round(pct[1], 1) if len(pct) > 1 else 0.0,
        )

    # Project onto PC1, PC2
    coords_2d = (X_std @ Vt[:2].T).tolist()   # shape (n, 2)
    coords    = [(row[0], row[1]) for row in coords_2d]

    return coords, explained, True


# =============================================================================
# PCATab
# =============================================================================

class PCATab(tk.Frame):
    """
    Interactive PCA scatter plot tab.
    Toggle button switches between single-colour and entropy-category colouring.
    """

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result       = result
        self._entropy_rows = compute_entropy(result)
        self._colour_mode  = tk.BooleanVar(value=False)  # False = single colour

        try:
            self._coords, self._explained, self._valid = compute_pca(result)
        except ImportError as exc:
            self._valid = False
            self._error = str(exc)
        else:
            self._error = None

        self._tooltip_win: Optional[tk.Toplevel] = None
        self._redraw_pending: Optional[str] = None  # Debounce timer ID
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()

        if not self._valid:
            msg = self._error or "PCA requires at least 3 policies."
            tk.Label(
                self, text=msg,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
                bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            ).pack(expand=True)
            return

        self._build_controls()
        self._build_canvas()
        self._build_hover_hint()
        self._build_legend_bar()

    # ------------------------------------------------------------------

    def _build_info_bar(self):
        bar = tk.Frame(self, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_columnconfigure(1, weight=0)

        content = tk.Frame(bar, bg=COLOR_BG)
        content.grid(row=0, column=0, sticky="w", padx=16)

        method_label = aggregation_method_label(self._result)

        tk.Label(
            content,
            text=f"PCA  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_PAGE_TITLE, "normal"),
            bg=COLOR_BG, fg=COLOR_PAGE_TITLE,
        ).pack(side="left")

        if self._valid:
            pct1, pct2 = self._explained
            tk.Label(
                content,
                text=(f"PC1: {pct1}%   PC2: {pct2}%   "
                      f"Total explained: {round(pct1+pct2,1)}%"),
                font=(FONT_FAMILY, 11, "italic"),
                bg=COLOR_BG, fg="#a3a3a3",
            ).pack(side="left", padx=(18, 0))

    def _build_save_button(self, parent: tk.Misc):
        label = "Save as PNG"
        btn_font = tkFont.Font(family=FONT_FAMILY, size=11)
        text_w = btn_font.measure(label)
        btn_w = TOPBAR_EXCEL_PADX + TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP + text_w + TOPBAR_EXCEL_PADX

        btn = tk.Canvas(
            parent,
            width=btn_w + 2,
            height=TOPBAR_EXCEL_HEIGHT + 2,
            bg=COLOR_BG,
            highlightthickness=0,
            cursor=CURSOR_HAND,
        )
        btn.grid(row=0, column=1, sticky="e", padx=16)

        hover = {"value": 0.0, "job": None}

        def _draw(color: str):
            btn.delete("all")
            pts = _rrect_pts(1, 1, btn_w + 1, TOPBAR_EXCEL_HEIGHT + 1, TOPBAR_EXCEL_RADIUS)
            btn.create_polygon(*pts, fill=color, outline=TOPBAR_EXCEL_BORDER, width=1)
            cy = 1 + TOPBAR_EXCEL_HEIGHT // 2
            content_w = TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP + text_w
            ix = 1 + (btn_w - content_w) // 2
            iy = 1 + (TOPBAR_EXCEL_HEIGHT - TOPBAR_EXCEL_ICON_SIZE) // 2
            self._draw_image_down_icon(btn, ix, iy, TOPBAR_EXCEL_FG)
            btn.create_text(
                ix + TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP,
                cy,
                text=label,
                fill=TOPBAR_EXCEL_FG,
                anchor="w",
                font=btn_font,
            )

        def _animate(target: float):
            if hover["job"]:
                btn.after_cancel(hover["job"])
                hover["job"] = None

            def _tick():
                diff = target - hover["value"]
                if abs(diff) < 0.02:
                    hover["value"] = target
                    _draw(TOPBAR_EXCEL_HOVER_BG if target else TOPBAR_EXCEL_BG)
                    hover["job"] = None
                    return
                hover["value"] += diff * 0.3
                mix = TOPBAR_EXCEL_HOVER_BG if hover["value"] >= 0.5 else TOPBAR_EXCEL_BG
                _draw(mix)
                hover["job"] = btn.after(16, _tick)

            _tick()

        btn.bind("<Enter>", lambda _e: _animate(1.0))
        btn.bind("<Leave>", lambda _e: _animate(0.0))
        btn.bind("<Button-1>", lambda _e: self._save_canvas())
        _draw(TOPBAR_EXCEL_BG)

    def _draw_image_down_icon(self, canvas: tk.Canvas, ox: int, oy: int, fg: str):
        s = TOPBAR_EXCEL_ICON_SIZE / 24.0
        lw = 1.35
        kw = dict(fill=fg, width=lw, capstyle="round", joinstyle="round")
        canvas.create_line(
            10.3*s+ox, 21*s+oy, 5*s+ox, 21*s+oy,
            3*s+ox, 19*s+oy, 3*s+ox, 5*s+oy,
            5*s+ox, 3*s+oy, 19*s+ox, 3*s+oy,
            21*s+ox, 5*s+oy, 21*s+ox, 15*s+oy,
            **kw,
        )
        canvas.create_line(
            21*s+ox, 15*s+oy, 17.9*s+ox, 11.9*s+oy,
            15.086*s+ox, 11.914*s+oy, 6*s+ox, 21*s+oy,
            **kw,
        )
        canvas.create_line(17*s+ox, 16.5*s+oy, 17*s+ox, 22*s+oy, **kw)
        canvas.create_line(14*s+ox, 19*s+oy, 17*s+ox, 22*s+oy, 20*s+ox, 19*s+oy, **kw)
        canvas.create_oval(7*s+ox, 7*s+oy, 11*s+ox, 11*s+oy, outline=fg, width=lw)

    # ------------------------------------------------------------------

    def _build_controls(self):
        ctrl = tk.Frame(self, bg=COLOR_BG)
        ctrl.pack(fill="x", padx=16, pady=6)

        tk.Label(
            ctrl,
            text="Colour by entropy category:",
            font=(FONT_FAMILY, 10, "normal"),
            bg=COLOR_BG, fg="#a3a3a3",
        ).pack(side="left", padx=(0, 6))

        cb = tk.Checkbutton(
            ctrl,
            variable=self._colour_mode,
            command=self._redraw,
            bg=COLOR_BG,
            activebackground=COLOR_BG,
            cursor=CURSOR_HAND,
        )
        cb.pack(side="left")

    # ------------------------------------------------------------------

    def _build_canvas(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        self._canvas = tk.Canvas(
            frame,
            bg="#ffffff",
            highlightthickness=2,
            highlightbackground=COLOR_ACCENT,
        )
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda e: self._redraw_debounced())

    def _build_hover_hint(self):
        self._hover_hint = tk.Label(
            self,
            text="Hover over a point to see the full policy name.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG,
            fg="#a3a3a3",
        )
        self._hover_hint.pack(anchor="w", padx=16, pady=(0, 8))

    # ------------------------------------------------------------------

    def _save_canvas(self):
        """Export the canvas to a PNG file."""
        from tkinter import filedialog
        try:
            from PIL import ImageGrab
        except ImportError:
            try:
                import subprocess, os
                path = filedialog.asksaveasfilename(
                    title="Save PCA plot",
                    defaultextension=".ps",
                    filetypes=[("PostScript", "*.ps"), ("All files", "*.*")],
                    initialfile="pca_plot.ps",
                )
                if path:
                    self._canvas.postscript(file=path, colormode="color")
                    import tkinter.messagebox as mb
                    mb.showinfo("Saved", f"Saved as PostScript:\n{path}\n\n"
                               "Open with any PS viewer or convert with Ghostscript.")
            except Exception as exc:
                import tkinter.messagebox as mb
                mb.showerror("Save Error", str(exc))
            return
        path = filedialog.asksaveasfilename(
            title="Save PCA plot",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All files", "*.*")],
            initialfile="pca_plot.png",
        )
        if not path:
            return
        x = self._canvas.winfo_rootx()
        y = self._canvas.winfo_rooty()
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        ImageGrab.grab(bbox=(x, y, x+w, y+h)).save(path)
        import tkinter.messagebox as mb
        mb.showinfo("Saved", f"PCA plot saved to:\n{path}")

    def _build_legend_bar(self):
        self._legend_frame = tk.Frame(self, bg=COLOR_BG)
        self._legend_frame.pack(fill="x", padx=16, pady=(0, 8))
        self._legend_frame.grid_columnconfigure(0, weight=1)
        self._legend_frame.grid_columnconfigure(1, weight=0)
        self._update_legend()

    # ------------------------------------------------------------------

    def _update_legend(self):
        for w in self._legend_frame.winfo_children():
            w.destroy()

        if self._colour_mode.get():
            left = tk.Frame(self._legend_frame, bg=COLOR_BG)
            left.grid(row=0, column=0, sticky="ew")

            tk.Label(
                left,
                text="Entropy categories:",
                font=(FONT_FAMILY, 10, "normal"),
                bg=COLOR_BG, fg="#a3a3a3",
            ).pack(side="left", padx=(0, 16))
            for cat, (bg, fg) in _CAT_COLORS.items():
                item = tk.Frame(left, bg=COLOR_BG)
                item.pack(side="left", padx=(0, 8))
                tk.Label(
                    item,
                    text=f"  {cat}  ",
                    font=(FONT_FAMILY, FONT_SIZE_SMALL),
                    bg=bg, fg=fg,
                    padx=6, pady=2, relief="flat",
                ).pack(side="left")

        self._build_save_button(self._legend_frame)

    # ------------------------------------------------------------------

    def _redraw_debounced(self):
        """Debounced version of _redraw to prevent excessive redraws."""
        # Cancel any pending redraw
        if self._redraw_pending is not None:
            self.after_cancel(self._redraw_pending)
        # Schedule redraw after 50ms of no new events
        self._redraw_pending = self.after(50, self._redraw)

    def _redraw(self):
        self._redraw_pending = None
        self._update_legend()
        canvas = self._canvas
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10 or h < 10:
            return

        coords   = self._coords
        n        = self._result.n
        codes    = self._result.codes
        policies = self._result.policies

        if not coords:
            return

        # ---- Compute scale ----
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        x_range = x_max - x_min or 1.0
        y_range = y_max - y_min or 1.0

        m = _MARGIN

        def to_canvas(x, y):
            cx = m + (x - x_min) / x_range * (w - 2 * m)
            cy = (h - m) - (y - y_min) / y_range * (h - 2 * m)
            return cx, cy

        # ---- Draw axes ----
        # X axis
        ax_y = to_canvas(0, 0)[1] if y_min <= 0 <= y_max else h // 2
        canvas.create_line(m, ax_y, w - m, ax_y,
                           fill="#cccccc", width=1, dash=(4, 4))
        # Y axis
        ax_x = to_canvas(0, 0)[0] if x_min <= 0 <= x_max else w // 2
        canvas.create_line(ax_x, m, ax_x, h - m,
                           fill="#cccccc", width=1, dash=(4, 4))

        # ---- Axis labels ----
        pct1, pct2 = self._explained
        canvas.create_text(
            w - m + 4, ax_y,
            text=f"PC1 ({pct1}%)", anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_SMALL), fill=COLOR_TEXT_LIGHT,
        )
        canvas.create_text(
            ax_x, m - 10,
            text=f"PC2 ({pct2}%)", anchor="center",
            font=(FONT_FAMILY, FONT_SIZE_SMALL), fill=COLOR_TEXT_LIGHT,
        )

        # ---- Draw points ----
        r = _POINT_RADIUS
        for i, (x, y) in enumerate(coords):
            cx, cy = to_canvas(x, y)

            if self._colour_mode.get():
                cat    = self._entropy_rows[i]["category"]
                color  = _CAT_COLORS[cat][0]
                border = _CAT_COLORS[cat][1]
            else:
                color  = _POINT_COLOR
                border = "#ffffff"

            oval = canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=color, outline=border, width=1.5,
            )
            canvas.create_text(
                cx, cy,
                text=codes[i],
                font=(FONT_FAMILY, FONT_SIZE_SMALL - 1, "bold"),
                fill="#ffffff" if color != "#ffffff" else COLOR_TEXT,
            )

            # Bind tooltip
            full_name = policies[i]
            canvas.tag_bind(oval, "<Enter>",
                lambda e, name=full_name, code=codes[i]:
                    self._show_tooltip(e, f"{code}:  {name}"))
            canvas.tag_bind(oval, "<Leave>",
                lambda e: self._hide_tooltip())

    # ------------------------------------------------------------------

    def _show_tooltip(self, event, text: str):
        self._hide_tooltip()
        x = event.widget.winfo_rootx() + event.x + 14
        y = event.widget.winfo_rooty() + event.y + 14
        tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=text, justify="left",
            background="#fffbe6", foreground="#1e1e1e",
            relief="solid", borderwidth=1,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            padx=8, pady=4,
        ).pack()
        self._tooltip_win = tw

    def _hide_tooltip(self):
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None
