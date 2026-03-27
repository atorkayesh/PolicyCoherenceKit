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
from tkinter import ttk
from typing import List, Tuple, Optional

from aggregator import AggregationResult
from range_of_influence_tab import compute_entropy, _CAT_COLORS
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
    CURSOR_HAND,
)

# Default point colour (single-colour mode)
_POINT_COLOR   = "#2c4a6e"
_POINT_RADIUS  = 16
_CANVAS_W      = 680
_CANVAS_H      = 520
_MARGIN        = 60


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
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)

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
        self._build_legend_bar()

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
            text=f"PCA — Policy Influence Space  ({method_label})",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
        ).pack(side="left", padx=16)

        if self._valid:
            pct1, pct2 = self._explained
            tk.Label(
                bar,
                text=(f"PC1: {pct1}%   PC2: {pct2}%   "
                      f"Total explained: {round(pct1+pct2,1)}%"),
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
                bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
            ).pack(side="left", padx=6)

    # ------------------------------------------------------------------

    def _build_controls(self):
        ctrl = tk.Frame(self, bg=COLOR_BG)
        ctrl.pack(fill="x", padx=16, pady=6)

        tk.Label(
            ctrl,
            text="Colour by entropy category:",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, fg=COLOR_TEXT,
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

        # Save button
        save_row = tk.Frame(self, bg=COLOR_BG)
        save_row.pack(anchor="e", padx=16, pady=(2, 6))
        tk.Button(
            save_row, text="Save as PNG",
            command=self._save_canvas,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
            relief="flat", padx=8, pady=3, cursor=CURSOR_HAND,
        ).pack(side="right")

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
        self._update_legend()

    # ------------------------------------------------------------------

    def _update_legend(self):
        for w in self._legend_frame.winfo_children():
            w.destroy()

        if self._colour_mode.get():
            tk.Label(
                self._legend_frame,
                text="Entropy categories:",
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg=COLOR_BG, fg=COLOR_TEXT,
            ).pack(side="left", padx=(0, 10))
            for cat, (bg, fg) in _CAT_COLORS.items():
                tk.Label(
                    self._legend_frame,
                    text=f"  {cat}  ",
                    font=(FONT_FAMILY, FONT_SIZE_SMALL),
                    bg=bg, fg=fg,
                    padx=6, pady=2, relief="flat",
                ).pack(side="left", padx=2)
        else:
            tk.Label(
                self._legend_frame,
                text="Hover over a point to see the full policy name.",
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
                bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            ).pack(side="left")

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
