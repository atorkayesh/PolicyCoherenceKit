# =============================================================================
# Policy Coherence Kit -- aggregation_dialog.py
# Dialogs that drive the aggregation workflow:
#
#   AggregationMethodDialog  -- choose Average / Majority / Weighted
#                               (only shown when n_matrices >= 3)
#   WeightDialog             -- enter per-DM weights that sum to 1.0
#   TieResolutionDialog      -- resolve majority ties one by one
#
# All dialogs are modal Toplevels.
# Each stores its result in  .result  (None = cancelled).
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from aggregator import TiedCell
from constants import (
    COHERENCE_RATINGS, RATING_SCORES,
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
    COLOR_BUTTON, COLOR_BUTTON_FG,
    CURSOR_HAND,
)
import tkinter.font as tkFont
from dialogs import style_button, _create_rounded_rect, _hex_interp, _rrect_pts
from theme import (
    MODAL_BG, MODAL_BORDER, MODAL_TITLE_COLOR, MODAL_TITLE_SIZE,
    MODAL_SUBTITLE_COLOR, MODAL_SUBTITLE_SIZE, MODAL_DIVIDER_COLOR,
    MODAL_CLOSE_CANVAS_SIZE, MODAL_CLOSE_ICON_COLOR, MODAL_CLOSE_HOVER_BG,
    MODAL_CLOSE_HOVER_RADIUS, MODAL_CLOSE_ICON_SIZE, MODAL_CLOSE_STROKE,
    MODAL_SECTION_TITLE_COLOR, MODAL_ADD_BTN_BG,
    MODAL_FIELD_BG, MODAL_FIELD_BORDER,
)


# =============================================================================
# Canvas button helper  (mirrors NewMatrixDialog._build_footer_button)
# =============================================================================

def _make_canvas_button(
    parent: tk.Misc,
    label: str,
    command,
    *,
    bg: str,
    hover_bg: str,
    fg: str,
    height: int = 33,
    radius: int = 5,
    padx: int = 18,
    text_size: int = 11,
    modal_bg: str = "#eaeef4",
    border: Optional[str] = None,
) -> tk.Canvas:
    font   = tkFont.Font(family=FONT_FAMILY, size=text_size)
    width  = padx + font.measure(label) + padx
    t      = [0.0]
    anim   = [None]

    canvas = tk.Canvas(
        parent,
        width=width + 2, height=height + 2,
        bg=modal_bg, highlightthickness=0, bd=0, cursor=CURSOR_HAND,
    )

    def draw(fill_color):
        canvas.delete("all")
        pts = _rrect_pts(1, 1, width + 1, height + 1, radius)
        outline = border if border is not None else fill_color
        outline_w = 1 if border is not None else 0
        canvas.create_polygon(*pts, fill=fill_color, outline=outline, width=outline_w)
        canvas.create_text(1 + width / 2, 1 + height / 2, text=label, fill=fg, font=font)

    def animate(target):
        if anim[0]:
            canvas.after_cancel(anim[0])
            anim[0] = None

        def tick():
            diff = target - t[0]
            if abs(diff) < 0.02:
                t[0] = target
                draw(_hex_interp(bg, hover_bg, target))
                anim[0] = None
                return
            t[0] += diff * 0.3
            draw(_hex_interp(bg, hover_bg, t[0]))
            anim[0] = canvas.after(16, tick)

        tick()

    def poll():
        try:
            mx, my = canvas.winfo_pointerx(), canvas.winfo_pointery()
            bx, by = canvas.winfo_rootx(), canvas.winfo_rooty()
            over = bx <= mx <= bx + width and by <= my <= by + height
            target = 1.0 if over else 0.0
            if abs(t[0] - target) > 0.01 and anim[0] is None:
                animate(target)
        except tk.TclError:
            return
        canvas.after(30, poll)

    draw(bg)
    canvas.bind("<Button-1>", lambda _e: command())
    canvas.after(100, poll)
    return canvas


# =============================================================================
# AggregationMethodDialog
# =============================================================================

