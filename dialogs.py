# =============================================================================
# Policy Coherence Kit -- dialogs.py
# NewMatrixDialog : collect decision-maker name + policy list (or file import)
# _SimpleInputDialog : single-field reusable prompt (used by app.py for rename)
# _read_policies_from_file : parse xlsx / csv into a list of policy name strings
# =============================================================================

import math
import sys
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Tuple

from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_TEXT,
    COLOR_TEXT_LIGHT, COLOR_BUTTON, COLOR_BUTTON_FG, COLOR_BORDER,
    CURSOR_HAND,
)
from theme import (
    MODAL_ACTION_BG,
    MODAL_ACTION_BORDER,
    MODAL_ACTION_FG,
    MODAL_ACTION_GAP,
    MODAL_ACTION_HEIGHT,
    MODAL_ACTION_HOVER_BG,
    MODAL_ACTION_ICON_SIZE,
    MODAL_ACTION_IMPORT_TEXT,
    MODAL_ACTION_PADX,
    MODAL_ACTION_RADIUS,
    MODAL_ACTION_TEXT_SIZE,
    MODAL_ADD_BTN_BG,
    MODAL_ADD_BTN_BORDER,
    MODAL_ADD_BTN_GAP,
    MODAL_ADD_BTN_HOVER_BG,
    MODAL_ADD_BTN_ICON_COLOR,
    MODAL_ADD_BTN_ICON_SIZE,
    MODAL_ADD_BTN_HEIGHT,
    MODAL_ADD_BTN_RADIUS,
    MODAL_ADD_BTN_STROKE,
    MODAL_ADD_BTN_TEXT,
    MODAL_ADD_BTN_TEXT_SIZE,
    MODAL_ADD_BTN_WIDTH,
    MODAL_BG,
    MODAL_BORDER,
    MODAL_CLOSE_CANVAS_SIZE,
    MODAL_CLOSE_ICON_COLOR,
    MODAL_CLOSE_HOVER_BG,
    MODAL_CLOSE_HOVER_RADIUS,
    MODAL_CLOSE_ICON_SIZE,
    MODAL_CLOSE_STROKE,
    MODAL_DIVIDER_COLOR,
    MODAL_DM_HINT,
    MODAL_DM_PLACEHOLDER,
    MODAL_FIELD_BG,
    MODAL_FIELD_BORDER,
    MODAL_FIELD_HEIGHT,
    MODAL_FIELD_LABEL_COLOR,
    MODAL_FIELD_LABEL_SIZE,
    MODAL_FIELD_PLACEHOLDER,
    MODAL_FIELD_PLACEHOLDER_COLOR,
    MODAL_FIELD_PLACEHOLDER_SIZE,
    MODAL_FIELD_RADIUS,
    MODAL_FIELD_TEXT_SIZE,
    MODAL_POLICY_HINT,
    MODAL_POLICY_PLACEHOLDER,
    MODAL_PROJECT_HINT,
    MODAL_RADIUS,
    MODAL_SECTION_ROW_GAP,
    MODAL_SECTION_HINT_COLOR,
    MODAL_SECTION_HINT_SIZE,
    MODAL_SECTION_TITLE_COLOR,
    MODAL_SECTION_TITLE_SIZE,
    MODAL_SUBTITLE_COLOR,
    MODAL_SUBTITLE_SIZE,
    MODAL_TITLE_COLOR,
    MODAL_TITLE_SIZE,
    TOPBAR_DELETE_TAB_FG,
    TOPBAR_EXCEL_BG,
    TOPBAR_EXCEL_BORDER,
    TOPBAR_EXCEL_HEIGHT,
    TOPBAR_EXCEL_HOVER_BG,
    TOPBAR_EXCEL_PADX,
    TOPBAR_EXCEL_RADIUS,
    TOPBAR_EXCEL_TEXT_SIZE,
    TOPBAR_RUN_ANALYSIS_BG,
    TOPBAR_RUN_ANALYSIS_FG,
    TOPBAR_RUN_ANALYSIS_HEIGHT,
    TOPBAR_RUN_ANALYSIS_HOVER_BG,
    TOPBAR_RUN_ANALYSIS_PADX,
    TOPBAR_RUN_ANALYSIS_RADIUS,
    TOPBAR_RUN_ANALYSIS_TEXT_SIZE,
)
from matrix_widget import _PillScrollbar


def _create_rounded_rect(canvas, x1, y1, x2, y2, r,
                          fill="", outline="black", width=1, tags=()):
    """Draw a filled, outlined rounded rectangle on a Canvas."""
    canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90,
                      style="pieslice", fill=fill, outline=fill, tags=tags)
    canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90,
                      style="pieslice", fill=fill, outline=fill, tags=tags)
    canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90,
                      style="pieslice", fill=fill, outline=fill, tags=tags)
    canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90,
                      style="pieslice", fill=fill, outline=fill, tags=tags)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline=fill, tags=tags)
    canvas.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline=fill, tags=tags)
    if outline and width > 0:
        canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90,
                          style="arc", outline=outline, width=width, tags=tags)
        canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90,
                          style="arc", outline=outline, width=width, tags=tags)
        canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90,
                          style="arc", outline=outline, width=width, tags=tags)
        canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90,
                          style="arc", outline=outline, width=width, tags=tags)
        canvas.create_line(x1+r, y1, x2-r, y1, fill=outline, width=width, tags=tags)
        canvas.create_line(x2, y1+r, x2, y2-r, fill=outline, width=width, tags=tags)
        canvas.create_line(x2-r, y2, x1+r, y2, fill=outline, width=width, tags=tags)
        canvas.create_line(x1, y2-r, x1, y1+r, fill=outline, width=width, tags=tags)


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


