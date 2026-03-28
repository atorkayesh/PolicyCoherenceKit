# =============================================================================
# Policy Coherence Kit -- app.py
# Multi-project workspace. Each project lives in its own top-level notebook tab
# and has completely independent state: matrices, analysis results, etc.
# =============================================================================

import io
import math
import sys
import ctypes, ctypes.util
import tkinter as tk

def _preload_cairo():
    name = ctypes.util.find_library("cairo")
    if name:
        try: ctypes.CDLL(name); return
        except OSError: pass
    fallbacks = (
        ["/opt/homebrew/lib/libcairo.2.dylib", "/usr/local/lib/libcairo.2.dylib"]
        if sys.platform == "darwin" else
        ["libcairo-2.dll"] if sys.platform == "win32" else
        ["libcairo.so.2"]
    )
    for p in fallbacks:
        try: ctypes.CDLL(p); return
        except OSError: pass

_preload_cairo()
import cairosvg
from PIL import Image, ImageDraw, ImageTk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont
from typing import List, Optional
from dataclasses import dataclass, field

from models import PolicyMatrix, make_empty_matrix
from matrix_widget import MatrixWidget
from dialogs import NewMatrixDialog, _SimpleInputDialog, style_button
from aggregator import (
    check_completeness,
    aggregate_average, aggregate_majority, aggregate_weighted, resolve_ties,
    AggregationResult,
)
from aggregation_dialog import (
    AggregationMethodDialog, WeightDialog, TieResolutionDialog,
)
from aggregation_tab import AggregationTab
from coherence_scores_tab import CoherenceScoresTab
from range_of_influence_tab import RangeOfInfluenceTab
from pca_tab import PCATab
from network_tab import NetworkTab
from llm_tab import LLMInterpretationTab
from importer import import_matrices_from_excel
from constants import (
    APP_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
    COLOR_TAB_BG, COLOR_BUTTON, COLOR_BUTTON_FG,
    CURSOR_HAND,
)


def _hex_interp(c1, c2, t):
    """Interpolate between two hex colours. t=0 → c1, t=1 → c2."""
    t = max(0.0, min(1.0, t))
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# =============================================================================
# Project data container
# =============================================================================

@dataclass
class Project:
    """All state belonging to one project."""
    name:        str
    matrices:    List[PolicyMatrix] = field(default_factory=list)
    agg_results: List[AggregationResult] = field(default_factory=list)
    agg_tab_ids: List[str] = field(default_factory=list)   # inner notebook tab ids
    notebook:    Optional[ttk.Notebook] = field(default=None, repr=False)
    frame:       Optional[tk.Frame]     = field(default=None, repr=False)


# =============================================================================
# Project name dialog (shown on launch + new project)
# =============================================================================

class _ProjectNameDialog(tk.Toplevel):
    """Simple modal to collect a project name."""

    def __init__(self, parent, title="New Project", existing_names=None):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.grab_set()
        self._existing = existing_names or []
        self.result: Optional[str] = None
        self._build()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tk.Label(
            self, text="Project Name",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT,
        ).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(
            self,
            text="Give this project a unique name.",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        ).pack(anchor="w", padx=24, pady=(0, 10))
        ttk.Separator(self).pack(fill="x", padx=24, pady=4)
        self._var = tk.StringVar()
        self._entry = tk.Entry(
            self, textvariable=self._var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#f5f7fa", fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1, width=36,
        )
        self._entry.pack(padx=24, pady=(8, 16))
        self._entry.focus_set()
        ttk.Separator(self).pack(fill="x", padx=24, pady=4)
        btn_row = tk.Frame(self, bg=COLOR_BG)
        btn_row.pack(anchor="e", padx=24, pady=(6, 18))
        ok = tk.Button(btn_row, text="Create Project", command=self._on_ok)
        style_button(ok)
        ok.pack()
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_ok(self):
        name = self._var.get().strip()
        if not name:
            messagebox.showwarning("Name Required",
                                   "Please enter a project name.", parent=self)
            return
        if name in self._existing:
            messagebox.showwarning("Duplicate Name",
                                   f'A project named "{name}" already exists.',
                                   parent=self)
            return
        self.result = name
        self.destroy()


# =============================================================================
# Main application
# =============================================================================

