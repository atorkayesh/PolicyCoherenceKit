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

from .aggregator import TiedCell
from .constants import (
    COHERENCE_RATINGS, RATING_SCORES,
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
    COLOR_BUTTON, COLOR_BUTTON_FG,
)
from .dialogs import style_button


# =============================================================================
# AggregationMethodDialog
# =============================================================================

class AggregationMethodDialog(tk.Toplevel):
    """
    Ask the user which aggregation method to use.
    Shown only when there are 3 or more decision-makers.

    .result : None | "average" | "majority" | "weighted"
    """

    def __init__(self, parent: tk.Misc, decision_makers: List[str]):
        super().__init__(parent)
        self.title("Aggregation Method")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.grab_set()

        self.result: Optional[str] = None
        self._decision_makers = decision_makers
        self._build()
        self._center()

    # ------------------------------------------------------------------

    def _build(self):
        # Title
        tk.Label(
            self,
            text="Choose Aggregation Method",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).pack(anchor="w", padx=24, pady=(20, 4))

        tk.Label(
            self,
            text=(
                f"{len(self._decision_makers)} decision-makers detected. "
                "How should their views be combined?"
            ),
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            wraplength=380,
        ).pack(anchor="w", padx=24, pady=(0, 10))

        ttk.Separator(self).pack(fill="x", padx=24, pady=4)

        # Radio buttons
        self._method_var = tk.StringVar(value="average")

        options = [
            (
                "average",
                "Average",
                "Each decision-maker is weighted equally.\n"
                "Cell score = mean of all scores.",
            ),
            (
                "majority",
                "Majority Rule",
                "The most common rating wins.\n"
                "Ties are flagged for manual resolution.",
            ),
            (
                "weighted",
                "Weighted by Importance",
                "You assign a weight (0-1) to each decision-maker.\n"
                "Weights must sum to exactly 1.0.",
            ),
        ]

        for value, label, description in options:
            row = tk.Frame(self, bg=COLOR_BG)
            row.pack(fill="x", padx=24, pady=4)

            rb = tk.Radiobutton(
                row,
                variable=self._method_var,
                value=value,
                text=label,
                font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                bg=COLOR_BG, fg=COLOR_TEXT,
                activebackground=COLOR_BG,
                selectcolor=COLOR_BG,
                anchor="w",
            )
            rb.pack(anchor="w")

            tk.Label(
                row,
                text=description,
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
                bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
                justify="left",
                padx=22,
            ).pack(anchor="w")

        ttk.Separator(self).pack(fill="x", padx=24, pady=(10, 4))

        # Buttons
        btn_row = tk.Frame(self, bg=COLOR_BG)
        btn_row.pack(anchor="e", padx=24, pady=(4, 20))

        cancel = tk.Button(btn_row, text="Cancel", command=self.destroy)
        cancel.config(
            bg=COLOR_PANEL, fg=COLOR_TEXT, relief="flat",
            padx=12, pady=5,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL), cursor="hand2",
        )
        cancel.pack(side="left", padx=(0, 8))

        ok = tk.Button(btn_row, text="Continue", command=self._on_ok)
        style_button(ok)
        ok.pack(side="left")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_ok(self):
        self.result = self._method_var.get()
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

    def __init__(self, parent: tk.Misc, decision_makers: List[str]):
        super().__init__(parent)
        self.title("Decision-Maker Weights")
        self.configure(bg=COLOR_BG)
        self.resizable(False, True)
        self.grab_set()

        self.result: Optional[List[float]] = None
        self._decision_makers = decision_makers
        self._entries: List[tk.Entry] = []
        self._vars:    List[tk.StringVar] = []

        self._build()
        self._center()

    # ------------------------------------------------------------------

    def _build(self):
        tk.Label(
            self,
            text="Assign Decision-Maker Weights",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).pack(anchor="w", padx=24, pady=(20, 4))

        tk.Label(
            self,
            text="Enter a value between 0.0 and 1.0 for each decision-maker.\nAll weights must sum to exactly 1.0.",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(0, 10))

        ttk.Separator(self).pack(fill="x", padx=24, pady=4)

        # One row per decision-maker
        grid = tk.Frame(self, bg=COLOR_BG)
        grid.pack(fill="x", padx=24, pady=8)

        for i, dm in enumerate(self._decision_makers):
            tk.Label(
                grid,
                text=dm,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                bg=COLOR_BG, fg=COLOR_TEXT,
                width=28, anchor="w",
            ).grid(row=i, column=0, pady=4, padx=(0, 12), sticky="w")

            var = tk.StringVar(value="")
            entry = tk.Entry(
                grid,
                textvariable=var,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg="#ffffff", fg=COLOR_TEXT,
                insertbackground=COLOR_ACCENT,
                relief="solid", bd=1,
                width=8,
                justify="center",
            )
            entry.grid(row=i, column=1, pady=4)
            self._vars.append(var)
            self._entries.append(entry)

        # Live sum display
        self._sum_var = tk.StringVar(value="Sum: —")
        tk.Label(
            self,
            textvariable=self._sum_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT2,
        ).pack(anchor="e", padx=24, pady=(0, 4))

        # Update sum on every keystroke
        for var in self._vars:
            var.trace_add("write", self._update_sum)

        ttk.Separator(self).pack(fill="x", padx=24, pady=4)

        # Buttons
        btn_row = tk.Frame(self, bg=COLOR_BG)
        btn_row.pack(anchor="e", padx=24, pady=(4, 20))

        cancel = tk.Button(btn_row, text="Cancel", command=self.destroy)
        cancel.config(
            bg=COLOR_PANEL, fg=COLOR_TEXT, relief="flat",
            padx=12, pady=5,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL), cursor="hand2",
        )
        cancel.pack(side="left", padx=(0, 8))

        ok = tk.Button(btn_row, text="Aggregate", command=self._on_ok)
        style_button(ok)
        ok.pack(side="left")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

        # Focus first entry
        if self._entries:
            self._entries[0].focus_set()

    # ------------------------------------------------------------------

    def _update_sum(self, *_):
        """Recompute and display the running sum of entered weights."""
        try:
            total = sum(float(v.get()) for v in self._vars if v.get().strip())
            label = f"Sum: {round(total, 4)}"
            color = COLOR_ACCENT if abs(total - 1.0) <= 0.01 else "#b71c1c"
        except ValueError:
            label = "Sum: —"
            color = COLOR_TEXT_LIGHT
        self._sum_var.set(label)
        # Update label colour dynamically
        for widget in self.pack_slaves():
            if isinstance(widget, tk.Label) and widget.cget("textvariable") == str(self._sum_var):
                widget.config(fg=color)
                break

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
            font=(FONT_FAMILY, FONT_SIZE_NORMAL), cursor="hand2",
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