class AggregationMethodDialog(tk.Toplevel):
    """
    Ask the user which aggregation method to use.
    Shown only when there are 3 or more decision-makers.

    .result : None | "average" | "majority" | "weighted"
    """

    _W      = 440
    _CARD_H = 76
    _CARD_R = 6
    _PADX   = 24

    _OPTIONS = [
        (
            "average",
            "Average",
            "Each decision-maker is weighted equally. Cell score = mean of all scores.",
        ),
        (
            "majority",
            "Majority Rule",
            "The most common rating wins. Ties are flagged for manual resolution.",
        ),
        (
            "weighted",
            "Weighted by Importance",
            "You assign a weight (0–1) to each DM. Weights must sum to exactly 1.0.",
        ),
    ]

    def __init__(self, parent: tk.Misc, decision_makers: List[str]):
        super().__init__(parent)
        self.title("Aggregation Method")
        self.configure(bg=MODAL_BG)
        self.resizable(False, False)
        self.grab_set()

        self.result: Optional[str] = None
        self._decision_makers = decision_makers
        self._selected = "average"
        self._card_cvs: dict = {}

        self._build()
        self._center()

    # ------------------------------------------------------------------

    def _build(self):
        W, PX = self._W, self._PADX

        # ── Header row ────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))

        tk.Label(
            hdr,
            text="Aggregation Method",
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")

        close_cv = tk.Canvas(
            hdr,
            width=MODAL_CLOSE_CANVAS_SIZE, height=MODAL_CLOSE_CANVAS_SIZE,
            bg=MODAL_BG, highlightthickness=0, cursor=CURSOR_HAND,
        )
        close_cv.pack(side="right")
        self._draw_close_icon(close_cv)
        close_cv.bind("<Button-1>", lambda _e: self.destroy())
        close_cv.bind("<Enter>",    lambda _e: self._close_hover(close_cv, True))
        close_cv.bind("<Leave>",    lambda _e: self._close_hover(close_cv, False))

        # ── Subtitle ──────────────────────────────────────────────────
        n = len(self._decision_makers)
        dm_word = "decision-maker" if n == 1 else "decision-makers"
        tk.Label(
            self,
            text=f"{n} {dm_word} detected — choose how to combine their ratings.",
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
            wraplength=W - PX * 2,
            justify="left",
        ).pack(anchor="w", padx=PX, pady=(4, 12))

        self._divider()

        # ── Option cards ──────────────────────────────────────────────
        cards_frame = tk.Frame(self, bg=MODAL_BG)
        cards_frame.pack(fill="x", padx=PX, pady=(12, 8))

        for value, _label, _desc in self._OPTIONS:
            cv = tk.Canvas(
                cards_frame,
                width=W - PX * 2, height=self._CARD_H,
                bg=MODAL_BG, highlightthickness=0, cursor=CURSOR_HAND,
            )
            cv.pack(pady=4)
            self._card_cvs[value] = cv
            self._draw_card(value)
            cv.bind("<Button-1>", lambda _e, v=value: self._select(v))
            cv.bind("<Enter>",    lambda _e, v=value: self._card_hover(v, True))
            cv.bind("<Leave>",    lambda _e, v=value: self._card_hover(v, False))

        self._divider()

        # ── Button row ────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=MODAL_BG)
        btn_row.pack(anchor="e", padx=PX, pady=(10, 20))

        cancel_btn = _make_canvas_button(
            btn_row, "Cancel", self.destroy,
            bg="#f5f7fa", hover_bg="#eaeef4",
            fg=MODAL_SECTION_TITLE_COLOR,
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG, border="#e6e6e6",
        )
        cancel_btn.pack(side="left", padx=(0, 8))

        ok_btn = _make_canvas_button(
            btn_row, "Continue", self._on_ok,
            bg=COLOR_BUTTON, hover_bg="#1a3550",
            fg="#ffffff",
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG,
        )
        ok_btn.pack(side="left")

        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self.destroy())

    # ── drawing helpers ───────────────────────────────────────────────

    def _divider(self):
        cv = tk.Canvas(self, height=1, bg=MODAL_BG, highlightthickness=0)
        cv.pack(fill="x", padx=self._PADX)
        cv.create_line(0, 0, self._W - self._PADX * 2, 0, fill=MODAL_DIVIDER_COLOR)

    def _draw_card(self, value: str, hovered: bool = False):
        cv   = self._card_cvs[value]
        cv.delete("all")
        W    = int(cv["width"])
        H    = int(cv["height"])
        R    = self._CARD_R
        sel  = (value == self._selected)

        if sel:
            bg, border, bw = "#e8eef5", COLOR_ACCENT, 2
        elif hovered:
            bg, border, bw = "#f5f7fa", "#b8cad8", 1
        else:
            bg, border, bw = "#ffffff", MODAL_BORDER, 1

        _create_rounded_rect(cv, 1, 1, W - 1, H - 1, R,
                              fill=bg, outline=border, width=bw)

        # Radio dot
        DOT_X, DOT_Y, DOT_R = 22, H // 2, 7
        cv.create_oval(
            DOT_X - DOT_R, DOT_Y - DOT_R, DOT_X + DOT_R, DOT_Y + DOT_R,
            outline=COLOR_ACCENT if sel else "#b0bfcc",
            fill="#ffffff", width=1.5,
        )
        if sel:
            INNER = 3
            cv.create_oval(
                DOT_X - INNER, DOT_Y - INNER, DOT_X + INNER, DOT_Y + INNER,
                fill=COLOR_ACCENT, outline="",
            )

        # Title + description
        label_map = {v: (lbl, desc) for v, lbl, desc in self._OPTIONS}
        title, desc = label_map[value]
        TX = 44
        cv.create_text(
            TX, H // 2 - 11,
            text=title, anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            fill=COLOR_ACCENT if sel else MODAL_TITLE_COLOR,
        )
        cv.create_text(
            TX, H // 2 + 11,
            text=desc, anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            fill=MODAL_SUBTITLE_COLOR,
            width=W - TX - 16,
        )

    def _select(self, value: str):
        old = self._selected
        self._selected = value
        if old != value:
            self._draw_card(old)
        self._draw_card(value)

    def _card_hover(self, value: str, entering: bool):
        if value != self._selected:
            self._draw_card(value, hovered=entering)

    def _draw_close_icon(self, cv: tk.Canvas):
        S  = MODAL_CLOSE_CANVAS_SIZE
        IS = MODAL_CLOSE_ICON_SIZE
        cx = cy = S // 2
        d  = IS // 2
        cv.create_line(cx - d, cy - d, cx + d, cy + d,
                       fill=MODAL_CLOSE_ICON_COLOR, width=MODAL_CLOSE_STROKE, capstyle="round")
        cv.create_line(cx + d, cy - d, cx - d, cy + d,
                       fill=MODAL_CLOSE_ICON_COLOR, width=MODAL_CLOSE_STROKE, capstyle="round")

    def _close_hover(self, cv: tk.Canvas, entering: bool):
        S = MODAL_CLOSE_CANVAS_SIZE
        cv.delete("all")
        if entering:
            _create_rounded_rect(cv, 0, 0, S, S, MODAL_CLOSE_HOVER_RADIUS,
                                  fill=MODAL_CLOSE_HOVER_BG, outline="")
        self._draw_close_icon(cv)

    def _on_ok(self):
        self.result = self._selected
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# =============================================================================
# WeightDialog
# =============================================================================