class PolicyCoherenceApp:
    """
    Multi-project workspace controller.

    Top-level notebook  : one tab per project
    Inner notebook      : DM matrices + analysis tabs for that project
    """

    def __init__(self, root: tk.Tk):
        self.root     = root
        self.projects: List[Project] = []

        self._configure_root()
        self._apply_styles()
        self._build_ui()


    # ==================================================================
    # Setup
    # ==================================================================

    def _configure_root(self):
        self.root.title(APP_TITLE)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.configure(bg=COLOR_BG)
        self.root.update_idletasks()
        w, h = 1200, 780
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=COLOR_BG,
                        borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("TNotebook.Tab", background=COLOR_TAB_BG,
                        foreground=COLOR_TEXT, padding=[14, 6],
                        font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_ACCENT)],
                  foreground=[("selected", "#ffffff")],
                  expand=[("selected", [1, 1, 1, 0])])
        style.configure("TScrollbar", background=COLOR_PANEL,
                        troughcolor=COLOR_BG, borderwidth=0, arrowsize=12)
        style.configure("TCombobox", fieldbackground="#ffffff",
                        background="#ffffff",
                        selectbackground=COLOR_ACCENT,
                        selectforeground="#ffffff")
        style.configure("TSeparator", background=COLOR_BORDER)

        # Inner notebook style (slightly different tab colour)
        style.configure("Inner.TNotebook", background=COLOR_BG,
                        borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("Inner.TNotebook.Tab",
                        background="#c8c4bc",
                        foreground=COLOR_TEXT,
                        padding=[10, 4],
                        font=(FONT_FAMILY, FONT_SIZE_SMALL))
        style.map("Inner.TNotebook.Tab",
                  background=[("selected", COLOR_ACCENT2)],
                  foreground=[("selected", "#ffffff")],
                  expand=[("selected", [1, 1, 1, 0])])

    # ==================================================================
    # Build UI
    # ==================================================================

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=COLOR_BG)
        outer.pack(fill="both", expand=True)

        self._build_sidebar(outer)

        self._content = tk.Frame(outer, bg=COLOR_BG)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_toolbar()
        tk.Frame(self._content, bg=COLOR_ACCENT2, height=2).pack(fill="x")
        self._build_project_notebook()
        self._build_statusbar()

    def _build_sidebar(self, parent):
        self._sidebar_open_states = {}
        self._sidebar_expanded    = True
        _EXP_W = 320
        _COL_W = 80

        sidebar = tk.Frame(parent, bg="#f5f7fa", width=_EXP_W)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._sidebar       = sidebar
        self._sidebar_exp_w = _EXP_W
        self._sidebar_col_w = _COL_W

        # ── Expanded header ────────────────────────────────────────────
        hdr_exp = tk.Frame(sidebar, bg="#f5f7fa", height=90, cursor=CURSOR_HAND)
        hdr_exp.pack(fill="x")
        hdr_exp.pack_propagate(False)
        self._sidebar_hdr_exp = hdr_exp

        text_col = tk.Frame(hdr_exp, bg="#f5f7fa", cursor=CURSOR_HAND)
        text_col.place(relx=0, rely=0.5, anchor="w", x=20)

        _title_lbl = tk.Label(
            text_col, text="Policy Coherence Kit",
            font=(FONT_FAMILY, 20, "bold"),
            bg="#f5f7fa", fg="#1f2937", justify="left", cursor=CURSOR_HAND,
        )
        _title_lbl.pack(anchor="w")

        _slogan_lbl = tk.Label(
            text_col,
            text="Evaluate interactions between policies using multiple decision-makers",
            font=(FONT_FAMILY, 10),
            bg="#f5f7fa", fg="#a3a3a3", justify="left",
            wraplength=280, cursor=CURSOR_HAND,
        )
        _slogan_lbl.pack(anchor="w")

        for _w in (hdr_exp, text_col, _title_lbl, _slogan_lbl):
            _w.bind("<Button-1>", lambda e: self._toggle_sidebar())

        # ── Collapsed header ───────────────────────────────────────────
        hdr_col = tk.Frame(sidebar, bg="#f5f7fa", height=90, cursor=CURSOR_HAND)
        hdr_col.pack_propagate(False)
        self._sidebar_hdr_col = hdr_col

        _PCK_BG  = "#1f2937"
        _PCK_FG  = "#f5f7fa"
        _PCK_R   = 6
        _PCK_PAD = 7
        _pck_font = tkFont.Font(family=FONT_FAMILY, size=12, weight="bold")
        _pck_tw   = _pck_font.measure("PCK")
        _pck_lh   = _pck_font.metrics("linespace")
        _pck_side = max(_pck_tw + _PCK_PAD * 2, _pck_lh + _PCK_PAD * 2)
        _pck_bw   = _pck_side
        _pck_bh   = _pck_side

        pck_c = tk.Canvas(hdr_col, width=_pck_bw, height=_pck_bh,
                          bg="#f5f7fa", highlightthickness=0, cursor=CURSOR_HAND)
        pck_c.place(relx=0.5, rely=0.5, anchor="center")

        def _draw_pck():
            pck_c.delete("all")
            x1, y1, x2, y2 = 1, 1, _pck_bw-1, _pck_bh-1
            r = _PCK_R; d = r * 2
            kw = dict(fill=_PCK_BG, outline=_PCK_BG)
            pck_c.create_arc(x1,      y1,      x1+d, y1+d, start=90,  extent=90, **kw)
            pck_c.create_arc(x2-d,    y1,      x2,   y1+d, start=0,   extent=90, **kw)
            pck_c.create_arc(x1,      y2-d,    x1+d, y2,   start=180, extent=90, **kw)
            pck_c.create_arc(x2-d,    y2-d,    x2,   y2,   start=270, extent=90, **kw)
            pck_c.create_rectangle(x1+r, y1, x2-r, y2, fill=_PCK_BG, outline=_PCK_BG)
            pck_c.create_rectangle(x1, y1+r, x2, y2-r, fill=_PCK_BG, outline=_PCK_BG)
            pck_c.create_text(_pck_bw//2, _pck_bh//2, text="PCK",
                              fill=_PCK_FG, font=_pck_font, anchor="center")

        _draw_pck()
        hdr_col.bind("<Button-1>", lambda e: self._toggle_sidebar())
        pck_c.bind("<Button-1>",   lambda e: self._toggle_sidebar())

        # ── Divider + PROJECTS label (always in layout for spacing) ──────
        exp_content = tk.Frame(sidebar, bg="#f5f7fa")
        exp_content.pack(fill="x")
        self._sidebar_exp_content = exp_content

        tk.Frame(exp_content, bg="#d3d3d3", height=1).pack(fill="x", pady=(0, 4))
        self._sidebar_proj_lbl = tk.Label(
            exp_content, text="PROJECTS",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg="#f5f7fa", fg="#a3a3a3", anchor="w",
        )
        self._sidebar_proj_lbl.pack(fill="x", padx=16, pady=(12, 10))

        # ── Project list (shared, content differs by state) ────────────
        self._sidebar_proj_list = tk.Frame(sidebar, bg="#f5f7fa")
        self._sidebar_proj_list.pack(fill="x")

        # Shared New Project button constants (used by both collapsed + expanded)
        _NP_BG     = "#eaeef4"
        _NP_HOVER  = "#d0dbe7"
        _NP_FG     = "#1f2937"
        _NP_RADIUS = 5
        _NP_H      = 40
        _NP_ICON   = 18
        _NP_GAP    = 6
        _NP_LABEL  = "New Project"

        _np_font   = tkFont.Font(family=FONT_FAMILY, size=13)
        _np_text_w = _np_font.measure(_NP_LABEL)
        _np_block  = _NP_ICON + _NP_GAP + _np_text_w   # total icon+gap+text width

        def _draw_np_icon(canvas, color, cx, cy):
            """Draw the folder+plus icon centered at (cx, cy)."""
            s  = _NP_ICON / 24.0
            ox = cx - _NP_ICON / 2
            oy = cy - _NP_ICON / 2
            fp = [
                4*s+ox,     20*s+oy,
                2*s+ox,     20*s+oy,
                2*s+ox,     5*s+oy,
                2*s+ox,     3*s+oy,
                7.93*s+ox,  3*s+oy,
                9.6*s+ox,   3.9*s+oy,
                10.21*s+ox, 5*s+oy,
                12.1*s+ox,  6*s+oy,
                20*s+ox,    6*s+oy,
                22*s+ox,    8*s+oy,
                22*s+ox,    20*s+oy,
                20*s+ox,    20*s+oy,
                4*s+ox,     20*s+oy,
            ]
            canvas.create_line(*fp, fill=color, width=1.35, capstyle="round", joinstyle="round")
            canvas.create_line(12*s+ox, 10*s+oy, 12*s+ox, 16*s+oy,
                               fill=color, width=1.35, capstyle="round")
            canvas.create_line(9*s+ox, 13*s+oy, 15*s+ox, 13*s+oy,
                               fill=color, width=1.35, capstyle="round")

        # ── Bottom: single New Project button (always packed at bottom) ──
        self._sidebar_bottom_exp = tk.Frame(sidebar, bg="#f5f7fa")
        self._sidebar_bottom_exp.pack(side="bottom", fill="x", padx=16, pady=(20, 32))

        _np_t    = [0.0]
        _np_anim = [None]

        btn_c = tk.Canvas(self._sidebar_bottom_exp, height=_NP_H+2, bg="#f5f7fa",
                          highlightthickness=0, cursor=CURSOR_HAND)
        btn_c.pack(fill="x")
        self._np_btn_c    = btn_c
        self._np_btn_draw = None  # set after _np_draw is defined

        def _np_draw(color):
            btn_c.delete("all")
            W = btn_c.winfo_width()
            if W < 2:
                return
            H = _NP_H
            r = _NP_RADIUS; d = r * 2
            x1, y1, x2, y2 = 1, 1, W-1, H-1
            btn_c.create_arc(x1,    y1,    x1+d, y1+d, start=90,  extent=90,  fill=color, outline=color)
            btn_c.create_arc(x2-d,  y1,    x2,   y1+d, start=0,   extent=90,  fill=color, outline=color)
            btn_c.create_arc(x1,    y2-d,  x1+d, y2,   start=180, extent=90,  fill=color, outline=color)
            btn_c.create_arc(x2-d,  y2-d,  x2,   y2,   start=270, extent=90,  fill=color, outline=color)
            btn_c.create_rectangle(x1+r, y1,   x2-r, y2,   fill=color, outline=color)
            btn_c.create_rectangle(x1,   y1+r, x2,   y2-r, fill=color, outline=color)
            if getattr(self, "_sidebar_expanded", True):
                # Expanded: icon + label centered together
                ix = (W - _np_block) / 2
                iy = H / 2
                _draw_np_icon(btn_c, _NP_FG, ix + _NP_ICON / 2, iy)
                btn_c.create_text(ix + _NP_ICON + _NP_GAP, iy, text=_NP_LABEL,
                                  fill=_NP_FG, anchor="w", font=_np_font)
            else:
                # Collapsed: icon only, centered
                _draw_np_icon(btn_c, _NP_FG, W / 2, H / 2)

        self._np_btn_draw = _np_draw

        def _np_animate(target):
            if _np_anim[0]:
                btn_c.after_cancel(_np_anim[0])
                _np_anim[0] = None
            def tick():
                diff = target - _np_t[0]
                if abs(diff) < 0.02:
                    _np_t[0] = target
                    _np_draw(_hex_interp(_NP_BG, _NP_HOVER, target))
                    _np_anim[0] = None
                    return
                _np_t[0] += diff * 0.3
                _np_draw(_hex_interp(_NP_BG, _NP_HOVER, _np_t[0]))
                _np_anim[0] = btn_c.after(16, tick)
            tick()

        def _np_poll():
            try:
                mx = btn_c.winfo_pointerx()
                my = btn_c.winfo_pointery()
                bx = btn_c.winfo_rootx()
                by = btn_c.winfo_rooty()
                bw = btn_c.winfo_width()
                bh = btn_c.winfo_height()
                over = bx <= mx <= bx + bw and by <= my <= by + bh
                target = 1.0 if over else 0.0
                if abs(_np_t[0] - target) > 0.01 and _np_anim[0] is None:
                    _np_animate(target)
            except tk.TclError:
                return
            btn_c.after(30, _np_poll)

        btn_c.bind("<Configure>", lambda e: _np_draw(_hex_interp(_NP_BG, _NP_HOVER, _np_t[0])))
        btn_c.bind("<Button-1>",  lambda e: self._new_project())
        btn_c.after(100, _np_poll)

        self._refresh_sidebar_projects()

    def _toggle_sidebar(self):
        self._sidebar_expanded = not self._sidebar_expanded
        if self._sidebar_expanded:
            self._sidebar_hdr_col.pack_forget()
            self._sidebar_hdr_exp.pack(fill="x", before=self._sidebar_exp_content)
            self._sidebar_proj_lbl.config(fg="#a3a3a3")
            self._sidebar_bottom_exp.pack_configure(padx=16, pady=(20, 32))
            self._sidebar.config(width=self._sidebar_exp_w)
        else:
            self._sidebar_hdr_exp.pack_forget()
            self._sidebar_hdr_col.pack(fill="x", before=self._sidebar_exp_content)
            self._sidebar_proj_lbl.config(fg="#f5f7fa")   # invisible text, keeps spacing
            self._sidebar_bottom_exp.pack_configure(padx=12, pady=(20, 32))
            self._sidebar.config(width=self._sidebar_col_w)
        # Redraw NP button for new state
        if self._np_btn_draw:
            self._np_btn_c.event_generate("<Configure>")
        self._refresh_sidebar_projects()

    def _build_toolbar(self):
        toolbar = tk.Frame(self._content, bg=COLOR_PANEL, pady=8)
        toolbar.pack(fill="x")

        # All buttons on the right
        export_btn = tk.Button(toolbar, text="Export to Excel",
                               command=self._export_excel)
        export_btn.config(bg=COLOR_PANEL, fg=COLOR_ACCENT2,
                          activebackground=COLOR_PANEL, activeforeground=COLOR_ACCENT,
                          relief="flat", padx=10, pady=5,
                          font=(FONT_FAMILY, FONT_SIZE_NORMAL), cursor=CURSOR_HAND)
        export_btn.pack(side="right", padx=(4, 16))

        import_btn = tk.Button(toolbar, text="Import Excel",
                               command=self._import_excel)
        import_btn.config(bg=COLOR_PANEL, fg=COLOR_ACCENT2,
                          activebackground=COLOR_PANEL, activeforeground=COLOR_ACCENT,
                          relief="flat", padx=10, pady=5,
                          font=(FONT_FAMILY, FONT_SIZE_NORMAL), cursor=CURSOR_HAND)
        import_btn.pack(side="right", padx=(0, 4))

        tk.Frame(toolbar, bg=COLOR_BORDER, width=1).pack(
            side="right", fill="y", padx=8, pady=4)

        agg_btn = tk.Button(toolbar, text="Run Analysis",
                            command=self._run_aggregation)
        agg_btn.config(bg=COLOR_PANEL, fg="#1a6e3c",
                       activebackground=COLOR_PANEL, activeforeground="#1a6e3c",
                       relief="flat", padx=10, pady=5,
                       font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                       cursor=CURSOR_HAND)
        agg_btn.pack(side="right", padx=4)

        tk.Frame(toolbar, bg=COLOR_BORDER, width=1).pack(
            side="right", fill="y", padx=8, pady=4)

        for label, cmd, fg in [
            ("Remove Tab",    self._remove_current_tab,  "#b71c1c"),
            ("Rename Tab",    self._rename_current_tab,  COLOR_ACCENT),
        ]:
            btn = tk.Button(toolbar, text=label, command=cmd)
            btn.config(bg=COLOR_PANEL, fg=fg,
                       activebackground=COLOR_PANEL, activeforeground=fg,
                       relief="flat", padx=10, pady=5,
                       font=(FONT_FAMILY, FONT_SIZE_NORMAL), cursor=CURSOR_HAND)
            btn.pack(side="right", padx=4)

    def _build_project_notebook(self):
        self._proj_nb_container = tk.Frame(self._content, bg=COLOR_BG)
        self._proj_nb_container.pack(fill="both", expand=True)
        self._proj_nb = ttk.Notebook(self._proj_nb_container)
        self._proj_nb.pack(fill="both", expand=True)

        self._empty_label = tk.Label(
            self._proj_nb_container,
            text='Click  "+ New Project"  to get started.',
            font=(FONT_FAMILY, FONT_SIZE_HEADER),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT, justify="center",
        )
        self._empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="Ready")
        tk.Label(self._content, textvariable=self._status_var,
                 font=(FONT_FAMILY, FONT_SIZE_SMALL),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
                 anchor="w", padx=12, pady=4).pack(fill="x", side="bottom")

    # ==================================================================
    # Project management
    # ==================================================================

    def _new_project(self):
        existing = [p.name for p in self.projects]
        dlg = _ProjectNameDialog(self.root, existing_names=existing)
        self.root.wait_window(dlg)
        if dlg.result:
            self._add_project(dlg.result)

    def _add_project(self, name: str):
        """Create a new Project and its top-level notebook tab."""
        self._empty_label.place_forget()

        proj = Project(name=name)

        # Outer frame inside the project notebook
        outer = tk.Frame(self._proj_nb, bg=COLOR_BG)
        self._proj_nb.add(outer, text=f"  {name}  ")
        self._proj_nb.select(outer)
        proj.frame = outer

        # Project header bar
        ph = tk.Frame(outer, bg=COLOR_ACCENT, height=32)
        ph.pack(fill="x")
        ph.pack_propagate(False)
        tk.Label(ph, text=f"Project:  {name}",
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                 bg=COLOR_ACCENT, fg="#ffffff").pack(side="left", padx=12, pady=6)

        # Inner notebook for DM tabs + analysis tabs
        inner_nb = ttk.Notebook(outer, style="Inner.TNotebook")
        inner_nb.pack(fill="both", expand=True)
        proj.notebook = inner_nb

        # Empty state inside project
        empty = tk.Label(
            outer,
            text='Click  "+ Add Decision-Maker"  to add the first matrix.',
            font=(FONT_FAMILY, FONT_SIZE_HEADER),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        )
        empty.place(relx=0.5, rely=0.55, anchor="center")
        proj._empty_label = empty

        self.projects.append(proj)
        self._sidebar_open_states[name] = True
        self._refresh_sidebar_projects()
        self._set_status(f'Project "{name}" created.')

    # ------------------------------------------------------------------
    # Sidebar project list helpers
    # ------------------------------------------------------------------

    def _make_chevron(self, parent, direction="right"):
        """Canvas drawing of a chevron-right or chevron-down icon (16×16)."""
        size = 16
        c = tk.Canvas(parent, width=size, height=size,
                      bg="#f5f7fa", highlightthickness=0)
        s = size / 24.0
        if direction == "right":
            pts = [9*s, 18*s, 15*s, 12*s, 9*s, 6*s]
        else:
            pts = [6*s, 9*s, 12*s, 15*s, 18*s, 9*s]
        c.create_line(*pts, fill="#a3a3a3", width=1.35,
                      capstyle="round", joinstyle="round")
        return c

    def _make_plus(self, parent, bg="#f5f7fa"):
        """Canvas drawing of a plus icon (16×16)."""
        size = 16
        c = tk.Canvas(parent, width=size, height=size,
                      bg=bg, highlightthickness=0)
        s = size / 24.0
        c.create_line(5*s, 12*s, 19*s, 12*s,
                      fill="#a3a3a3", width=1.35, capstyle="round")
        c.create_line(12*s, 5*s, 12*s, 19*s,
                      fill="#a3a3a3", width=1.35, capstyle="round")
        return c

    def _make_user_icon(self, parent, bg="#f5f7fa"):
        """Canvas drawing of Lucide user icon (16×16)."""
        size = 16
        c = tk.Canvas(parent, width=size, height=size,
                      bg=bg, highlightthickness=0)
        s = size / 24.0
        # Body arc: M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2
        # Approximate shoulders with a polyline
        c.create_line(
            19*s, 21*s, 19*s, 19*s,
            fill="#a3a3a3", width=1.35, capstyle="round", joinstyle="round",
        )
        c.create_line(
            5*s, 21*s, 5*s, 19*s,
            fill="#a3a3a3", width=1.35, capstyle="round", joinstyle="round",
        )
        # Shoulder curve approximated as arc
        c.create_arc(5*s, 11*s, 19*s, 23*s,
                     start=0, extent=180,
                     outline="#a3a3a3", width=1.35, style="arc")
        # Head circle: cx=12, cy=7, r=4
        r = 4*s
        cx, cy = 12*s, 7*s
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      outline="#a3a3a3", width=1.35, fill="")
        return c

    def _make_folder(self, parent):
        """Canvas drawing of folder icon tracing the Lucide SVG path (16×16)."""
        size = 16
        c = tk.Canvas(parent, width=size, height=size,
                      bg="#f5f7fa", highlightthickness=0)
        s = size / 24.0
        # Trace: M20 20 ... a2 2 ... V8 ... h-7.9 ... L9.6 3.9 ... H4 ... v13 ... Z
        # Approximated with straight-line segments (corner radii are ~1px at this scale)
        pts = [
            2*s,    5*s,    # top-left (after corner)
            4*s,    3*s,    # top-left body start
            7.93*s, 3*s,    # tab top-left
            9.6*s,  3.9*s,  # tab curve point
            12.1*s, 6*s,    # tab right meets body
            20*s,   6*s,    # top-right (before corner)
            22*s,   8*s,    # top-right (after corner)
            22*s,   18*s,   # bottom-right (before corner)
            20*s,   20*s,   # bottom-right (after corner)
            2*s,    20*s,   # bottom-left (before corner)
            2*s,    5*s,    # close back to start
        ]
        c.create_line(pts, fill="#a3a3a3", width=1.35,
                      capstyle="round", joinstyle="round")
        return c

    def _refresh_sidebar_projects(self):
        """Rebuild the project rows in the sidebar, preserving open/close state."""
        if not hasattr(self, "_sidebar_open_states"):
            self._sidebar_open_states = {}

        for w in self._sidebar_proj_list.winfo_children():
            w.destroy()

        # ── Collapsed view ─────────────────────────────────────────────
        if not getattr(self, "_sidebar_expanded", True):
            for proj in self.projects:
                abbrev = proj.name[:2].upper()
                _BG    = "#426387"
                _FG    = "#f5f7fa"
                _R     = 6
                _PAD   = 10
                _f     = tkFont.Font(family=FONT_FAMILY, size=12, weight="bold")
                _tw    = _f.measure(abbrev)
                _lh    = _f.metrics("linespace")
                _side  = max(_tw + _PAD * 2, _lh + _PAD * 2)
                bw = _side
                bh = _side
                wrap = tk.Frame(self._sidebar_proj_list, bg="#f5f7fa")
                wrap.pack(fill="x", pady=4)
                bc = tk.Canvas(wrap, width=bw, height=bh,
                               bg="#f5f7fa", highlightthickness=0, cursor=CURSOR_HAND)
                bc.pack()
                r = _R; d = r * 2
                x1, y1, x2, y2 = 1, 1, bw-1, bh-1
                kw = dict(fill=_BG, outline=_BG)
                bc.create_arc(x1,    y1,    x1+d, y1+d, start=90,  extent=90, **kw)
                bc.create_arc(x2-d,  y1,    x2,   y1+d, start=0,   extent=90, **kw)
                bc.create_arc(x1,    y2-d,  x1+d, y2,   start=180, extent=90, **kw)
                bc.create_arc(x2-d,  y2-d,  x2,   y2,   start=270, extent=90, **kw)
                bc.create_rectangle(x1+r, y1, x2-r, y2, fill=_BG, outline=_BG)
                bc.create_rectangle(x1, y1+r, x2, y2-r, fill=_BG, outline=_BG)
                bc.create_text(bw // 2, bh // 2, text=abbrev,
                               fill=_FG, font=_f, anchor="center")
                bc.bind("<Button-1>", lambda e, p=proj: self._proj_nb.select(p.frame))
            return

        # ── Expanded view ──────────────────────────────────────────────
        if not self.projects:
            tk.Label(
                self._sidebar_proj_list,
                text="No projects available.\nCreate a new project to begin assessing interactions between policies across decision-makers.",
                font=(FONT_FAMILY, 11),
                bg="#f5f7fa", fg="#a3a3a3",
                justify="left", anchor="w",
                wraplength=270,
            ).pack(anchor="w", padx=20, pady=(4, 0))
            return

        _HOVER_BG  = "#ebebeb"
        _NORMAL_BG = "#f5f7fa"

        for proj in self.projects:
            is_open = self._sidebar_open_states.get(proj.name, False)

            row = tk.Frame(self._sidebar_proj_list, bg="#f5f7fa", cursor=CURSOR_HAND)
            row.pack(fill="x", padx=20, pady=1)

            chevron = self._make_chevron(row, "down" if is_open else "right")
            chevron.grid(row=0, column=0, padx=(0, 4), pady=(3, 0), sticky="n")

            folder = self._make_folder(row)
            folder.grid(row=0, column=1, padx=(0, 6), pady=(3, 0), sticky="n")

            name_lbl = tk.Label(
                row, text=proj.name,
                font=(FONT_FAMILY, 14),
                bg="#f5f7fa", fg="#2c3b4e", anchor="nw",
                justify="left", wraplength=236,
                pady=0,
            )
            name_lbl.grid(row=0, column=2, sticky="nw")
            row.grid_columnconfigure(2, weight=1)

            # Collapsible content
            content = tk.Frame(self._sidebar_proj_list, bg="#f5f7fa")
            tk.Frame(content, bg="#f5f7fa", height=8).pack(fill="x")  # top spacer

            # Add DM button — canvas for rounded corners
            dm_wrap = tk.Frame(content, bg="#f5f7fa")
            dm_wrap.pack(fill="x", padx=20, pady=(0, 2))

            _DM_RR       = 5
            _dm_btn_t    = [0.0]
            _dm_btn_anim = [None]
            _dm_bg_items = []

            dm_row = tk.Canvas(dm_wrap, height=32, bg="#f5f7fa",
                               highlightthickness=0, cursor=CURSOR_HAND)
            dm_row.pack(fill="x")

            dm_lbl = tk.Label(
                dm_row, text="DECISION-MAKERS",
                font=(FONT_FAMILY, 11),
                bg=_NORMAL_BG, fg="#a3a3a3", anchor="w",
                padx=0, pady=0,
            )
            lbl_win  = dm_row.create_window(20, 15, anchor="w", window=dm_lbl)
            plus_icon = self._make_plus(dm_row, bg=_NORMAL_BG)
            icon_win = [dm_row.create_window(0, 15, anchor="e", window=plus_icon)]

            def _dm_rebuild_rr(color):
                for item in _dm_bg_items:
                    try: dm_row.delete(item)
                    except tk.TclError: pass
                _dm_bg_items.clear()
                W = dm_row.winfo_width()
                if W < 2:
                    return
                H = 30; r = _DM_RR; d = r * 2
                x1, y1, x2, y2 = 1, 1, W-1, H-1
                kw = dict(fill=color, outline=color)
                _dm_bg_items.extend([
                    dm_row.create_arc(x1,    y1,    x1+d, y1+d, start=90,  extent=90, **kw),
                    dm_row.create_arc(x2-d,  y1,    x2,   y1+d, start=0,   extent=90, **kw),
                    dm_row.create_arc(x1,    y2-d,  x1+d, y2,   start=180, extent=90, **kw),
                    dm_row.create_arc(x2-d,  y2-d,  x2,   y2,   start=270, extent=90, **kw),
                    dm_row.create_rectangle(x1+r, y1,   x2-r, y2,   **kw),
                    dm_row.create_rectangle(x1,   y1+r, x2,   y2-r, **kw),
                ])
                dm_row.tag_raise(lbl_win)
                dm_row.tag_raise(icon_win[0])
                dm_row.coords(icon_win[0], W - 12, 15)
                try: dm_lbl.config(bg=color); plus_icon.config(bg=color)
                except tk.TclError: pass

            def _dm_update_color(color):
                for item in _dm_bg_items:
                    try: dm_row.itemconfig(item, fill=color, outline=color)
                    except tk.TclError: pass
                try: dm_lbl.config(bg=color); plus_icon.config(bg=color)
                except tk.TclError: pass

            def _dm_btn_animate(target):
                if _dm_btn_anim[0]:
                    dm_row.after_cancel(_dm_btn_anim[0])
                    _dm_btn_anim[0] = None
                def tick():
                    diff = target - _dm_btn_t[0]
                    if abs(diff) < 0.02:
                        _dm_btn_t[0] = target
                        _dm_update_color(_hex_interp(_NORMAL_BG, _HOVER_BG, target))
                        _dm_btn_anim[0] = None
                        return
                    _dm_btn_t[0] += diff * 0.3
                    _dm_update_color(_hex_interp(_NORMAL_BG, _HOVER_BG, _dm_btn_t[0]))
                    _dm_btn_anim[0] = dm_row.after(16, tick)
                tick()

            def _hover_in(e):
                _dm_btn_animate(1.0)

            def _hover_out(e):
                _dm_btn_animate(0.0)

            dm_row.bind("<Configure>", lambda e: _dm_rebuild_rr(
                _hex_interp(_NORMAL_BG, _HOVER_BG, _dm_btn_t[0])))
            dm_row.after(50, lambda: _dm_rebuild_rr(_NORMAL_BG))

            for w in (dm_wrap, dm_row, dm_lbl, plus_icon):
                w.bind("<Enter>", _hover_in)
                w.bind("<Leave>", _hover_out)
                w.bind("<Button-1>", lambda e: self._add_matrix())

            # DM list
            dm_list_frame = tk.Frame(content, bg="#f5f7fa")
            dm_list_frame.pack(fill="x", pady=(1, 0))

            _DM_ITEM_RR    = 5
            _DM_ITEM_HOVER = "#eaeef4"

            for matrix in proj.matrices:
                dm_item_wrap = tk.Frame(dm_list_frame, bg="#f5f7fa")
                dm_item_wrap.pack(fill="x", padx=20, pady=1)

                _item_t       = [0.0]
                _item_anim    = [None]
                _item_bg_itms = []

                dm_item = tk.Canvas(dm_item_wrap, height=36, bg="#f5f7fa",
                                    highlightthickness=0, cursor=CURSOR_HAND)
                dm_item.pack(fill="x")

                user_ic = self._make_user_icon(dm_item, bg="#f5f7fa")
                u_win = dm_item.create_window(28, 18, anchor="w", window=user_ic)

                dm_name_lbl = tk.Label(
                    dm_item, text=matrix.decision_maker,
                    font=(FONT_FAMILY, 13),
                    bg="#f5f7fa", fg="#426387", anchor="w",
                    justify="left", wraplength=210,
                    pady=0,
                )
                n_win = dm_item.create_window(50, 18, anchor="w", window=dm_name_lbl)

                def _resize_canvas(e, cv=dm_item, lbl=dm_name_lbl,
                                   uw=u_win, nw=n_win):
                    lh = lbl.winfo_reqheight()
                    new_h = max(36, lh + 16)
                    cv.config(height=new_h)
                    cy = new_h // 2
                    cv.coords(uw, 28, cy)
                    cv.coords(nw, 50, cy)

                dm_name_lbl.bind("<Configure>", _resize_canvas)

                def _item_rebuild_rr(color, cv=dm_item, bi=_item_bg_itms,
                                     uw=u_win, nw=n_win,
                                     u=user_ic, lbl=dm_name_lbl):
                    for item in bi:
                        try: cv.delete(item)
                        except tk.TclError: pass
                    bi.clear()
                    W = cv.winfo_width()
                    H = cv.winfo_height()
                    if W < 2 or H < 2:
                        return
                    r = _DM_ITEM_RR; d = r * 2
                    x1, y1, x2, y2 = 1, 1, W-1, H-1
                    kw = dict(fill=color, outline=color)
                    bi.extend([
                        cv.create_arc(x1,    y1,    x1+d, y1+d, start=90,  extent=90, **kw),
                        cv.create_arc(x2-d,  y1,    x2,   y1+d, start=0,   extent=90, **kw),
                        cv.create_arc(x1,    y2-d,  x1+d, y2,   start=180, extent=90, **kw),
                        cv.create_arc(x2-d,  y2-d,  x2,   y2,   start=270, extent=90, **kw),
                        cv.create_rectangle(x1+r, y1,   x2-r, y2,   **kw),
                        cv.create_rectangle(x1,   y1+r, x2,   y2-r, **kw),
                    ])
                    cv.tag_raise(uw)
                    cv.tag_raise(nw)
                    try: u.config(bg=color); lbl.config(bg=color)
                    except tk.TclError: pass

                def _item_update_color(color, cv=dm_item, bi=_item_bg_itms,
                                       u=user_ic, lbl=dm_name_lbl):
                    for item in bi:
                        try: cv.itemconfig(item, fill=color, outline=color)
                        except tk.TclError: pass
                    try: u.config(bg=color); lbl.config(bg=color)
                    except tk.TclError: pass

                def _dm_item_animate(target, cv=dm_item, t=_item_t, anim=_item_anim,
                                     upd=_item_update_color):
                    if anim[0]:
                        cv.after_cancel(anim[0])
                        anim[0] = None
                    def tick():
                        diff = target - t[0]
                        if abs(diff) < 0.02:
                            t[0] = target
                            upd(_hex_interp(_NORMAL_BG, _DM_ITEM_HOVER, target))
                            anim[0] = None
                            return
                        t[0] += diff * 0.3
                        upd(_hex_interp(_NORMAL_BG, _DM_ITEM_HOVER, t[0]))
                        anim[0] = cv.after(16, tick)
                    tick()

                def _dm_hover_in(e, animate=_dm_item_animate):
                    animate(1.0)

                def _dm_hover_out(e, animate=_dm_item_animate):
                    animate(0.0)

                def _dm_click(e, p=proj, m=matrix):
                    self._proj_nb.select(p.frame)
                    if hasattr(m, "_tab"):
                        p.notebook.select(m._tab)

                dm_item.bind("<Configure>", lambda e, rb=_item_rebuild_rr, t=_item_t:
                             rb(_hex_interp(_NORMAL_BG, _DM_ITEM_HOVER, t[0])))
                dm_item.after(50, lambda rb=_item_rebuild_rr: rb(_NORMAL_BG))

                for w in (dm_item_wrap, dm_item, dm_name_lbl, user_ic):
                    w.bind("<Enter>", _dm_hover_in)
                    w.bind("<Leave>", _dm_hover_out)
                    w.bind("<Button-1>", _dm_click)

            def _toggle(event, cv=chevron, pname=proj.name, ct=content, rw=row):
                self._sidebar_open_states[pname] = not self._sidebar_open_states.get(pname, False)
                opened = self._sidebar_open_states[pname]
                cv.delete("all")
                s = 16 / 24.0
                if opened:
                    pts = [6*s, 9*s, 12*s, 15*s, 18*s, 9*s]
                else:
                    pts = [9*s, 18*s, 15*s, 12*s, 9*s, 6*s]
                cv.create_line(*pts, fill="#a3a3a3", width=1.35,
                               capstyle="round", joinstyle="round")
                if opened:
                    ct.pack(fill="x", after=rw)
                else:
                    ct.pack_forget()

            if is_open:
                content.pack(fill="x", after=row)

            chevron.bind("<Button-1>", _toggle)
            row.bind("<Button-1>", _toggle)
            name_lbl.bind("<Button-1>", _toggle)
            folder.bind("<Button-1>", _toggle)

    def _current_project(self) -> Optional[Project]:
        """Return the currently selected project, or None."""
        if not self._proj_nb.tabs():
            return None
        try:
            idx = self._proj_nb.index("current")
            return self.projects[idx]
        except (tk.TclError, IndexError):
            return None

    def _rename_project(self):
        proj = self._current_project()
        if not proj:
            messagebox.showinfo("No Project", "No project is open.", parent=self.root)
            return
        existing = [p.name for p in self.projects if p is not proj]
        dlg = _SimpleInputDialog(self.root, "Rename Project",
                                 "New project name:", proj.name)
        self.root.wait_window(dlg)
        if dlg.result and dlg.result != proj.name:
            if dlg.result in [p.name for p in self.projects]:
                messagebox.showwarning("Duplicate Name",
                                       f'A project named "{dlg.result}" already exists.',
                                       parent=self.root)
                return
            idx = self._proj_nb.index("current")
            proj.name = dlg.result
            self._proj_nb.tab(idx, text=f"  {dlg.result}  ")
            # Update project header bar
            for widget in proj.frame.winfo_children():
                if isinstance(widget, tk.Frame) and widget.cget("bg") == COLOR_ACCENT:
                    for lbl in widget.winfo_children():
                        if isinstance(lbl, tk.Label):
                            lbl.config(text=f"Project:  {dlg.result}")
            self._set_status(f'Project renamed to "{dlg.result}".')

    def _delete_project(self):
        proj = self._current_project()
        if not proj:
            messagebox.showinfo("No Project", "No project is open.",
                                parent=self.root)
            return
        if not messagebox.askyesno(
            "Delete Project",
            f'Permanently delete project "{proj.name}" and all its data?\n'
            "This cannot be undone.",
            parent=self.root,
        ):
            return
        idx = self._proj_nb.index("current")
        self._proj_nb.forget(idx)
        self.projects.pop(idx)
        self._refresh_sidebar_projects()
        if not self.projects:
            self._empty_label.place(relx=0.5, rely=0.5, anchor="center")
        self._set_status(f'Project "{proj.name}" deleted.')

    # ==================================================================
    # Decision-maker tab management (operates on current project)
    # ==================================================================

    def _add_matrix(self):
        proj = self._current_project()
        if not proj:
            messagebox.showinfo("No Project",
                                "Create a project first.", parent=self.root)
            return

        if proj.matrices:
            # Reuse existing policy list
            dlg = _SimpleInputDialog(self.root, "Add Decision-Maker",
                                     "Decision-Maker Name:")
            self.root.wait_window(dlg)
            if not dlg.result:
                return
            dm_name  = dlg.result
            policies = proj.matrices[0].policies
        else:
            dlg = NewMatrixDialog(self.root)
            self.root.wait_window(dlg)
            if dlg.result is None:
                return
            dm_name, policies = dlg.result

        matrix = make_empty_matrix(dm_name, policies)
        proj.matrices.append(matrix)
        self._create_dm_tab(proj, matrix)
        self._refresh_sidebar_projects()
        self._set_status(f'"{dm_name}" added to project "{proj.name}".')

    def _create_dm_tab(self, proj: Project, matrix: PolicyMatrix):
        """Build one DM matrix tab inside the project's inner notebook."""
        proj._empty_label.place_forget()

        tab = tk.Frame(proj.notebook, bg=COLOR_BG)
        proj.notebook.add(tab, text=f"  {matrix.decision_maker}  ")
        proj.notebook.select(tab)
        matrix._tab = tab

        # Info bar
        info = tk.Frame(tab, bg=COLOR_PANEL, pady=6)
        info.pack(fill="x")
        tk.Label(info, text=f"Decision-Maker:  {matrix.decision_maker}",
                 font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_ACCENT).pack(side="left", padx=16)
        tk.Label(info, text=f"{len(matrix.policies)} policies  |  "
                            f"{matrix.total_cells()} cells to fill",
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT).pack(side="left", padx=6)

        tk.Frame(tab, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)

        def on_change(r, c, v):
            filled = matrix.filled_count()
            total  = matrix.total_cells()
            self._set_status(
                f'"{matrix.decision_maker}"  --  {filled}/{total} cells filled  '
                f'|  {matrix.codes[r]} -> {matrix.codes[c]}: {v}'
            )

        mw = MatrixWidget(tab, matrix, on_change=on_change)
        mw.pack(fill="both", expand=True, padx=8, pady=8)

    def _current_inner_index(self, proj: Project) -> int:
        if not proj.notebook.tabs():
            return -1
        try:
            return proj.notebook.index("current")
        except tk.TclError:
            return -1

    def _rename_current_tab(self):
        proj = self._current_project()
        if not proj:
            return
        idx = self._current_inner_index(proj)
        if idx < 0:
            return
        # Only DM tabs (before agg tabs) can be renamed
        n_dm = len(proj.matrices)
        if idx >= n_dm:
            messagebox.showinfo("Cannot Rename",
                                "Analysis result tabs cannot be renamed.",
                                parent=self.root)
            return
        matrix = proj.matrices[idx]
        dlg = _SimpleInputDialog(self.root, "Rename Tab",
                                 "New decision-maker name:", matrix.decision_maker)
        self.root.wait_window(dlg)
        if dlg.result:
            matrix.decision_maker = dlg.result
            proj.notebook.tab(idx, text=f"  {dlg.result}  ")
            self._set_status(f'Renamed to "{dlg.result}".')

    def _remove_current_tab(self):
        proj = self._current_project()
        if not proj:
            return
        idx = self._current_inner_index(proj)
        if idx < 0:
            return
        n_dm = len(proj.matrices)

        if idx >= n_dm:
            # Analysis result tab
            if not messagebox.askyesno("Remove Tab",
                                       "Remove this analysis result tab?",
                                       parent=self.root):
                return
            tab_id = proj.notebook.tabs()[idx]
            proj.notebook.forget(idx)
            if tab_id in proj.agg_tab_ids:
                proj.agg_tab_ids.remove(tab_id)
            self._set_status("Analysis tab removed.")
        else:
            # DM tab
            dm = proj.matrices[idx].decision_maker
            if not messagebox.askyesno("Remove Matrix",
                                       f'Remove matrix for "{dm}"?',
                                       parent=self.root):
                return
            proj.notebook.forget(idx)
            proj.matrices.pop(idx)
            if not proj.matrices:
                proj._empty_label.place(relx=0.5, rely=0.55, anchor="center")
            self._set_status(f'Removed "{dm}".')

    # ==================================================================
    # Aggregation / Analysis (operates on current project)
    # ==================================================================

    def _run_aggregation(self):
        proj = self._current_project()
        if not proj:
            messagebox.showinfo("No Project", "Create a project first.",
                                parent=self.root)
            return

        if len(proj.matrices) < 2:
            messagebox.showwarning("Not Enough Matrices",
                                   "You need at least 2 decision-maker matrices.",
                                   parent=self.root)
            return

        incomplete = check_completeness(proj.matrices)
        if incomplete:
            lines = []
            for dm_name, blanks in incomplete:
                cells = ", ".join(f"{r}->{c}" for r, c in blanks[:10])
                suffix = f" (+{len(blanks)-10} more)" if len(blanks) > 10 else ""
                lines.append(f"  {dm_name}: {cells}{suffix}")
            messagebox.showerror("Incomplete Matrices",
                                 "Please fill all cells before aggregating.\n\n"
                                 + "\n".join(lines), parent=self.root)
            return

        n_dms = len(proj.matrices)
        if n_dms < 3:
            method = "average"
        else:
            dlg = AggregationMethodDialog(
                self.root, [m.decision_maker for m in proj.matrices])
            self.root.wait_window(dlg)
            if dlg.result is None:
                return
            method = dlg.result

        weights = None
        if method == "weighted":
            dlg_w = WeightDialog(
                self.root, [m.decision_maker for m in proj.matrices])
            self.root.wait_window(dlg_w)
            if dlg_w.result is None:
                return
            weights = dlg_w.result

        if method == "average":
            result = aggregate_average(proj.matrices)
        elif method == "majority":
            result = aggregate_majority(proj.matrices)
        elif method == "weighted":
            result = aggregate_weighted(proj.matrices, weights)
        else:
            return

        if result.ties:
            dlg_t = TieResolutionDialog(self.root, result.ties)
            self.root.wait_window(dlg_t)
            if dlg_t.result is None:
                return
            resolve_ties(result)

        self._create_analysis_tabs(proj, result)
        self._set_status(
            f'Analysis complete for "{proj.name}"  |  method: {method}  '
            f'|  {n_dms} decision-makers'
        )

    def _create_analysis_tabs(self, proj: Project, result: AggregationResult):
        """Add all six analysis tabs to the project's inner notebook."""
        method_label = {
            "average":  "Average",
            "majority": "Majority",
            "weighted": "Weighted",
        }.get(result.method, result.method.title())

        proj.agg_results.append(result)

        tabs = [
            (f"  Aggregated ({method_label})  ",       AggregationTab),
            (f"  Coherence Scores ({method_label})  ", CoherenceScoresTab),
            (f"  Range of Influence ({method_label})  ", RangeOfInfluenceTab),
            (f"  PCA ({method_label})  ",              PCATab),
            (f"  Network Analysis ({method_label})  ", NetworkTab),
            (f"  LLM Interpretation ({method_label})  ", LLMInterpretationTab),
        ]

        first = True
        for title, TabClass in tabs:
            widget = TabClass(proj.notebook, result)
            proj.notebook.add(widget, text=title)
            tab_id = proj.notebook.tabs()[-1]
            proj.agg_tab_ids.append(tab_id)
            if first:
                proj.notebook.select(widget)
                first = False

    # ==================================================================
    # Import (operates on current project)
    # ==================================================================

    def _import_excel(self):
        proj = self._current_project()
        if not proj:
            messagebox.showinfo("No Project", "Create a project first.",
                                parent=self.root)
            return

        path = filedialog.askopenfilename(
            parent=self.root,
            title="Import matrices from Excel workbook",
            filetypes=[("Excel Workbook", "*.xlsx *.xls")],
        )
        if not path:
            return

        try:
            result = import_matrices_from_excel(path)
        except (ValueError, ImportError) as exc:
            messagebox.showerror("Import Error", str(exc), parent=self.root)
            return

        if not result.matrices:
            messagebox.showwarning("Nothing Imported",
                                   "No valid matrices were found in the workbook.",
                                   parent=self.root)
            return

        ref_policies = (
            proj.matrices[0].policies if proj.matrices
            else result.matrices[0].policies
        )

        mismatches = [m.decision_maker for m in result.matrices
                      if m.policies != ref_policies]
        if mismatches:
            msg = ("The following sheets have a different policy list "
                   "and cannot be imported:\n\n"
                   + "\n".join("  - " + dm for dm in mismatches)
                   + "\n\nAll matrices must share the same policy list.")
            messagebox.showerror("Policy List Mismatch", msg, parent=self.root)
            return

        added = 0
        for matrix in result.matrices:
            if matrix.policies == ref_policies:
                proj.matrices.append(matrix)
                self._create_dm_tab(proj, matrix)
                added += 1

        if result.warnings:
            msg = (str(added) + " matrix/matrices imported.\n\n"
                   "The following sheets have blank cells:\n\n"
                   + "\n".join(result.warnings))
            messagebox.showwarning("Import Complete with Warnings",
                                   msg, parent=self.root)
        else:
            messagebox.showinfo("Import Complete",
                                str(added) + " matrix/matrices imported successfully.",
                                parent=self.root)

        self._set_status(f"Imported {added} matrix/matrices from: {path}")

    # ==================================================================
    # Export (operates on current project)
    # ==================================================================

    def _export_excel(self):
        proj = self._current_project()
        if not proj:
            messagebox.showinfo("No Project", "Create a project first.",
                                parent=self.root)
            return
        if not proj.matrices:
            messagebox.showinfo("Nothing to Export",
                                "Add at least one matrix before exporting.",
                                parent=self.root)
            return

        initial = f"{proj.name}_coherence.xlsx".replace(" ", "_")
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title=f"Export project: {proj.name}",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile=initial,
        )
        if not path:
            return

        try:
            _export_to_excel(proj.matrices, proj.agg_results, path)
            self._set_status(f"Exported to: {path}")
            messagebox.showinfo("Export Complete",
                                f"Saved to:\n{path}", parent=self.root)
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc), parent=self.root)

    # ==================================================================
    # Status
    # ==================================================================

    def _set_status(self, message: str):
        self._status_var.set(message)


