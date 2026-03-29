# =============================================================================
# Policy Coherence Kit -- dialogs.py
# NewMatrixDialog : collect decision-maker name + policy list (or file import)
# _SimpleInputDialog : single-field reusable prompt (used by app.py for rename)
# _read_policies_from_file : parse xlsx / csv into a list of policy name strings
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Tuple

from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_TEXT,
    COLOR_TEXT_LIGHT, COLOR_BUTTON, COLOR_BUTTON_FG,
    CURSOR_HAND,
)


# =============================================================================
# Shared style helper
# =============================================================================

def style_button(btn: tk.Button, danger: bool = False):
    """Apply the standard primary-button look (or red danger variant)."""
    bg = "#b71c1c" if danger else COLOR_BUTTON
    btn.config(
        bg=bg,
        fg=COLOR_BUTTON_FG,
        activebackground="#1a3550" if not danger else "#7f0000",
        activeforeground="#ffffff",
        relief="flat",
        padx=12, pady=5,
        font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        cursor=CURSOR_HAND,
    )


# =============================================================================
# NewMatrixDialog
# =============================================================================

class NewMatrixDialog(tk.Toplevel):
    """
    Modal dialog that collects:
      - Decision-maker name  (free text entry)
      - Policy names         (multiline text box, one per line)
                             OR imported from an xlsx / csv file

    After the dialog closes, check  .result:
      None                  -> user cancelled
      (str, List[str])      -> (decision_maker_name, [policy_name, ...])
    """

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("Add Decision-Maker Matrix")
        self.configure(bg=COLOR_BG)
        self.resizable(True, True)
        self.grab_set()          # modal -- block the parent window

        self.result: Optional[Tuple[str, List[str]]] = None

        self._build()
        self._center()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        # ---- Title --------------------------------------------------
        tk.Label(
            self,
            text="New Policy Coherence Matrix",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).pack(anchor="w", padx=24, pady=(20, 2))

        tk.Label(
            self,
            text="Enter the decision-maker and the policies to include in the matrix.",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(anchor="w", padx=24, pady=(0, 8))

        ttk.Separator(self).pack(fill="x", padx=24, pady=4)

        # ---- Decision-maker name ------------------------------------
        tk.Label(
            self,
            text="Decision-Maker Name",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(10, 2))

        self._dm_var = tk.StringVar()
        self._dm_entry = tk.Entry(
            self,
            textvariable=self._dm_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff", fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            width=44,
        )
        self._dm_entry.pack(anchor="w", padx=24, pady=(0, 14))
        self._dm_entry.focus_set()

        # ---- Policy names -------------------------------------------
        tk.Label(
            self,
            text="Policy Names  (one per line, minimum 2)",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(0, 2))

        # Text area + scrollbar in a sub-frame
        text_frame = tk.Frame(self, bg=COLOR_BG)
        text_frame.pack(fill="both", expand=True, padx=24, pady=(0, 4))

        self._policy_text = tk.Text(
            text_frame,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff", fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            width=50, height=10,
            wrap="word",
        )
        sb = ttk.Scrollbar(text_frame, command=self._policy_text.yview)
        self._policy_text.configure(yscrollcommand=sb.set)
        self._policy_text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Hint
        tk.Label(
            self,
            text="Policies will be coded automatically: P1, P2, P3 ...",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(anchor="w", padx=24, pady=(0, 6))

        # ---- Import button ------------------------------------------
        import_btn = tk.Button(
            self,
            text="  Import from XLSX / CSV",
            command=self._import_file,
        )
        style_button(import_btn)
        import_btn.pack(anchor="w", padx=24, pady=(0, 14))

        ttk.Separator(self).pack(fill="x", padx=24, pady=6)

        # ---- OK / Cancel row ----------------------------------------
        btn_row = tk.Frame(self, bg=COLOR_BG)
        btn_row.pack(anchor="e", padx=24, pady=(4, 20))

        cancel_btn = tk.Button(btn_row, text="Cancel", command=self.destroy)
        cancel_btn.config(
            bg=COLOR_PANEL, fg=COLOR_TEXT,
            activebackground=COLOR_PANEL,
            relief="flat", padx=12, pady=5,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            cursor=CURSOR_HAND,
        )
        cancel_btn.pack(side="left", padx=(0, 8))

        ok_btn = tk.Button(btn_row, text="Create Matrix", command=self._on_ok)
        style_button(ok_btn)
        ok_btn.pack(side="left")

        # Keyboard shortcuts
        self.bind("<Return>", self._on_return)
        self.bind("<Escape>", lambda e: self.destroy())

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _import_file(self):
        """Open a file-picker, parse the first column as policy names."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Import policy names from file",
            filetypes=[
                ("Excel / CSV files", "*.xlsx *.xls *.csv"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            policies = _read_policies_from_file(path)
            if not policies:
                messagebox.showwarning(
                    "No Policies Found",
                    "No policy names were found in the first column of that file.",
                    parent=self,
                )
                return
            self._policy_text.delete("1.0", "end")
            self._policy_text.insert("1.0", "\n".join(policies))
        except Exception as exc:
            messagebox.showerror("Import Error", str(exc), parent=self)

    def _on_ok(self):
        """Validate inputs then store result and close."""
        dm_name = self._dm_var.get().strip()
        if not dm_name:
            messagebox.showwarning(
                "Missing Name",
                "Please enter a decision-maker name.",
                parent=self,
            )
            self._dm_entry.focus_set()
            return

        raw      = self._policy_text.get("1.0", "end").strip()
        policies = [line.strip() for line in raw.splitlines() if line.strip()]

        if len(policies) < 2:
            messagebox.showwarning(
                "Too Few Policies",
                "Please enter at least 2 policy names (one per line).",
                parent=self,
            )
            self._policy_text.focus_set()
            return

        # Check for duplicates
        if len(policies) != len(set(policies)):
            messagebox.showwarning(
                "Duplicate Policies",
                "Each policy name must be unique. Please remove duplicates.",
                parent=self,
            )
            return

        self.result = (dm_name, policies)
        self.destroy()

    def _on_return(self, event):
        """Only finalise if focus is on the name entry, not the policy text box."""
        if self.focus_get() is self._dm_entry:
            self._on_ok()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _center(self):
        """Center the dialog on screen after layout is resolved."""
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


# =============================================================================
# _SimpleInputDialog  (used by app.py for "Rename Tab")
# =============================================================================

class _SimpleInputDialog(tk.Toplevel):
    """
    Minimal single-field modal dialog.

    Usage:
        dlg = _SimpleInputDialog(parent, title="Rename", label="New name:", default="x")
        parent.wait_window(dlg)
        if dlg.result:
            ...
    """

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        label: str,
        default: str = "",
    ):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.grab_set()

        self.result: Optional[str] = None

        tk.Label(
            self,
            text=label,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(anchor="w", padx=20, pady=(16, 4))

        self._var = tk.StringVar(value=default)
        entry = tk.Entry(
            self,
            textvariable=self._var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff", fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            width=34,
        )
        entry.pack(anchor="w", padx=20, pady=(0, 14))
        entry.select_range(0, "end")
        entry.focus_set()

        btn_row = tk.Frame(self, bg=COLOR_BG)
        btn_row.pack(anchor="e", padx=20, pady=(0, 16))

        cancel_btn = tk.Button(btn_row, text="Cancel", command=self.destroy)
        cancel_btn.config(
            bg=COLOR_PANEL, fg=COLOR_TEXT,
            relief="flat", padx=10, pady=4,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            cursor=CURSOR_HAND,
        )
        cancel_btn.pack(side="left", padx=(0, 6))

        ok_btn = tk.Button(btn_row, text="OK", command=self._on_ok)
        style_button(ok_btn)
        ok_btn.pack(side="left")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _on_ok(self):
        value = self._var.get().strip()
        if value:
            self.result = value
            self.destroy()


# =============================================================================
# File import helper
# =============================================================================

def _read_policies_from_file(path: str) -> List[str]:
    """
    Read policy names from the first column of an xlsx, xls, or csv file.

    Rules:
    - Skips blank cells.
    - Skips common header words: "policy", "policy name", "name", "policies".
    - Returns the remaining non-empty strings in order.
    """
    _SKIP = {"", "policy", "policy name", "name", "policies"}

    # ---- CSV -----------------------------------------------------------
    if path.lower().endswith(".csv"):
        import csv
        policies = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.reader(f):
                if not row:
                    continue
                val = row[0].strip()
                if val.lower() in _SKIP:
                    continue
                policies.append(val)
        return policies

    # ---- Excel (xlsx / xls) --------------------------------------------
    try:
        import openpyxl
    except ImportError:
        raise ImportError(
            "The openpyxl package is required for Excel import.\n"
            "Install it with:  pip install openpyxl"
        )

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    policies = []
    for row in ws.iter_rows(min_col=1, max_col=1, values_only=True):
        val = row[0]
        if val is None:
            continue
        val = str(val).strip()
        if val.lower() in _SKIP:
            continue
        policies.append(val)
    wb.close()
    return policies