class WeightDialog(tk.Toplevel):
    """
    Ask the user to enter a weight (0.0 - 1.0) for each decision-maker.
    Weights must sum to exactly 1.0 (tolerance 0.01).

    .result : None | List[float]   (same order as decision_makers)
    """

    _W    = 420
    _PADX = 24

    def __init__(self, parent: tk.Misc, decision_makers: List[str]):
        super().__init__(parent)
        self.title("Decision-Maker Weights")
        self.configure(bg=MODAL_BG)
        self.resizable(False, True)
        self.grab_set()

        self.result: Optional[List[float]] = None
        self._decision_makers = decision_makers
        self._entries: List[tk.Entry] = []
        self._vars:    List[tk.StringVar] = []
        self._sum_label: Optional[tk.Label] = None

        self._build()
        self._center()

    # ------------------------------------------------------------------

    def _build(self):
        W, PX = self._W, self._PADX

        # ── Header row ────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))

        tk.Label(
            hdr,
            text="Decision-Maker Weights",
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")

        close_cv = tk.Canvas(
            hdr,
            width=MODAL_CLOSE_CANVAS_SIZE, height=MODAL_CLOSE_CANVAS_SIZE,
            bg=MODAL_BG, highlightthickness=0, cursor=CURSOR_HAND,
        )
        close_cv.pack(side="right")
        self._draw_close_icon(close_cv)
        close_cv.bind("<Button-1>", lambda _e: self.destroy())
        close_cv.bind("<Enter>",    lambda _e: self._close_hover(close_cv, True))
        close_cv.bind("<Leave>",    lambda _e: self._close_hover(close_cv, False))

        # ── Subtitle ──────────────────────────────────────────────────
        tk.Label(
            self,
            text="Enter a value between 0.0 and 1.0 for each decision-maker. Weights must sum to exactly 1.0.",
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
            wraplength=W - PX * 2,
            justify="left",
        ).pack(anchor="w", padx=PX, pady=(4, 12))

        self._divider()

        # ── DM weight rows ────────────────────────────────────────────
        grid = tk.Frame(self, bg=MODAL_BG)
        grid.pack(fill="x", padx=PX, pady=(12, 4))
        grid.columnconfigure(0, weight=1)

        for i, dm in enumerate(self._decision_makers):
            tk.Label(
                grid,
                text=dm,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
                anchor="w",
            ).grid(row=i, column=0, pady=5, padx=(0, 12), sticky="w")

            var = tk.StringVar(value="")
            entry = tk.Entry(
                grid,
                textvariable=var,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=MODAL_FIELD_BG, fg=COLOR_TEXT,
                insertbackground=COLOR_ACCENT,
                relief="solid", bd=1,
                highlightthickness=1,
                highlightbackground=MODAL_FIELD_BORDER,
                highlightcolor=COLOR_ACCENT,
                width=8,
                justify="center",
            )
            entry.grid(row=i, column=1, pady=5)
            self._vars.append(var)
            self._entries.append(entry)

        # ── Live sum label ────────────────────────────────────────────
        self._sum_var = tk.StringVar(value="Sum: —")
        self._sum_label = tk.Label(
            self,
            textvariable=self._sum_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
        )
        self._sum_label.pack(anchor="e", padx=PX, pady=(2, 8))

        for var in self._vars:
            var.trace_add("write", self._update_sum)

        self._divider()

        # ── Button row ────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=MODAL_BG)
        btn_row.pack(anchor="e", padx=PX, pady=(10, 20))

        cancel_btn = _make_canvas_button(
            btn_row, "Cancel", self.destroy,
            bg="#f5f7fa", hover_bg="#eaeef4",
            fg=MODAL_SECTION_TITLE_COLOR,
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG, border="#e6e6e6",
        )
        cancel_btn.pack(side="left", padx=(0, 8))

        ok_btn = _make_canvas_button(
            btn_row, "Aggregate", self._on_ok,
            bg=COLOR_BUTTON, hover_bg="#1a3550",
            fg="#ffffff",
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG,
        )
        ok_btn.pack(side="left")

        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self.destroy())

        if self._entries:
            self._entries[0].focus_set()

    # ------------------------------------------------------------------

    def _divider(self):
        cv = tk.Canvas(self, height=1, bg=MODAL_BG, highlightthickness=0)
        cv.pack(fill="x", padx=self._PADX)
        cv.create_line(0, 0, self._W - self._PADX * 2, 0, fill=MODAL_DIVIDER_COLOR)

    def _draw_close_icon(self, cv: tk.Canvas):
        S  = MODAL_CLOSE_CANVAS_SIZE
        IS = MODAL_CLOSE_ICON_SIZE
        cx = cy = S // 2
        d  = IS // 2
        cv.create_line(cx - d, cy - d, cx + d, cy + d,
                       fill=MODAL_CLOSE_ICON_COLOR, width=MODAL_CLOSE_STROKE, capstyle="round")
        cv.create_line(cx + d, cy - d, cx - d, cy + d,
                       fill=MODAL_CLOSE_ICON_COLOR, width=MODAL_CLOSE_STROKE, capstyle="round")

    def _close_hover(self, cv: tk.Canvas, entering: bool):
        S = MODAL_CLOSE_CANVAS_SIZE
        cv.delete("all")
        if entering:
            _create_rounded_rect(cv, 0, 0, S, S, MODAL_CLOSE_HOVER_RADIUS,
                                  fill=MODAL_CLOSE_HOVER_BG, outline="")
        self._draw_close_icon(cv)

    def _update_sum(self, *_):
        try:
            total = sum(float(v.get()) for v in self._vars if v.get().strip())
            label = f"Sum: {round(total, 4)}"
            color = COLOR_ACCENT if abs(total - 1.0) <= 0.01 else "#b71c1c"
        except ValueError:
            label = "Sum: —"
            color = MODAL_SUBTITLE_COLOR
        self._sum_var.set(label)
        if self._sum_label:
            self._sum_label.config(fg=color)

    def _on_ok(self):
        weights = []
        for i, var in enumerate(self._vars):
            raw = var.get().strip()
            if not raw:
                messagebox.showwarning(
                    "Missing Weight",
                    f'Please enter a weight for "{self._decision_makers[i]}".',
                    parent=self,
                )
                self._entries[i].focus_set()
                return
            try:
                w = float(raw)
            except ValueError:
                messagebox.showwarning(
                    "Invalid Value",
                    f'"{raw}" is not a valid number for '
                    f'"{self._decision_makers[i]}". Use a decimal like 0.3.',
                    parent=self,
                )
                self._entries[i].focus_set()
                return
            if not (0.0 <= w <= 1.0):
                messagebox.showwarning(
                    "Out of Range",
                    f'Weight for "{self._decision_makers[i]}" must be '
                    f"between 0.0 and 1.0.",
                    parent=self,
                )
                self._entries[i].focus_set()
                return
            weights.append(w)

        total = round(sum(weights), 10)
        if abs(total - 1.0) > 0.01:
            messagebox.showwarning(
                "Weights Do Not Sum to 1",
                f"Current sum is {round(total, 4)}.\n"
                "Please adjust the weights so they sum to exactly 1.0.",
                parent=self,
            )
            return

        self.result = weights
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# =============================================================================
# TieResolutionDialog
# =============================================================================