# =============================================================================
# Excel export helper
# =============================================================================

def _export_to_excel(matrices, agg_results, path: str):
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    except ImportError:
        raise ImportError("openpyxl is required.\nInstall: pip install openpyxl")

    from constants import RATING_COLORS, RATING_TEXT_COLORS
    from coherence_scores_tab import compute_scores
    from range_of_influence_tab import compute_entropy
    from network_tab import compute_centrality

    thin   = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def auto_width(ws):
        for col in ws.columns:
            letter  = col[0].column_letter
            max_len = max((len(str(c.value)) for c in col if c.value), default=0)
            ws.column_dimensions[letter].width = max(max_len + 4, 14)

    def hcell(ws, row, col, value):
        c = ws.cell(row=row, column=col, value=value)
        c.font      = Font(bold=True, color="FFFFFF")
        c.fill      = PatternFill("solid", fgColor="2C4A6E")
        c.alignment = Alignment(horizontal="center")
        c.border    = border
        return c

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # DM matrices
    for matrix in matrices:
        ws    = wb.create_sheet(title=matrix.decision_maker[:31])
        n     = len(matrix.policies)
        codes = matrix.codes
        ws.cell(row=1, column=1, value="Policy Index").font = Font(bold=True)
        for k, (code, name) in enumerate(zip(codes, matrix.policies)):
            ws.cell(row=1, column=k+2, value=f"{code}: {name}")
        ws.cell(row=3, column=1, value="Influencing / Influenced")
        ws.cell(row=3, column=1).font = Font(bold=True, italic=True)
        for j, code in enumerate(codes):
            hcell(ws, 3, j+2, code)
        for i, rc in enumerate(codes):
            rh = ws.cell(row=i+4, column=1, value=rc)
            rh.font = Font(bold=True, color="FFFFFF")
            rh.fill = PatternFill("solid", fgColor="2C4A6E")
            rh.alignment = Alignment(horizontal="center")
            rh.border = border
            for j in range(n):
                value = matrix.get_rating(i, j)
                cell  = ws.cell(row=i+4, column=j+2, value=value)
                cell.alignment = Alignment(horizontal="center")
                cell.border = border
                if value in RATING_COLORS:
                    cell.fill = PatternFill("solid",
                        fgColor=RATING_COLORS[value].lstrip("#").upper())
                    cell.font = Font(
                        color=RATING_TEXT_COLORS[value].lstrip("#").upper())
        auto_width(ws)

    # Analysis results
    for idx, result in enumerate(agg_results):
        ml     = {"average":"Avg","majority":"Majority","weighted":"Weighted"
                  }.get(result.method, result.method.title())
        suffix = f" {idx+1}" if len(agg_results) > 1 else ""
        pfx    = f"{ml}{suffix}"
        n, codes = result.n, result.codes

        # Aggregated matrix
        ws = wb.create_sheet(title=f"Aggregated ({pfx})"[:31])
        ws.cell(row=1, column=1, value="Policy Index").font = Font(bold=True)
        for k, (code, name) in enumerate(zip(codes, result.policies)):
            ws.cell(row=1, column=k+2, value=f"{code}: {name}")
        ws.cell(row=3, column=1, value="Influencing / Influenced")
        ws.cell(row=3, column=1).font = Font(bold=True, italic=True)
        for j, code in enumerate(codes): hcell(ws, 3, j+2, code)
        for i, rc in enumerate(codes):
            rh = ws.cell(row=i+4, column=1, value=rc)
            rh.font = Font(bold=True, color="FFFFFF")
            rh.fill = PatternFill("solid", fgColor="2C4A6E")
            rh.alignment = Alignment(horizontal="center")
            rh.border = border
            for j in range(n):
                s = result.scores.get((i,j), 0.0) or 0.0
                cell = ws.cell(row=i+4, column=j+2, value=s)
                cell.alignment = Alignment(horizontal="center")
                cell.border = border
                cell.number_format = "0.00"
        auto_width(ws)

        # Coherence scores
        ws = wb.create_sheet(title=f"Coh Scores ({pfx})"[:31])
        for c, h in enumerate(["Code","Policy","OI","II","WOI","WII"], 1):
            hcell(ws, 1, c, h)
        for r, row in enumerate(compute_scores(result), 2):
            for c, v in enumerate([row["code"], row["policy"], row["oi"],
                                    row["ii"], row["woi"], row["wii"]], 1):
                ws.cell(row=r, column=c, value=v)
        auto_width(ws)

        # Range of influence
        ws = wb.create_sheet(title=f"Range Influence ({pfx})"[:31])
        for c, h in enumerate(["Code","Policy","Entropy","Category"], 1):
            hcell(ws, 1, c, h)
        for r, row in enumerate(compute_entropy(result), 2):
            for c, v in enumerate([row["code"], row["policy"],
                                    row["entropy"], row["category"]], 1):
                ws.cell(row=r, column=c, value=v)
        auto_width(ws)

        # Network centrality
        ws = wb.create_sheet(title=f"Centrality ({pfx})"[:31])
        for c, h in enumerate(["Code","Policy","Betweenness","Closeness"], 1):
            hcell(ws, 1, c, h)
        for r, row in enumerate(
                sorted(compute_centrality(result),
                       key=lambda x: x["betweenness"], reverse=True), 2):
            for c, v in enumerate([row["code"], row["policy"],
                                    row["betweenness"], row["closeness"]], 1):
                ws.cell(row=r, column=c, value=v)
        auto_width(ws)

    wb.save(path)
