# =============================================================================
# Policy Coherence Kit -- dialogs.py
# NewMatrixDialog : collect decision-maker name + policy list (or file import)
# _SimpleInputDialog : single-field reusable prompt (used by app.py for rename)
# _read_policies_from_file : parse xlsx / csv into a list of policy name strings
# =============================================================================

import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Tuple

from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_TEXT,
    COLOR_TEXT_LIGHT, COLOR_BUTTON, COLOR_BUTTON_FG, COLOR_BORDER,
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
# ProjectSetupDialog
# =============================================================================

class ProjectSetupDialog(tk.Toplevel):
    """
    Shared modal dialog for:
      - creating a new project with project name, decision-makers, and policies
      - adding decision-makers to an existing project while showing inherited policies
    """

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        include_project_name: bool = True,
        existing_project_names: Optional[List[str]] = None,
        existing_dm_names: Optional[List[str]] = None,
        fixed_policies: Optional[List[str]] = None,
    ):
        super().__init__(parent)
        self._parent = parent

        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(parent)
        self.overrideredirect(True)
        self.grab_set()

        self._dialog_title = title
        self._include_project_name = include_project_name
        self._existing_project_names = set(existing_project_names or [])
        self._existing_dm_names = set(existing_dm_names or [])
        self._fixed_policies = list(fixed_policies or [])

        self._project_var = tk.StringVar()
        self._dm_vars: List[tk.StringVar] = []
        self._policy_vars: List[tk.StringVar] = []
        self._first_dm_entry: Optional[tk.Entry] = None
        self._section_entries = {}
        self.result: Optional[dict] = None

        self._build()
        self._resize_to_content()

    def _build(self):
        shell = tk.Frame(
            self,
            bg="#ffffff",
            highlightbackground="#d9d5ce",
            highlightthickness=1,
        )
        shell.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Frame(shell, bg="#ffffff", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=self._dialog_title,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg="#ffffff", fg=COLOR_TEXT,
        ).pack(side="top", pady=(12, 0))

        close_btn = tk.Canvas(header, width=24, height=24, bg="#ffffff",
                              highlightthickness=0, cursor=CURSOR_HAND)
        close_btn.place(relx=1.0, x=-18, y=12, anchor="ne")
        self._draw_close_icon(close_btn)
        close_btn.bind("<Button-1>", lambda e: self._close())

        self._drag_origin = None
        for widget in (header,):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

        tk.Frame(shell, bg=COLOR_BORDER, height=1).pack(fill="x")

        canvas_wrap = tk.Frame(shell, bg=COLOR_BG)
        canvas_wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(canvas_wrap, bg=COLOR_BG, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(canvas_wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)

        self._content = tk.Frame(self._canvas, bg=COLOR_BG)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")
        self._content.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

        root = self._content
        title_text = "Create Project" if self._include_project_name else "Add Decision-Makers"
        subtitle = (
            "Define the project, decision-makers, and policy set."
            if self._include_project_name
            else "Add one or more decision-makers to the current project."
        )

        tk.Label(
            root,
            text=title_text,
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).pack(anchor="w", padx=24, pady=(20, 2))

        tk.Label(
            root,
            text=subtitle,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(anchor="w", padx=24, pady=(0, 8))

        import_top = tk.Button(
            root,
            text="Import Excel",
            command=self._on_import_excel,
        )
        style_button(import_top)
        import_top.pack(anchor="w", padx=24, pady=(0, 10))

        ttk.Separator(root).pack(fill="x", padx=24, pady=4)

        if self._include_project_name:
            self._build_project_name_section()

        self._dm_entries_host = self._build_dynamic_section(
            title="Decision-Maker Names",
            hint="Add one or more decision-makers. Default: 2 inputs.",
            add_cmd=lambda: self._add_line(self._dm_entries_host, self._dm_vars),
        )
        for _ in range(2):
            self._add_line(self._dm_entries_host, self._dm_vars)

        ttk.Separator(root).pack(fill="x", padx=24, pady=8)

        if self._fixed_policies:
            self._build_fixed_policy_section()
        else:
            self._policy_entries_host = self._build_dynamic_section(
                title="Policy Names",
                hint="Add at least 2 policies. Default: 2 inputs.",
                add_cmd=lambda: self._add_line(self._policy_entries_host, self._policy_vars),
            )
            for _ in range(2):
                self._add_line(self._policy_entries_host, self._policy_vars)

        ttk.Separator(root).pack(fill="x", padx=24, pady=8)

        btn_row = tk.Frame(root, bg=COLOR_BG)
        btn_row.pack(anchor="e", padx=24, pady=(4, 20))

        cancel_btn = tk.Button(btn_row, text="Cancel", command=self._close)
        cancel_btn.config(
            bg=COLOR_PANEL, fg=COLOR_TEXT,
            activebackground=COLOR_PANEL,
            relief="flat", padx=12, pady=5,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            cursor=CURSOR_HAND,
        )
        cancel_btn.pack(side="left", padx=(0, 8))

        action = "Create Project" if self._include_project_name else "Add Decision-Makers"
        ok_btn = tk.Button(btn_row, text=action, command=self._on_ok)
        style_button(ok_btn)
        ok_btn.pack(side="left")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._close())

        if self._include_project_name:
            self._project_entry.focus_set()
        elif self._first_dm_entry is not None:
            self._first_dm_entry.focus_set()

    def _build_project_name_section(self):
        tk.Label(
            self._content,
            text="Project Name",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(10, 2))

        self._project_entry = tk.Entry(
            self._content,
            textvariable=self._project_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff", fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            width=42,
        )
        self._project_entry.pack(anchor="w", padx=24, pady=(0, 14))

    def _build_dynamic_section(self, title: str, hint: str, add_cmd):
        wrap = tk.Frame(self._content, bg=COLOR_BG)
        wrap.pack(fill="x", padx=24, pady=(8, 0))

        head = tk.Frame(wrap, bg=COLOR_BG)
        head.pack(fill="x")
        tk.Label(
            head,
            text=title,
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(side="left")

        add_btn = tk.Button(
            head,
            text="+",
            command=add_cmd,
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
            activebackground=COLOR_PANEL,
            relief="flat", padx=10, pady=1,
            cursor=CURSOR_HAND,
        )
        add_btn.pack(side="right")

        tk.Label(
            wrap,
            text=hint,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(anchor="w", pady=(2, 8))

        host = tk.Frame(wrap, bg=COLOR_BG)
        host.pack(fill="x")
        self._section_entries[host] = []
        return host

    def _build_fixed_policy_section(self):
        wrap = tk.Frame(self._content, bg=COLOR_BG)
        wrap.pack(fill="x", padx=24, pady=(8, 0))

        tk.Label(
            wrap,
            text="Policy Names",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(anchor="w")
        tk.Label(
            wrap,
            text="Policies are inherited from the current project.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(anchor="w", pady=(2, 8))

        host = tk.Frame(wrap, bg=COLOR_BG)
        host.pack(fill="x")
        self._section_entries[host] = []
        for policy in self._fixed_policies:
            var = tk.StringVar(value=policy)
            self._policy_vars.append(var)
            self._add_line(host, self._policy_vars, default=policy, state="disabled", append_var=False)

    def _add_line(
        self,
        parent: tk.Frame,
        vars_list: List[tk.StringVar],
        default: str = "",
        state: str = "normal",
        append_var: bool = True,
    ):
        var = tk.StringVar(value=default)
        if append_var:
            vars_list.append(var)
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff" if state == "normal" else "#f4f6f8",
            fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            width=32,
            state=state,
        )
        self._section_entries[parent].append(entry)
        self._relayout_section(parent)
        if state == "normal" and self._first_dm_entry is None:
            self._first_dm_entry = entry
        self.after_idle(self._resize_to_content)
        return entry

    def _relayout_section(self, parent: tk.Frame):
        entries = self._section_entries.get(parent, [])
        count = len(entries)
        if not entries:
            return

        cols = 1
        if count > 6:
            cols = 2
        if count > 12:
            cols = 3
        per_col = math.ceil(count / cols)

        for col in range(3):
            parent.grid_columnconfigure(col, weight=0)
        for col in range(cols):
            parent.grid_columnconfigure(col, weight=1, uniform=str(parent))

        for idx, entry in enumerate(entries):
            row = idx % per_col
            col = idx // per_col
            entry.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

    def _on_ok(self):
        project_name = self._project_var.get().strip() if self._include_project_name else None
        dm_names = [var.get().strip() for var in self._dm_vars if var.get().strip()]
        policies = self._fixed_policies or [var.get().strip() for var in self._policy_vars if var.get().strip()]

        if self._include_project_name:
            if not project_name:
                messagebox.showwarning("Project Name Required", "Please enter a project name.", parent=self)
                return
            if project_name in self._existing_project_names:
                messagebox.showwarning("Duplicate Project", f'A project named "{project_name}" already exists.', parent=self)
                return

        if not dm_names:
            messagebox.showwarning("Decision-Makers Required", "Please enter at least one decision-maker name.", parent=self)
            return
        if len(dm_names) != len(set(dm_names)):
            messagebox.showwarning("Duplicate Decision-Makers", "Decision-maker names must be unique.", parent=self)
            return
        duplicates = sorted(set(dm_names) & self._existing_dm_names)
        if duplicates:
            messagebox.showwarning(
                "Existing Decision-Makers",
                "These decision-maker names already exist in the project:\n\n" + "\n".join(duplicates),
                parent=self,
            )
            return

        if len(policies) < 2:
            messagebox.showwarning("Too Few Policies", "Please enter at least 2 policy names.", parent=self)
            return
        if len(policies) != len(set(policies)):
            messagebox.showwarning("Duplicate Policies", "Policy names must be unique.", parent=self)
            return

        self.result = {
            "action": "manual",
            "project_name": project_name,
            "decision_makers": dm_names,
            "policies": policies,
        }
        self._close()

    def _on_import_excel(self):
        self.result = {"action": "import_excel"}
        self._close()

    def _close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def _resize_to_content(self):
        self.update_idletasks()
        req_w = self.winfo_reqwidth()
        req_h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        width = min(max(860, req_w + 40), sw - 80)
        height = min(max(620, req_h + 20), 720, sh - 80)
        x = (sw - width) // 2
        y = max(40, (sh - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.lift()
        self.after_idle(self._update_scrollbar_visibility)

    def _draw_close_icon(self, canvas: tk.Canvas):
        canvas.delete("all")
        s = 1.0
        ox = oy = 0
        stroke = "#a3a3a3"
        lw = 1.5
        canvas.create_rectangle(0, 0, 24, 24, fill="#eaeef4", outline="")
        canvas.create_line(18*s+ox, 6*s+oy, 6*s+ox, 18*s+oy, fill=stroke, width=lw, capstyle="round")
        canvas.create_line(6*s+ox, 6*s+oy, 18*s+ox, 18*s+oy, fill=stroke, width=lw, capstyle="round")

    def _start_drag(self, event):
        self._drag_origin = (event.x_root, event.y_root, self.winfo_x(), self.winfo_y())

    def _on_drag(self, event):
        if not self._drag_origin:
            return
        start_x, start_y, win_x, win_y = self._drag_origin
        dx = event.x_root - start_x
        dy = event.y_root - start_y
        self.geometry(f"+{win_x + dx}+{win_y + dy}")

    def _on_canvas_configure(self, event):
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            if self.winfo_exists():
                self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    def _update_scrollbar_visibility(self):
        self.update_idletasks()
        needs_scroll = self._content.winfo_reqheight() > (self._canvas.winfo_height() + 80)
        if needs_scroll:
            if not self._scrollbar.winfo_ismapped():
                self._scrollbar.pack(side="right", fill="y")
        else:
            if self._scrollbar.winfo_ismapped():
                self._scrollbar.pack_forget()

    def destroy(self):
        super().destroy()


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