class TieResolutionDialog(tk.Toplevel):
    """
    Show each tied cell and let the user pick one label.
    All ties must be resolved before the dialog can be confirmed.

    .result : None | List[TiedCell]  (each with .chosen set)
    """

    def __init__(self, parent: tk.Misc, ties: List[TiedCell]):
        super().__init__(parent)
        self.title("Resolve Majority Ties")
        self.configure(bg=COLOR_BG)
        self.resizable(False, True)
        self.grab_set()

        self.result: Optional[List[TiedCell]] = None
        self._ties = ties
        self._vars: List[tk.StringVar] = []

        self._build()
        self._center()

    # ------------------------------------------------------------------

    def _build(self):
        tk.Label(
            self,
            text="Resolve Majority Ties",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).pack(anchor="w", padx=24, pady=(20, 4))

        tk.Label(
            self,
            text=(
                f"{len(self._ties)} cell(s) ended in a tie. "
                "Please select the rating for each one."
            ),
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            wraplength=400,
        ).pack(anchor="w", padx=24, pady=(0, 10))

        ttk.Separator(self).pack(fill="x", padx=24, pady=4)

        # Scrollable area for ties
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill="both", expand=True, padx=24, pady=8)

        canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        for idx, tie in enumerate(self._ties):
            row_frame = tk.Frame(inner, bg=COLOR_PANEL, pady=8)
            row_frame.pack(fill="x", pady=4, padx=4)

            # Cell label
            tk.Label(
                row_frame,
                text=f"  {tie.code_r}  ->  {tie.code_c}",
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg=COLOR_PANEL, fg=COLOR_ACCENT,
            ).pack(anchor="w", padx=12)

            # Tied options label
            tied_str = "  |  ".join(
                f"{lbl} ({RATING_SCORES[lbl]:+d})"
                for lbl in tie.tied_labels
            )
            tk.Label(
                row_frame,
                text=f"Tied:  {tied_str}",
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
                bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
            ).pack(anchor="w", padx=12)

            # Dropdown for selection (only tied labels as options)
            var = tk.StringVar(value="")
            combo = ttk.Combobox(
                row_frame,
                textvariable=var,
                values=tie.tied_labels,
                state="readonly",
                width=20,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            )
            combo.pack(anchor="w", padx=12, pady=(6, 4))
            self._vars.append(var)

        ttk.Separator(self).pack(fill="x", padx=24, pady=(8, 4))

        # Buttons
        btn_row = tk.Frame(self, bg=COLOR_BG)
        btn_row.pack(anchor="e", padx=24, pady=(4, 20))

        cancel = tk.Button(btn_row, text="Cancel", command=self.destroy)
        cancel.config(
            bg=COLOR_PANEL, fg=COLOR_TEXT, relief="flat",
            padx=12, pady=5,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL), cursor=CURSOR_HAND,
        )
        cancel.pack(side="left", padx=(0, 8))

        ok = tk.Button(btn_row, text="Confirm", command=self._on_ok)
        style_button(ok)
        ok.pack(side="left")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

    # ------------------------------------------------------------------

    def _on_ok(self):
        for i, (tie, var) in enumerate(zip(self._ties, self._vars)):
            chosen = var.get()
            if not chosen:
                messagebox.showwarning(
                    "Unresolved Tie",
                    f"Please select a rating for cell "
                    f"{tie.code_r} -> {tie.code_c}.",
                    parent=self,
                )
                return
            tie.chosen = chosen

        self.result = self._ties
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 460)
        h = min(self.winfo_reqheight(), 600)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