def _hex_interp(c1, c2, t):
    """Interpolate between two hex colours. t=0 -> c1, t=1 -> c2."""
    t = max(0.0, min(1.0, t))
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _rrect_pts(x1, y1, x2, y2, r, steps=10):
    """Return polygon points for a rounded rectangle."""
    pts = []
    for cx, cy, a0 in [(x2-r, y1+r, -90), (x2-r, y2-r, 0),
                       (x1+r, y2-r, 90), (x1+r, y1+r, 180)]:
        for i in range(steps + 1):
            a = math.radians(a0 + 90 * i / steps)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


# =============================================================================
# Shared modal UI helpers
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
    border=None,
) -> tk.Canvas:
    font   = tkFont.Font(family=FONT_FAMILY, size=text_size)
    width  = padx + font.measure(label) + padx
    t      = [0.0]
    anim   = [None]

    canvas = tk.Canvas(
        parent, width=width + 2, height=height + 2,
        bg=modal_bg, highlightthickness=0, bd=0, cursor=CURSOR_HAND,
    )

    def draw(fill_color):
        canvas.delete("all")
        pts = _rrect_pts(1, 1, width + 1, height + 1, radius)
        outline  = border if border is not None else fill_color
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


def _draw_modal_close_icon(cv: tk.Canvas):
    S  = MODAL_CLOSE_CANVAS_SIZE
    IS = MODAL_CLOSE_ICON_SIZE
    cx = cy = S // 2
    d  = IS // 2
    cv.create_line(cx - d, cy - d, cx + d, cy + d,
                   fill=MODAL_CLOSE_ICON_COLOR, width=MODAL_CLOSE_STROKE, capstyle="round")
    cv.create_line(cx + d, cy - d, cx - d, cy + d,
                   fill=MODAL_CLOSE_ICON_COLOR, width=MODAL_CLOSE_STROKE, capstyle="round")


def _modal_close_hover(cv: tk.Canvas, entering: bool, bg: str):
    cv.delete("all")
    if entering:
        _create_rounded_rect(cv, 0, 0, MODAL_CLOSE_CANVAS_SIZE, MODAL_CLOSE_CANVAS_SIZE,
                             MODAL_CLOSE_HOVER_RADIUS, fill=MODAL_CLOSE_HOVER_BG, outline="")
    _draw_modal_close_icon(cv)


def _make_modal_close_btn(parent: tk.Misc, on_close, bg: str = None) -> tk.Canvas:
    bg = bg or MODAL_BG
    cv = tk.Canvas(parent, width=MODAL_CLOSE_CANVAS_SIZE, height=MODAL_CLOSE_CANVAS_SIZE,
                   bg=bg, highlightthickness=0, cursor=CURSOR_HAND)
    _draw_modal_close_icon(cv)
    cv.bind("<Button-1>", lambda _e: on_close())
    cv.bind("<Enter>",    lambda _e: _modal_close_hover(cv, True, bg))
    cv.bind("<Leave>",    lambda _e: _modal_close_hover(cv, False, bg))
    return cv


