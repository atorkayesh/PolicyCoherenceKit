# =============================================================================
# Policy Coherence Kit -- aggregation_dialog.py
# Dialogs that drive the aggregation workflow:
#
#   AggregationMethodDialog  -- choose Average / Median / Majority / Weighted
#                               (only shown when n_matrices >= 3)
#   MedianChoiceDialog       -- choose Lower / Upper median for even counts
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
    RATING_SCORES,
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER,
    COLOR_ACCENT,
    COLOR_TEXT,
    COLOR_BUTTON,
    CURSOR_HAND,
)
from dialogs import (
    _create_rounded_rect,
    _make_canvas_button,
    _make_modal_close_btn,
    _modal_divider,
)
from theme import (
    MODAL_BG, MODAL_BORDER, MODAL_TITLE_COLOR, MODAL_TITLE_SIZE,
    MODAL_SUBTITLE_COLOR, MODAL_SUBTITLE_SIZE,
    MODAL_SECTION_TITLE_COLOR,
    MODAL_FIELD_BG, MODAL_FIELD_BORDER,
)


# =============================================================================
# AggregationMethodDialog
# =============================================================================

class AggregationMethodDialog(tk.Toplevel):
    """
    Ask the user which aggregation method to use.
    Shown only when there are 3 or more decision-makers.

    .result : None | "average" | "median" | "majority" | "weighted"
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
            "median",
            "Median (Ordinal)",
            "Uses the ordered middle rating(s) and avoids assuming equal spacing.",
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

        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))

        tk.Label(
            hdr,
            text="Aggregation Method",
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")

        _make_modal_close_btn(hdr, self.destroy).pack(side="right")

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

        _modal_divider(self, PX)

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

        _modal_divider(self, PX)

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

    def _on_ok(self):
        self.result = self._selected
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# =============================================================================
# MedianChoiceDialog
# =============================================================================

class MedianChoiceDialog(tk.Toplevel):
    """
    Ask the user to choose how the median should be handled for an even
    number of decision-makers.

    .result : None | "lower" | "upper"
    """

    _W      = 440
    _CARD_H = 76
    _CARD_R = 6
    _PADX   = 24

    _OPTIONS = [
        (
            "lower",
            "Lower Median",
            "Use the lower of the two middle ratings in the ordered scale.",
        ),
        (
            "upper",
            "Upper Median",
            "Use the upper of the two middle ratings in the ordered scale.",
        ),
    ]

    def __init__(self, parent: tk.Misc, decision_makers: List[str]):
        super().__init__(parent)
        self.title("Median Choice")
        self.configure(bg=MODAL_BG)
        self.resizable(False, False)
        self.grab_set()

        self.result: Optional[str] = None
        self._decision_makers = decision_makers
        self._selected = "lower"
        self._card_cvs: dict = {}

        self._build()
        self._center()

    def _build(self):
        W, PX = self._W, self._PADX

        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))

        tk.Label(
            hdr,
            text="Median Choice",
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")

        _make_modal_close_btn(hdr, self.destroy).pack(side="right")

        n = len(self._decision_makers)
        dm_word = "decision-maker" if n == 1 else "decision-makers"
        tk.Label(
            self,
            text=(
                f"{n} {dm_word} detected. "
                "Choose which median should be used for aggregation."
            ),
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
            wraplength=W - PX * 2,
            justify="left",
        ).pack(anchor="w", padx=PX, pady=(4, 12))

        _modal_divider(self, PX)

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

        _modal_divider(self, PX)

        btn_row = tk.Frame(self, bg=MODAL_BG)
        btn_row.pack(anchor="e", padx=PX, pady=(10, 20))

        _make_canvas_button(
            btn_row, "Cancel", self.destroy,
            bg="#f5f7fa", hover_bg="#eaeef4",
            fg=MODAL_SECTION_TITLE_COLOR,
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG, border="#e6e6e6",
        ).pack(side="left", padx=(0, 8))
        _make_canvas_button(
            btn_row, "Continue", self._on_ok,
            bg=COLOR_BUTTON, hover_bg="#1a3550",
            fg="#ffffff",
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG,
        ).pack(side="left")

        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _draw_card(self, value: str, hovered: bool = False):
        cv = self._card_cvs[value]
        cv.delete("all")
        W = int(cv["width"])
        H = int(cv["height"])
        R = self._CARD_R
        sel = (value == self._selected)

        if sel:
            bg, border, bw = "#e8eef5", COLOR_ACCENT, 2
        elif hovered:
            bg, border, bw = "#f5f7fa", "#b8cad8", 1
        else:
            bg, border, bw = "#ffffff", MODAL_BORDER, 1

        _create_rounded_rect(cv, 1, 1, W - 1, H - 1, R,
                              fill=bg, outline=border, width=bw)

        DOT_X, DOT_Y, DOT_R = 22, H // 2, 7
        cv.create_oval(
            DOT_X - DOT_R, DOT_Y - DOT_R, DOT_X + DOT_R, DOT_Y + DOT_R,
            outline=COLOR_ACCENT if sel else "#b0bfcc",
            fill="#ffffff", width=1.5,
        )
        if sel:
            cv.create_oval(
                DOT_X - 3, DOT_Y - 3, DOT_X + 3, DOT_Y + 3,
                fill=COLOR_ACCENT, outline="",
            )

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

        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))

        tk.Label(
            hdr,
            text="Decision-Maker Weights",
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")

        _make_modal_close_btn(hdr, self.destroy).pack(side="right")

        tk.Label(
            self,
            text="Enter a value between 0.0 and 1.0 for each decision-maker. Weights must sum to exactly 1.0.",
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
            wraplength=W - PX * 2,
            justify="left",
        ).pack(anchor="w", padx=PX, pady=(4, 12))

        _modal_divider(self, PX)

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

        _modal_divider(self, PX)

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

    _W    = 500
    _HMAX = 620
    _PADX = 24

    def __init__(self, parent: tk.Misc, ties: List[TiedCell]):
        super().__init__(parent)
        self.title("Resolve Majority Ties")
        self.configure(bg=MODAL_BG)
        self.resizable(False, True)
        self.grab_set()

        self.result: Optional[List[TiedCell]] = None
        self._ties = ties
        self._vars: List[tk.StringVar] = []

        self._build()
        self._center()

    # ------------------------------------------------------------------

    def _build(self):
        W, PX = self._W, self._PADX

        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))

        tk.Label(
            hdr,
            text="Resolve Majority Ties",
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")
        _make_modal_close_btn(hdr, self.destroy).pack(side="right")

        tk.Label(
            self,
            text=(
                f"{len(self._ties)} cell(s) ended in a tie. "
                "Please select the rating for each one."
            ),
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
            wraplength=W - PX * 2,
            justify="left",
        ).pack(anchor="w", padx=PX, pady=(6, 10))

        _modal_divider(self, PX)

        # Scrollable area for ties
        outer = tk.Frame(self, bg=MODAL_BG)
        outer.pack(fill="both", expand=True, padx=PX, pady=(12, 8))

        canvas = tk.Canvas(outer, bg=MODAL_BG, highlightthickness=0, width=W - PX * 2)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=MODAL_BG)
        inner_window = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(inner_window, width=e.width)
        )

        for idx, tie in enumerate(self._ties):
            row_frame = tk.Frame(
                inner,
                bg="#ffffff",
                highlightthickness=1,
                highlightbackground=MODAL_BORDER,
                highlightcolor=MODAL_BORDER,
                bd=0,
            )
            row_frame.pack(fill="x", pady=(0 if idx == 0 else 8, 0))

            tk.Label(
                row_frame,
                text=f"{tie.code_r} -> {tie.code_c}",
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg="#ffffff", fg=MODAL_TITLE_COLOR,
            ).pack(anchor="w", padx=14, pady=(12, 0))

            tied_str = "  |  ".join(
                f"{lbl} ({RATING_SCORES[lbl]:+d})"
                for lbl in tie.tied_labels
            )
            tk.Label(
                row_frame,
                text=f"Tied options: {tied_str}",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg="#ffffff", fg=MODAL_SUBTITLE_COLOR,
                justify="left", wraplength=W - PX * 2 - 40,
            ).pack(anchor="w", padx=14, pady=(4, 8))

            field_row = tk.Frame(row_frame, bg="#ffffff")
            field_row.pack(fill="x", padx=14, pady=(0, 12))
            tk.Label(
                field_row,
                text="Selected rating",
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg="#ffffff", fg=MODAL_SECTION_TITLE_COLOR,
            ).pack(anchor="w")

            var = tk.StringVar(value="")
            combo = ttk.Combobox(
                field_row,
                textvariable=var,
                values=tie.tied_labels,
                state="readonly",
                width=28,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            )
            combo.pack(anchor="w", pady=(6, 0))
            self._vars.append(var)

        _modal_divider(self, PX)

        btn_row = tk.Frame(self, bg=MODAL_BG)
        btn_row.pack(anchor="e", padx=PX, pady=(10, 20))

        _make_canvas_button(
            btn_row, "Cancel", self.destroy,
            bg="#f5f7fa", hover_bg="#eaeef4", fg=MODAL_SECTION_TITLE_COLOR,
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG, border="#e6e6e6",
        ).pack(side="left", padx=(0, 8))
        _make_canvas_button(
            btn_row, "Confirm", self._on_ok,
            bg=COLOR_BUTTON, hover_bg="#1a3550", fg="#ffffff",
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG,
        ).pack(side="left")

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
        w = max(self.winfo_reqwidth(), self._W)
        h = min(self.winfo_reqheight(), self._HMAX)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