def _modal_divider(parent: tk.Misc, padx: int = 24, bg: str = None):
    bg = bg or MODAL_BG
    cv = tk.Canvas(parent, height=1, bg=bg, highlightthickness=0)
    cv.pack(fill="x", padx=padx)
    cv.create_line(0, 0, 2000, 0, fill=MODAL_DIVIDER_COLOR)
    return cv


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
        self._transparent_key = "#00ff01"

        self._configure_modal_window()

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
        self._entry_fields = {}
        self.result: Optional[dict] = None
        self._close_btn: Optional[tk.Canvas] = None
        self._close_anim_id: Optional[str] = None
        self._close_hover_t = 0.0
        self._outer_canvas: Optional[tk.Canvas] = None
        self._shell_frame: Optional[tk.Frame] = None
        self._shell_window = None
        self._modal_x: Optional[int] = None
        self._modal_y: Optional[int] = None
        self._build()
        self._resize_to_content()

    _REMOVE_BTN_SIZE = 20
    _REMOVE_BTN_ICON_COLOR = "#ef4444"
    _REMOVE_BTN_STROKE = 1.35

    def _configure_modal_window(self):
        self.resizable(False, False)
        self.transient(self._parent)
        self.overrideredirect(True)
        platform = sys.platform
        if platform == "darwin":
            try:
                self.wm_attributes("-transparent", True)
                self.configure(bg="systemTransparent")
            except Exception:
                self.configure(bg=MODAL_BG)
            try:
                self.tk.call(
                    "::tk::unsupported::MacWindowStyle",
                    "style",
                    self._w,
                    "plain",
                    "noShadow",
                )
            except Exception:
                pass
            return
        self.configure(bg=self._transparent_key)
        try:
            self.wm_attributes("-transparentcolor", self._transparent_key)
        except Exception:
            pass
        if platform.startswith("win"):
            try:
                self.wm_attributes("-toolwindow", True)
            except Exception:
                pass
        else:
            try:
                self.wm_attributes("-type", "splash")
            except Exception:
                pass

    def _build(self):
        r = MODAL_RADIUS

        outer = tk.Canvas(self, highlightthickness=0, bd=0)
        try:
            outer.configure(bg="systemTransparent" if sys.platform == "darwin" else self._transparent_key)
        except Exception:
            outer.configure(bg=self._transparent_key)
        outer.pack(fill="both", expand=True)
        self._outer_canvas = outer

        def _draw_bg(event=None):
            outer.delete("modal_bg")
            if self._shell_frame is None or self._shell_window is None:
                return
            shell_w = outer.winfo_width()
            shell_h = outer.winfo_height()
            if shell_w < 4 or shell_h < 4:
                return
            _create_rounded_rect(
                outer, 0, 0, shell_w - 1, shell_h - 1, r,
                fill=MODAL_BG, outline=MODAL_BORDER, width=1, tags="modal_bg",
            )
            outer.tag_lower("modal_bg")

        shell = tk.Frame(outer, bg=MODAL_BG)
        self._shell_frame = shell
        self._shell_window = outer.create_window(r, r, window=shell, anchor="nw")

        def _on_resize(event):
            outer.itemconfigure(
                self._shell_window,
                width=max(1, event.width - 2 * r),
                height=max(1, event.height - 2 * r),
            )
            _draw_bg()

        outer.bind("<Configure>", _on_resize)

        self._drag_origin = None
        for widget in (shell,):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

        canvas_wrap = tk.Frame(shell, bg=MODAL_BG)
        canvas_wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(canvas_wrap, bg=MODAL_BG, highlightthickness=0)
        self._scrollbar = _PillScrollbar(canvas_wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)

        self._content = tk.Frame(self._canvas, bg=MODAL_BG)
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

        hero = tk.Frame(root, bg=MODAL_BG)
        hero.pack(fill="x", padx=24, pady=(24, 10))

        hero_top = tk.Frame(hero, bg=MODAL_BG)
        hero_top.pack(fill="x")

        hero_text = tk.Frame(hero_top, bg=MODAL_BG)
        hero_text.pack(side="left", fill="x", expand=True)

        tk.Label(
            hero_text,
            text=title_text,
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(anchor="w")

        tk.Label(
            hero_text,
            text=subtitle,
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
        ).pack(anchor="w", pady=(4, 0))

        close_btn = tk.Canvas(hero_top, width=MODAL_CLOSE_CANVAS_SIZE, height=MODAL_CLOSE_CANVAS_SIZE, bg=MODAL_BG,
                              highlightthickness=0, cursor=CURSOR_HAND)
        close_btn.pack(side="right", anchor="n", padx=(16, 0), pady=(2, 0))
        self._close_btn = close_btn
        self._draw_close_icon(close_btn)
        close_btn.bind("<Button-1>", lambda e: self._close())
        close_btn.bind("<Enter>", lambda e: self._animate_close_hover(True))
        close_btn.bind("<Leave>", lambda e: self._animate_close_hover(False))

        self._build_import_excel_button(hero).pack(anchor="w", pady=(12, 0))

        tk.Frame(root, bg=MODAL_DIVIDER_COLOR, height=1).pack(fill="x", pady=4)

        if self._include_project_name:
            self._build_project_name_section()

        self._dm_entries_host = self._build_dynamic_section(
            title="Add decision-maker names",
            hint=MODAL_DM_HINT,
            add_cmd=lambda: self._add_line(self._dm_entries_host, self._dm_vars, placeholder=self._next_dm_placeholder()),
        )
        for _ in range(2):
            self._add_line(self._dm_entries_host, self._dm_vars, placeholder=self._next_dm_placeholder())

        if self._fixed_policies and self._include_project_name:
            self._build_fixed_policy_section()
        elif not self._fixed_policies:
            self._policy_entries_host = self._build_dynamic_section(
                title="Add policy names",
                hint=MODAL_POLICY_HINT,
                add_cmd=lambda: self._add_line(self._policy_entries_host, self._policy_vars, placeholder=self._next_policy_placeholder()),
            )
            for _ in range(2):
                self._add_line(self._policy_entries_host, self._policy_vars, placeholder=self._next_policy_placeholder())

        btn_row = tk.Frame(root, bg=MODAL_BG)
        btn_row.pack(anchor="e", padx=24, pady=(4, 20))

        cancel_btn = self._build_footer_button(
            btn_row,
            "Cancel",
            self._close,
            bg=TOPBAR_EXCEL_BG,
            hover_bg="#d0dbe7",
            fg=TOPBAR_DELETE_TAB_FG,
            height=TOPBAR_EXCEL_HEIGHT,
            radius=TOPBAR_EXCEL_RADIUS,
            padx=TOPBAR_EXCEL_PADX,
            text_size=TOPBAR_EXCEL_TEXT_SIZE,
            border=TOPBAR_EXCEL_BORDER,
        )
        cancel_btn.pack(side="left", padx=(0, 8))

        action = "Create Project" if self._include_project_name else "Add Decision-Makers"
        ok_btn = self._build_footer_button(
            btn_row,
            action,
            self._on_ok,
            bg="#2c3b4e",
            hover_bg="#30455c",
            fg=TOPBAR_RUN_ANALYSIS_FG,
            height=TOPBAR_RUN_ANALYSIS_HEIGHT,
            radius=TOPBAR_RUN_ANALYSIS_RADIUS,
            padx=TOPBAR_RUN_ANALYSIS_PADX,
            text_size=TOPBAR_RUN_ANALYSIS_TEXT_SIZE,
        )
        ok_btn.pack(side="left")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._close())

        if self._include_project_name:
            self._project_entry.focus_set()
        elif self._first_dm_entry is not None:
            self._first_dm_entry.focus_set()

    def _build_import_excel_button(self, parent: tk.Misc) -> tk.Canvas:
        ex_bg = MODAL_ACTION_BG
        ex_hover = MODAL_ACTION_HOVER_BG
        ex_border = MODAL_ACTION_BORDER
        ex_fg = MODAL_ACTION_FG
        ex_h = MODAL_ACTION_HEIGHT
        ex_r = MODAL_ACTION_RADIUS
        ex_icon = MODAL_ACTION_ICON_SIZE
        ex_gap = MODAL_ACTION_GAP
        ex_padx = MODAL_ACTION_PADX
        ex_font = tkFont.Font(family=FONT_FAMILY, size=MODAL_ACTION_TEXT_SIZE)
        label = MODAL_ACTION_IMPORT_TEXT
        tw = ex_font.measure(label)
        width = ex_padx + ex_icon + ex_gap + tw + ex_padx
        t = [0.0]
        anim = [None]

        canvas = tk.Canvas(
            parent,
            width=width + 2,
            height=ex_h + 2,
            bg=MODAL_BG,
            highlightthickness=0,
            cursor=CURSOR_HAND,
        )

        def draw_file_icon(cnv, ox, oy, fg):
            s = ex_icon / 24.0
            lw = 1.35
            kw = dict(fill=fg, width=lw, capstyle="round", joinstyle="round")
            doc = [
                6*s+ox, 22*s+oy, 4*s+ox, 20*s+oy,
                4*s+ox, 4*s+oy, 6*s+ox, 2*s+oy,
                14*s+ox, 2*s+oy, 15.704*s+ox, 2.706*s+oy,
                19.292*s+ox, 6.294*s+oy, 20*s+ox, 8*s+oy,
                20*s+ox, 20*s+oy, 18*s+ox, 22*s+oy,
                6*s+ox, 22*s+oy,
            ]
            cnv.create_line(*doc, **kw)
            cnv.create_line(14*s+ox, 2*s+oy, 14*s+ox, 7*s+oy, 20*s+ox, 7*s+oy, **kw)
            cnv.create_line(12*s+ox, 12*s+oy, 12*s+ox, 18*s+oy, **kw)
            cnv.create_line(9*s+ox, 15*s+oy, 12*s+ox, 18*s+oy, 15*s+ox, 15*s+oy, **kw)

        def draw(bg):
            canvas.delete("all")
            pts = _rrect_pts(1, 1, width + 1, ex_h + 1, ex_r)
            canvas.create_polygon(*pts, fill=bg, outline=ex_border, width=1)
            cx = 1 + width // 2
            cy = 1 + ex_h // 2
            ix = cx - (ex_icon + ex_gap + tw) // 2
            iy = cy - ex_icon // 2
            draw_file_icon(canvas, ix, iy, ex_fg)
            canvas.create_text(ix + ex_icon + ex_gap, cy,
                               text=label, fill=ex_fg, anchor="w", font=ex_font)

        def animate(target):
            if anim[0]:
                canvas.after_cancel(anim[0])
                anim[0] = None

            def tick():
                diff = target - t[0]
                if abs(diff) < 0.02:
                    t[0] = target
                    draw(_hex_interp(ex_bg, ex_hover, target))
                    anim[0] = None
                    return
                t[0] += diff * 0.3
                draw(_hex_interp(ex_bg, ex_hover, t[0]))
                anim[0] = canvas.after(16, tick)

            tick()

        def poll():
            try:
                mx = canvas.winfo_pointerx()
                my = canvas.winfo_pointery()
                bx = canvas.winfo_rootx()
                by = canvas.winfo_rooty()
                over = bx <= mx <= bx + width and by <= my <= by + ex_h
                target = 1.0 if over else 0.0
                if abs(t[0] - target) > 0.01 and anim[0] is None:
                    animate(target)
            except tk.TclError:
                return
            canvas.after(30, poll)

        draw(ex_bg)
        canvas.bind("<Button-1>", lambda e: self._on_import_excel())
        canvas.after(100, poll)
        return canvas

    def _build_add_button(self, parent: tk.Misc, command) -> tk.Canvas:
        width = MODAL_ADD_BTN_WIDTH
        height = MODAL_ADD_BTN_HEIGHT
        radius = MODAL_ADD_BTN_RADIUS
        t = [0.0]
        anim = [None]
        canvas = tk.Canvas(
            parent,
            width=width + 2,
            height=height + 2,
            bg=MODAL_BG,
            highlightthickness=0,
            bd=0,
            cursor=CURSOR_HAND,
        )

        def draw(bg):
            canvas.delete("all")
            pts = _rrect_pts(1, 1, width + 1, height + 1, radius)
            canvas.create_polygon(*pts, fill=bg, outline=MODAL_ADD_BTN_BORDER, width=1)
            font = tkFont.Font(family=FONT_FAMILY, size=MODAL_ADD_BTN_TEXT_SIZE)
            text_w = font.measure(MODAL_ADD_BTN_TEXT)
            gap = MODAL_ADD_BTN_GAP
            group_w = MODAL_ADD_BTN_ICON_SIZE + gap + text_w
            cx = 1 + width / 2
            cy = 1 + height / 2
            half = min(MODAL_ADD_BTN_ICON_SIZE / 2, max(3, (height - 8) / 2))
            lw = MODAL_ADD_BTN_STROKE
            ix = cx - group_w / 2 + half
            canvas.create_line(ix - half, cy, ix + half, cy,
                               fill=MODAL_ADD_BTN_ICON_COLOR, width=lw, capstyle="round")
            canvas.create_line(ix, cy - half, ix, cy + half,
                               fill=MODAL_ADD_BTN_ICON_COLOR, width=lw, capstyle="round")
            canvas.create_text(ix + half + gap, cy, text=MODAL_ADD_BTN_TEXT,
                               fill=MODAL_ADD_BTN_ICON_COLOR, anchor="w", font=font)

        def animate(target):
            if anim[0]:
                canvas.after_cancel(anim[0])
                anim[0] = None

            def tick():
                diff = target - t[0]
                if abs(diff) < 0.02:
                    t[0] = target
                    draw(_hex_interp(MODAL_ADD_BTN_BG, MODAL_ADD_BTN_HOVER_BG, target))
                    anim[0] = None
                    return
                t[0] += diff * 0.3
                draw(_hex_interp(MODAL_ADD_BTN_BG, MODAL_ADD_BTN_HOVER_BG, t[0]))
                anim[0] = canvas.after(16, tick)

            tick()

        def poll():
            try:
                mx = canvas.winfo_pointerx()
                my = canvas.winfo_pointery()
                bx = canvas.winfo_rootx()
                by = canvas.winfo_rooty()
                over = bx <= mx <= bx + width and by <= my <= by + height
                target = 1.0 if over else 0.0
                if abs(t[0] - target) > 0.01 and anim[0] is None:
                    animate(target)
            except tk.TclError:
                return
            canvas.after(30, poll)

        draw(MODAL_ADD_BTN_BG)
        canvas.bind("<Button-1>", lambda e: command())
        canvas.after(100, poll)
        return canvas

    def _build_footer_button(
        self,
        parent: tk.Misc,
        label: str,
        command,
        *,
        bg: str,
        hover_bg: str,
        fg: str,
        height: int,
        radius: int,
        padx: int,
        text_size: int,
        border: Optional[str] = None,
    ) -> tk.Canvas:
        font = tkFont.Font(family=FONT_FAMILY, size=text_size)
        text_w = font.measure(label)
        width = padx + text_w + padx
        t = [0.0]
        anim = [None]
        canvas = tk.Canvas(
            parent,
            width=width + 2,
            height=height + 2,
            bg=MODAL_BG,
            highlightthickness=0,
            bd=0,
            cursor=CURSOR_HAND,
        )

        def draw(fill_color):
            canvas.delete("all")
            pts = _rrect_pts(1, 1, width + 1, height + 1, radius)
            outline = border if border is not None else fill_color
            outline_width = 1 if border is not None else 0
            canvas.create_polygon(*pts, fill=fill_color, outline=outline, width=outline_width)
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
                mx = canvas.winfo_pointerx()
                my = canvas.winfo_pointery()
                bx = canvas.winfo_rootx()
                by = canvas.winfo_rooty()
                over = bx <= mx <= bx + width and by <= my <= by + height
                target = 1.0 if over else 0.0
                if abs(t[0] - target) > 0.01 and anim[0] is None:
                    animate(target)
            except tk.TclError:
                return
            canvas.after(30, poll)

        draw(bg)
        canvas.bind("<Button-1>", lambda e: command())
        canvas.after(100, poll)
        return canvas

    def _build_remove_button(self, parent: tk.Misc, command) -> tk.Canvas:
        size = self._REMOVE_BTN_SIZE
        half = size / 2
        radius = 7
        icon_radius = 6.5
        stroke = self._REMOVE_BTN_STROKE
        color = self._REMOVE_BTN_ICON_COLOR

        canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            bg=MODAL_BG,
            highlightthickness=0,
            bd=0,
            cursor=CURSOR_HAND,
        )
        canvas.create_oval(
            half - icon_radius,
            half - icon_radius,
            half + icon_radius,
            half + icon_radius,
            outline=color,
            width=stroke,
        )
        canvas.create_line(
            half - radius / 2,
            half,
            half + radius / 2,
            half,
            fill=color,
            width=stroke,
            capstyle="round",
        )
        canvas.bind("<Button-1>", lambda e: command())
        return canvas

    def _build_project_name_section(self):
        tk.Label(
            self._content,
            text="Project Name",
            font=(FONT_FAMILY, MODAL_FIELD_LABEL_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_FIELD_LABEL_COLOR,
        ).pack(anchor="w", padx=24, pady=(10, 2))

        tk.Label(
            self._content,
            text=MODAL_PROJECT_HINT,
            font=(FONT_FAMILY, MODAL_SECTION_HINT_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_SECTION_HINT_COLOR,
        ).pack(anchor="w", padx=24, pady=(0, MODAL_SECTION_ROW_GAP))

        field_wrap, entry = self._create_rounded_entry(self._content, self._project_var, MODAL_FIELD_PLACEHOLDER)
        field_wrap.pack(fill="x", padx=24, pady=(0, 14))
        self._project_entry = entry
        self._set_placeholder(entry, MODAL_FIELD_PLACEHOLDER)
        self._pack_section_divider(self._content)

    def _pack_section_divider(self, parent: tk.Misc):
        tk.Frame(parent, bg=MODAL_DIVIDER_COLOR, height=1).pack(fill="x", pady=(0, 8))

    def _alpha_index(self, index: int) -> str:
        letters = []
        while index > 0:
            index -= 1
            letters.append(chr(ord("A") + (index % 26)))
            index //= 26
        return "".join(reversed(letters)) or "A"

    def _next_dm_placeholder(self) -> str:
        return f"e.g. Expert {self._alpha_index(len(self._dm_vars) + 1)}"

    def _next_policy_placeholder(self) -> str:
        return f"e.g. Policy {len(self._policy_vars) + 1}"

    def _create_rounded_entry(self, parent: tk.Misc, var: tk.StringVar, placeholder: str, state: str = "normal"):
        field_wrap = tk.Canvas(
            parent,
            height=MODAL_FIELD_HEIGHT + 2,
            bg=MODAL_BG,
            highlightthickness=0,
            bd=0,
        )
        entry = tk.Entry(
            field_wrap,
            textvariable=var,
            font=(FONT_FAMILY, MODAL_FIELD_TEXT_SIZE, "normal"),
            bg=MODAL_FIELD_BG,
            fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            state=state,
        )
        entry_window = field_wrap.create_window(14, (MODAL_FIELD_HEIGHT + 2) // 2, window=entry, anchor="w")

        def _resize_field(event):
            field_wrap.delete("field_bg")
            width = max(2, event.width)
            pts = _rrect_pts(1, 1, width - 1, MODAL_FIELD_HEIGHT + 1, MODAL_FIELD_RADIUS)
            field_wrap.create_polygon(*pts, fill=MODAL_FIELD_BG, outline=MODAL_FIELD_BORDER, width=1, tags="field_bg")
            field_wrap.tag_lower("field_bg")
            field_wrap.coords(entry_window, 14, (MODAL_FIELD_HEIGHT + 2) // 2)
            field_wrap.itemconfigure(entry_window, width=max(1, width - 28))

        field_wrap.bind("<Configure>", _resize_field)
        self._entry_fields[entry] = {"var": var, "placeholder": placeholder, "active": False, "state": state}
        if state == "normal":
            self._set_placeholder(entry, placeholder)
            entry.bind("<FocusIn>", lambda e, ent=entry: self._on_entry_focus_in(ent))
            entry.bind("<FocusOut>", lambda e, ent=entry: self._on_entry_focus_out(ent))
        return field_wrap, entry

    def _build_dynamic_section(self, title: str, hint: str, add_cmd, top_pady: int = 6):
        wrap = tk.Frame(self._content, bg=MODAL_BG)
        wrap.pack(fill="x", padx=24, pady=(top_pady, 0))

        head = tk.Frame(wrap, bg=MODAL_BG)
        head.pack(fill="x")
        head_text = tk.Frame(head, bg=MODAL_BG)
        head_text.pack(side="left", fill="x", expand=True)
        tk.Label(
            head_text,
            text=title,
            font=(FONT_FAMILY, MODAL_SECTION_TITLE_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_SECTION_TITLE_COLOR,
        ).pack(anchor="w")

        tk.Label(
            head_text,
            text=hint,
            font=(FONT_FAMILY, MODAL_SECTION_HINT_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_SECTION_HINT_COLOR,
        ).pack(anchor="w", pady=(2, 0))

        self._build_add_button(head, add_cmd).pack(side="right", padx=(12, 0), pady=(0, 2))

        host = tk.Frame(wrap, bg=MODAL_BG)
        host.pack(fill="x", pady=(MODAL_SECTION_ROW_GAP, 8))
        self._section_entries[host] = []
        self._pack_section_divider(wrap)
        return host

    def _build_fixed_policy_section(self):
        wrap = tk.Frame(self._content, bg=MODAL_BG)
        wrap.pack(fill="x", padx=24, pady=(8, 0))

        head = tk.Frame(wrap, bg=MODAL_BG)
        head.pack(fill="x")

        head_text = tk.Frame(head, bg=MODAL_BG)
        head_text.pack(side="left", fill="x", expand=True)

        tk.Label(
            head_text,
            text="Add policy names",
            font=(FONT_FAMILY, MODAL_SECTION_TITLE_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_SECTION_TITLE_COLOR,
        ).pack(anchor="w")
        tk.Label(
            head_text,
            text="Policies are inherited from the current project.",
            font=(FONT_FAMILY, MODAL_SECTION_HINT_SIZE, "normal"),
            bg=MODAL_BG, fg=MODAL_SECTION_HINT_COLOR,
        ).pack(anchor="w", pady=(2, 0))

        host = tk.Frame(wrap, bg=MODAL_BG)
        host.pack(fill="x", pady=(MODAL_SECTION_ROW_GAP, 8))
        self._section_entries[host] = []
        for policy in self._fixed_policies:
            var = tk.StringVar(value=policy)
            self._policy_vars.append(var)
            self._add_line(host, self._policy_vars, default=policy, state="disabled", append_var=False)
        self._pack_section_divider(wrap)

    def _add_line(
        self,
        parent: tk.Frame,
        vars_list: List[tk.StringVar],
        default: str = "",
        state: str = "normal",
        append_var: bool = True,
        placeholder: str = "",
    ):
        var = tk.StringVar(value=default)
        if append_var:
            vars_list.append(var)
        row_wrap = tk.Frame(parent, bg=MODAL_BG)
        row_wrap.grid_columnconfigure(0, weight=1)

        field_wrap, entry = self._create_rounded_entry(row_wrap, var, placeholder, state=state)
        field_wrap.pack(side="left", fill="x", expand=True)

        remove_btn = None
        if state == "normal" and append_var:
            remove_btn = self._build_remove_button(
                row_wrap,
                lambda rw=row_wrap, host=parent: self._remove_line(host, rw),
            )
            row_wrap._remove_btn = remove_btn
            row_wrap._var = var
            row_wrap._vars_list = vars_list
            row_wrap._entry = entry
            row_wrap._removable = True
        else:
            row_wrap._remove_btn = None
            row_wrap._var = var
            row_wrap._vars_list = vars_list
            row_wrap._entry = entry
            row_wrap._removable = False

        self._section_entries[parent].append(row_wrap)
        self._relayout_section(parent)
        if state == "normal" and self._first_dm_entry is None:
            self._first_dm_entry = entry
        self.after_idle(self._resize_to_content)
        return entry

    def _remove_line(self, parent: tk.Frame, row_wrap: tk.Frame):
        entries = self._section_entries.get(parent, [])
        if row_wrap not in entries:
            return
        entries.remove(row_wrap)
        var = getattr(row_wrap, "_var", None)
        vars_list = getattr(row_wrap, "_vars_list", None)
        entry = getattr(row_wrap, "_entry", None)
        if vars_list is not None and var in vars_list:
            vars_list.remove(var)
        if entry in self._entry_fields:
            del self._entry_fields[entry]
        row_wrap.destroy()
        self._relayout_section(parent)
        if self._first_dm_entry is entry:
            self._first_dm_entry = None
            for meta_entry, meta in self._entry_fields.items():
                if meta.get("state") == "normal":
                    self._first_dm_entry = meta_entry
                    break
        self.after_idle(self._resize_to_content)

    def _update_remove_buttons(self, parent: tk.Frame):
        for idx, row_wrap in enumerate(self._section_entries.get(parent, [])):
            btn = getattr(row_wrap, "_remove_btn", None)
            if btn is None:
                continue
            removable = idx >= 2 and getattr(row_wrap, "_removable", False)
            if removable:
                if not btn.winfo_ismapped():
                    btn.pack(side="left", padx=(8, 0))
            elif btn.winfo_ismapped():
                btn.pack_forget()

    def _relayout_section(self, parent: tk.Frame):
        entries = self._section_entries.get(parent, [])
        count = len(entries)
        if not entries:
            return

        self._update_remove_buttons(parent)

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
        project_name = self._get_project_name() if self._include_project_name else None
        dm_names = [self._value_from_var(var) for var in self._dm_vars]
        dm_names = [name for name in dm_names if name]
        policies = self._fixed_policies or [self._value_from_var(var) for var in self._policy_vars]
        if not self._fixed_policies:
            policies = [name for name in policies if name]

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
        if self._shell_frame is not None:
            parent = self._parent
            parent.update_idletasks()
            req_w = self._shell_frame.winfo_reqwidth() + 2 * MODAL_RADIUS
            req_h = self._shell_frame.winfo_reqheight() + 2 * MODAL_RADIUS
            parent_w = max(1, parent.winfo_width())
            parent_h = max(1, parent.winfo_height())
            target_modal_h = 665 if self._include_project_name else 400
            modal_w = min(max(860, req_w + 40), max(320, parent_w - 80))
            modal_h = min(max(target_modal_h, req_h + 20), target_modal_h, max(240, parent_h - 80))
            if self._modal_x is None:
                self._modal_x = parent.winfo_rootx() + max(24, (parent_w - modal_w) // 2)
            if self._modal_y is None:
                self._modal_y = parent.winfo_rooty() + max(24, (parent_h - modal_h) // 2)
            max_x = parent.winfo_rootx() + max(24, parent_w - modal_w - 24)
            max_y = parent.winfo_rooty() + max(24, parent_h - modal_h - 24)
            min_x = parent.winfo_rootx() + 24
            min_y = parent.winfo_rooty() + 24
            self._modal_x = min(max(min_x, self._modal_x), max_x)
            self._modal_y = min(max(min_y, self._modal_y), max_y)
            self.geometry(f"{modal_w}x{modal_h}+{self._modal_x}+{self._modal_y}")
        self.lift()
        self.after_idle(self._update_scrollbar_visibility)

    def _draw_close_icon(self, canvas: tk.Canvas):
        canvas.delete("all")
        size = MODAL_CLOSE_CANVAS_SIZE
        cx = size / 2
        cy = size / 2
        fill = _hex_interp(MODAL_BG, MODAL_CLOSE_HOVER_BG, self._close_hover_t)
        r = MODAL_CLOSE_HOVER_RADIUS
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline=fill, width=0)
        half = MODAL_CLOSE_ICON_SIZE / 2
        stroke = MODAL_CLOSE_ICON_COLOR
        lw = MODAL_CLOSE_STROKE
        canvas.create_line(cx + half, cy - half, cx - half, cy + half, fill=stroke, width=lw, capstyle="round")
        canvas.create_line(cx - half, cy - half, cx + half, cy + half, fill=stroke, width=lw, capstyle="round")

    def _animate_close_hover(self, entering: bool):
        """Animate the close button background on hover/leave."""
        if self._close_anim_id is not None:
            try:
                self.after_cancel(self._close_anim_id)
            except Exception:
                pass
            self._close_anim_id = None
        start = self._close_hover_t
        target = 1.0 if entering else 0.0
        self._run_close_anim(start, target, step=0, total=8)

    def _run_close_anim(self, start_t: float, target_t: float, step: int, total: int):
        if self._close_btn is None:
            return
        self._close_hover_t = start_t + (target_t - start_t) * (step / total)
        try:
            self._draw_close_icon(self._close_btn)
        except Exception:
            return
        if step < total:
            self._close_anim_id = self.after(
                20, lambda: self._run_close_anim(start_t, target_t, step + 1, total)
            )

    def _get_project_name(self) -> str:
        return self._entry_value(self._project_entry)

    def _set_placeholder(self, entry: tk.Entry, placeholder: str):
        meta = self._entry_fields[entry]
        meta["active"] = True
        meta["var"].set(placeholder)
        entry.configure(
            fg=MODAL_FIELD_PLACEHOLDER_COLOR,
            font=(FONT_FAMILY, MODAL_FIELD_PLACEHOLDER_SIZE, "normal"),
        )

    def _clear_placeholder(self, entry: tk.Entry):
        meta = self._entry_fields[entry]
        if not meta["active"]:
            return
        meta["active"] = False
        meta["var"].set("")
        entry.configure(
            fg=COLOR_TEXT,
            font=(FONT_FAMILY, MODAL_FIELD_TEXT_SIZE, "normal"),
        )

    def _on_entry_focus_in(self, entry: tk.Entry):
        meta = self._entry_fields[entry]
        if meta["active"]:
            self._clear_placeholder(entry)

    def _on_entry_focus_out(self, entry: tk.Entry):
        meta = self._entry_fields[entry]
        if not meta["var"].get().strip():
            self._set_placeholder(entry, meta["placeholder"])

    def _entry_value(self, entry: tk.Entry) -> str:
        meta = self._entry_fields.get(entry)
        if meta and meta["active"]:
            return ""
        return entry.get().strip()

    def _value_from_var(self, var: tk.StringVar) -> str:
        for entry, meta in self._entry_fields.items():
            if meta["var"] is var:
                return self._entry_value(entry)
        return var.get().strip()

    def _start_drag(self, event):
        self._drag_origin = (event.x_root, event.y_root, self.winfo_x(), self.winfo_y())

    def _on_drag(self, event):
        if not self._drag_origin or self._shell_frame is None:
            return
        start_x, start_y, modal_x, modal_y = self._drag_origin
        dx = event.x_root - start_x
        dy = event.y_root - start_y
        self._modal_x = modal_x + dx
        self._modal_y = modal_y + dy
        self._resize_to_content()

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
        needs_scroll = self._content.winfo_reqheight() > self._canvas.winfo_height()
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

    _PADX = 24

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("Add Decision-Maker Matrix")
        self.configure(bg=MODAL_BG)
        self.resizable(True, True)
        self.grab_set()

        self.result: Optional[Tuple[str, List[str]]] = None

        self._build()
        self._center()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        PX = self._PADX

        # Header
        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))
        tk.Label(
            hdr, text="New Policy Coherence Matrix",
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")
        _make_modal_close_btn(hdr, self.destroy).pack(side="right")

        tk.Label(
            self,
            text="Enter the decision-maker and the policies to include in the matrix.",
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
            wraplength=460, justify="left",
        ).pack(anchor="w", padx=PX, pady=(4, 10))

        _modal_divider(self, PX)

        # Decision-maker name
        tk.Label(
            self, text="Decision-Maker Name",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(anchor="w", padx=PX, pady=(12, 4))

        self._dm_var = tk.StringVar()
        self._dm_entry = tk.Entry(
            self, textvariable=self._dm_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=MODAL_FIELD_BG, fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            highlightthickness=1,
            highlightbackground=MODAL_FIELD_BORDER,
            highlightcolor=COLOR_ACCENT,
            width=44,
        )
        self._dm_entry.pack(anchor="w", padx=PX, pady=(0, 14))
        self._dm_entry.focus_set()

        # Policy names
        tk.Label(
            self, text="Policy Names  (one per line, minimum 2)",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(anchor="w", padx=PX, pady=(0, 4))

        text_frame = tk.Frame(self, bg=MODAL_BG)
        text_frame.pack(fill="both", expand=True, padx=PX, pady=(0, 4))

        self._policy_text = tk.Text(
            text_frame,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=MODAL_FIELD_BG, fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            highlightthickness=1,
            highlightbackground=MODAL_FIELD_BORDER,
            highlightcolor=COLOR_ACCENT,
            width=50, height=10,
            wrap="word",
        )
        sb = ttk.Scrollbar(text_frame, command=self._policy_text.yview)
        self._policy_text.configure(yscrollcommand=sb.set)
        self._policy_text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        tk.Label(
            self,
            text="Policies will be coded automatically: P1, P2, P3 ...",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
        ).pack(anchor="w", padx=PX, pady=(2, 6))

        # Import button
        _make_canvas_button(
            self, "  Import from XLSX / CSV", self._import_file,
            bg=COLOR_BUTTON, hover_bg="#1a3550", fg="#ffffff",
            height=30, radius=5, padx=14, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG,
        ).pack(anchor="w", padx=PX, pady=(0, 14))

        _modal_divider(self, PX)

        # OK / Cancel row
        btn_row = tk.Frame(self, bg=MODAL_BG)
        btn_row.pack(anchor="e", padx=PX, pady=(10, 20))

        _make_canvas_button(
            btn_row, "Cancel", self.destroy,
            bg="#f5f7fa", hover_bg="#eaeef4", fg=MODAL_SECTION_TITLE_COLOR,
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG, border="#e6e6e6",
        ).pack(side="left", padx=(0, 8))
        _make_canvas_button(
            btn_row, "Create Matrix", self._on_ok,
            bg=COLOR_BUTTON, hover_bg="#1a3550", fg="#ffffff",
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG,
        ).pack(side="left")

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

    _W    = 380
    _PADX = 24

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        label: str,
        default: str = "",
    ):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=MODAL_BG)
        self.resizable(False, False)
        self.grab_set()

        self.result: Optional[str] = None
        self._title_text = title
        self._label_text = label
        self._default    = default

        self._build()

    def _build(self):
        W, PX = self._W, self._PADX

        # Header
        hdr = tk.Frame(self, bg=MODAL_BG)
        hdr.pack(fill="x", padx=PX, pady=(20, 0))
        tk.Label(
            hdr, text=self._title_text,
            font=(FONT_FAMILY, MODAL_TITLE_SIZE, "bold"),
            bg=MODAL_BG, fg=MODAL_TITLE_COLOR,
        ).pack(side="left")
        _make_modal_close_btn(hdr, self.destroy).pack(side="right")

        # Subtitle / field label
        tk.Label(
            self, text=self._label_text,
            font=(FONT_FAMILY, MODAL_SUBTITLE_SIZE),
            bg=MODAL_BG, fg=MODAL_SUBTITLE_COLOR,
        ).pack(anchor="w", padx=PX, pady=(10, 4))

        # Entry
        self._var = tk.StringVar(value=self._default)
        entry = tk.Entry(
            self, textvariable=self._var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=MODAL_FIELD_BG, fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1,
            highlightthickness=1,
            highlightbackground=MODAL_FIELD_BORDER,
            highlightcolor=COLOR_ACCENT,
            width=34,
        )
        entry.pack(anchor="w", padx=PX, pady=(0, 16))
        entry.select_range(0, "end")
        entry.focus_set()

        _modal_divider(self, PX)

        # Buttons
        btn_row = tk.Frame(self, bg=MODAL_BG)
        btn_row.pack(anchor="e", padx=PX, pady=(10, 20))
        _make_canvas_button(
            btn_row, "Cancel", self.destroy,
            bg="#f5f7fa", hover_bg="#eaeef4", fg=MODAL_SECTION_TITLE_COLOR,
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG, border="#e6e6e6",
        ).pack(side="left", padx=(0, 8))
        _make_canvas_button(
            btn_row, "OK", self._on_ok,
            bg=COLOR_BUTTON, hover_bg="#1a3550", fg="#ffffff",
            height=33, radius=5, padx=18, text_size=FONT_SIZE_NORMAL,
            modal_bg=MODAL_BG,
        ).pack(side="left")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        w = max(self.winfo_reqwidth(), W)
        h = self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
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
