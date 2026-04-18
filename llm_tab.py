# =============================================================================
# Policy Coherence Kit -- llm_tab.py
# LLMInterpretationTab: LLM-powered structured interpretation of analysis.
#
# - User selects provider, model, enters API key (never saved)
# - Clicking "Generate Interpretation" assembles a structured prompt from
#   all analysis results and calls the selected LLM API
# - Response is displayed in a structured scrollable text area
# - Downloadable as .txt or .pdf
# =============================================================================

import math
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional

from aggregator import AggregationResult
from coherence_scores_tab import compute_scores
from range_of_influence_tab import compute_entropy
from network_tab import compute_centrality
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE, FONT_SIZE_PAGE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_PAGE_TITLE,
    COLOR_BUTTON, COLOR_BUTTON_FG,
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


def _rrect_pts(x1, y1, x2, y2, r, steps=10):
    pts = []
    for cx, cy, a0 in [
        (x2-r, y1+r, -90),
        (x2-r, y2-r, 0),
        (x1+r, y2-r, 90),
        (x1+r, y1+r, 180),
    ]:
        for i in range(steps + 1):
            a = math.radians(a0 + 90 * i / steps)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts

# =============================================================================
# Engine / model registry
# =============================================================================

ENGINES = {
    "Groq": {
        "models": [
            "llama-3.3-70b-versatile",
        ],
        "base_url": "https://api.groq.com/openai/v1",
        "style": "openai_compat",
    },
    "OpenAI": {
        "models": [
            "gpt-4o-mini",
            "gpt-4o",
        ],
        "base_url": "https://api.openai.com/v1",
        "style": "openai_compat",
    },
}

SYSTEM_PROMPT = (
    "You are an expert policy analyst specialising in policy coherence and "
    "systems thinking. You provide rigorous, evidence-based, in-depth "
    "interpretations of policy interaction analyses. Your responses are "
    "structured, analytical, and written for policy professionals."
)

SECTION_HEADERS = [
    "1. Overall Coherence Assessment",
    "2. Key Synergies",
    "3. Key Conflicts",
    "4. Influential Policies",
    "5. Range of Influence",
    "6. Network Structure",
    "7. Strategic Recommendations",
]


# =============================================================================
# Prompt builder
# =============================================================================

def build_prompt(result: AggregationResult) -> str:
    n       = result.n
    codes   = result.codes
    policies = result.policies
    method_label = {
        "average":  "Average",
        "majority": "Majority Rule",
        "weighted": "Weighted",
    }.get(result.method, result.method.title())

    lines = []

    # ── Header ───────────────────────────────────────────────────────
    lines.append(
        f"You are given the results of a policy coherence analysis for "
        f"{n} policies, aggregated using the {method_label} method.\n"
    )

    # ── Policy list ──────────────────────────────────────────────────
    lines.append("POLICY LIST:")
    for code, name in zip(codes, policies):
        lines.append(f"  {code}: {name}")
    lines.append("")

    # ── Aggregated matrix ────────────────────────────────────────────
    lines.append(
        "AGGREGATED SCORE MATRIX "
        "(rows = influencing policy, columns = influenced policy, "
        "scale: -3=Cancelling to +3=Indivisible, 0=diagonal):"
    )
    header = "         " + "  ".join(f"{c:>6}" for c in codes)
    lines.append(header)
    for i in range(n):
        row_vals = []
        for j in range(n):
            s = result.scores.get((i, j), 0.0) or 0.0
            row_vals.append(f"{s:>6.2f}")
        lines.append(f"  {codes[i]:>5}  " + "  ".join(row_vals))
    lines.append("")

    # ── Coherence scores ─────────────────────────────────────────────
    lines.append(
        "COHERENCE SCORES "
        "(OI=Outgoing Influence count, II=Incoming Influence count, "
        "WOI=Weighted Outgoing, WII=Weighted Incoming):"
    )
    lines.append(
        f"  {'Code':<6} {'OI':>4} {'II':>4} {'WOI':>7} {'WII':>7}  Policy"
    )
    for row in compute_scores(result):
        lines.append(
            f"  {row['code']:<6} {row['oi']:>4} {row['ii']:>4} "
            f"{row['woi']:>7.2f} {row['wii']:>7.2f}  {row['policy']}"
        )
    lines.append("")

    # ── Range of influence ───────────────────────────────────────────
    lines.append(
        "RANGE OF INFLUENCE — SHANNON ENTROPY "
        "(0=concentrated on one policy, higher=distributed; "
        "categories based on fraction of max entropy):"
    )
    lines.append(f"  {'Code':<6} {'Entropy':>8}  {'Category':<14}  Policy")
    for row in compute_entropy(result):
        lines.append(
            f"  {row['code']:<6} {row['entropy']:>8.4f}  "
            f"{row['category']:<14}  {row['policy']}"
        )
    lines.append("")

    # ── Network centrality ───────────────────────────────────────────
    lines.append(
        "NETWORK CENTRALITY "
        "(Betweenness: broker role 0-1; "
        "Closeness: reachability, higher=more central):"
    )
    lines.append(f"  {'Code':<6} {'Betweenness':>12} {'Closeness':>10}  Policy")
    for row in sorted(compute_centrality(result),
                      key=lambda r: r["betweenness"], reverse=True):
        lines.append(
            f"  {row['code']:<6} {row['betweenness']:>12.4f} "
            f"{row['closeness']:>10.4f}  {row['policy']}"
        )
    lines.append("")

    # ── Instruction ──────────────────────────────────────────────────
    lines.append(
        "Please provide a structured, in-depth interpretation with the "
        "following sections. Each section should be multiple paragraphs "
        "with specific references to the data above:\n"
    )
    for header in SECTION_HEADERS:
        lines.append(f"## {header}")
    lines.append(
        "\nEnsure your interpretation is analytical, references specific "
        "policies by name and code, and provides actionable insights for "
        "policy professionals."
    )

    return "\n".join(lines)


# =============================================================================
# API callers
# =============================================================================

def _http_post(url: str, payload: dict, headers: dict) -> dict:
    """
    Shared HTTP POST helper with clear error messages.
    Raises RuntimeError with the full API error body on failure.
    """
    import urllib.request, urllib.error, json
    data = json.dumps(payload).encode()
    # Merge in a browser-like User-Agent so Cloudflare doesn't block us
    full_headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PolicyCoherenceKit/1.0)",
        "Accept": "application/json",
    }
    full_headers.update(headers)
    req  = urllib.request.Request(
        url, data=data, headers=full_headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(body)
            msg = (err.get("error", {}).get("message")
                   or err.get("message")
                   or body)
        except Exception:
            msg = body
        raise RuntimeError(
            f"HTTP {e.code} from API:\n\n{msg}"
        )
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def _call_openai_compat(base_url: str, api_key: str, model: str,
                         system: str, user: str) -> str:
    data = _http_post(
        url=f"{base_url}/chat/completions",
        payload={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "max_tokens": 4096,
            "temperature": 0.3,
        },
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected response structure:\n{data}")


def call_llm(engine: str, model: str, api_key: str, prompt: str) -> str:
    """Dispatch to the correct API based on engine."""
    if not api_key.strip():
        raise RuntimeError("API key is empty. Please enter a valid API key.")
    cfg   = ENGINES[engine]
    style = cfg["style"]
    if style == "openai_compat":
        return _call_openai_compat(
            cfg["base_url"], api_key, model, SYSTEM_PROMPT, prompt)
    raise ValueError(f"Unknown engine style: {style}")


# =============================================================================
# LLMInterpretationTab
# =============================================================================

class LLMInterpretationTab(tk.Frame):

    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result      = result
        self._response    = ""
        self._running     = False
        self._api_key_var = tk.StringVar()
        self._engine_var  = tk.StringVar(value=list(ENGINES.keys())[0])
        self._model_var   = tk.StringVar()
        self._selector_popup = None
        self._selector_close_fn = None
        self._model_options = []
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        self._build_config_panel()
        self._build_output_area()
        self._build_action_bar()
        self._update_models()

    # ------------------------------------------------------------------

    def _build_info_bar(self):
        bar = tk.Frame(self, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")
        content = tk.Frame(bar, bg=COLOR_BG)
        content.pack(anchor="w", padx=16)

        method_label = {
            "average":  "Average",
            "majority": "Majority Rule",
            "weighted": "Weighted",
        }.get(self._result.method, self._result.method.title())

        tk.Label(
            content,
            text=f"LLM Interpretation  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_PAGE_TITLE, "normal"),
            bg=COLOR_BG, fg=COLOR_PAGE_TITLE,
        ).pack(side="left")

        tk.Label(
            content,
            text="API key is used once and never stored.",
            font=(FONT_FAMILY, 11, "italic"),
            bg=COLOR_BG, fg="#a3a3a3",
        ).pack(side="left", padx=(18, 0))

    # ------------------------------------------------------------------

    def _build_config_panel(self):
        panel = tk.Frame(self, bg=COLOR_BG)
        panel.pack(fill="x", padx=16, pady=8)
        top_row = tk.Frame(panel, bg=COLOR_BG)
        top_row.pack(anchor="w")

        engine_group = tk.Frame(top_row, bg=COLOR_BG)
        engine_group.pack(side="left", padx=(0, 36))
        tk.Label(engine_group, text="Engine:",
                 font=(FONT_FAMILY, 10, "normal"),
                 bg=COLOR_BG, fg="#30455c", anchor="w",
                 ).pack(side="left", padx=(0, 4))

        self._engine_selector = self._build_selector_field(
            engine_group,
            variable=self._engine_var,
            options=list(ENGINES.keys()),
            width=180,
            on_pick=lambda _value: self._update_models(),
        )
        self._engine_selector.pack(side="left")

        model_group = tk.Frame(top_row, bg=COLOR_BG)
        model_group.pack(side="left")
        tk.Label(model_group, text="Model:",
                 font=(FONT_FAMILY, 10, "normal"),
                 bg=COLOR_BG, fg="#30455c", anchor="w",
                 ).pack(side="left", padx=(0, 4))

        self._model_selector = self._build_selector_field(
            model_group,
            variable=self._model_var,
            options=[],
            width=280,
            on_pick=lambda _value: None,
        )
        self._model_selector.pack(side="left")

        # API Key
        api_row = tk.Frame(panel, bg=COLOR_BG)
        api_row.pack(anchor="w", pady=(8, 0))
        tk.Label(api_row, text="API Key:",
                 font=(FONT_FAMILY, 10, "normal"),
                 bg=COLOR_BG, fg="#30455c", anchor="w",
                 ).pack(side="left", padx=(0, 4))

        key_wrap = tk.Canvas(
            api_row,
            width=540,
            height=36,
            bg=COLOR_BG,
            highlightthickness=0,
        )
        key_wrap.pack(side="left", padx=(0, 10))
        self._draw_input_shell(key_wrap, width=540, height=36)

        key_entry = tk.Entry(
            panel, textvariable=self._api_key_var,
            show="•",
            font=(FONT_FAMILY, 10),
            bg="#ffffff", fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="flat", bd=0, width=52,
            highlightthickness=0,
            highlightbackground="#ffffff",
            highlightcolor="#ffffff",
            insertwidth=1,
        )
        key_wrap.create_window(14, 18, window=key_entry, anchor="w", width=512, height=20)

        # Show/hide toggle
        self._show_key = tk.BooleanVar(value=False)

        def _toggle_key():
            key_entry.config(show="" if self._show_key.get() else "•")

        show_key_wrap = tk.Frame(api_row, bg=COLOR_BG)
        show_key_wrap.pack(side="left")
        tk.Checkbutton(
            show_key_wrap, text="Show key",
            variable=self._show_key,
            command=_toggle_key,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, activebackground=COLOR_BG,
            cursor=CURSOR_HAND,
        ).pack(side="right")

    # ------------------------------------------------------------------

    def _update_models(self):
        engine = self._engine_var.get()
        models = ENGINES[engine]["models"]
        self._model_options = models
        if hasattr(self, "_model_selector"):
            self._model_selector._selector_options = models
        self._model_var.set(models[0])

    def _draw_input_shell(self, canvas: tk.Canvas, width: int, height: int, active: bool = False, radius: int = 4):
        canvas.delete("all")
        outline = "#426387" if active else "#e6e6e6"
        pts = _rrect_pts(1, 1, width - 1, height - 1, radius)
        canvas.create_polygon(*pts, fill="#ffffff", outline=outline, width=1)

    def _build_selector_field(self, parent: tk.Misc, variable: tk.StringVar, options, width: int, on_pick):
        field = tk.Canvas(
            parent,
            width=width,
            height=36,
            bg=COLOR_BG,
            highlightthickness=0,
            cursor=CURSOR_HAND,
        )
        field._selector_options = options
        field._selector_on_pick = on_pick
        self._draw_selector_field(field, variable.get(), active=False)

        def _open(_event=None):
            self._open_selector_popup(field, variable)
            return "break"

        field.bind("<Button-1>", _open)
        variable.trace_add("write", lambda *_args, c=field, v=variable: self._draw_selector_field(c, v.get(), active=False))
        return field

    def _draw_selector_field(self, canvas: tk.Canvas, text: str, active: bool):
        width = int(canvas.cget("width"))
        height = int(canvas.cget("height"))
        self._draw_input_shell(canvas, width, height, active=active)
        canvas.create_text(
            10, height / 2,
            text=text,
            font=(FONT_FAMILY, 10),
            fill=COLOR_TEXT,
            anchor="w",
        )
        cx = width - 14
        cy = height / 2
        canvas.create_line(cx - 4, cy - 2, cx, cy + 2, fill="#a3a3a3", width=1.35, capstyle="round", joinstyle="round")
        canvas.create_line(cx, cy + 2, cx + 4, cy - 2, fill="#a3a3a3", width=1.35, capstyle="round", joinstyle="round")

    def _open_selector_popup(self, field: tk.Canvas, variable: tk.StringVar):
        if self._selector_popup is not None:
            self._close_selector_popup()

        options = list(getattr(field, "_selector_options", []))
        if not options:
            return

        width = int(field.cget("width"))
        item_h = 36
        pad = 1
        visible = min(8, len(options))
        popup_h = visible * item_h + pad * 2
        field_x = field.winfo_rootx()
        field_y = field.winfo_rooty()
        field_h = field.winfo_height()
        popup_y = field_y + field_h + 4
        if popup_y + popup_h > self.winfo_screenheight() - 20:
            popup_y = field_y - popup_h - 4

        self._draw_selector_field(field, variable.get(), active=True)

        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True)
        popup.configure(bg="#e6e6e6")
        popup.wm_geometry(f"{width}x{popup_h}+{field_x}+{popup_y}")

        shell = tk.Frame(popup, bg="#e6e6e6")
        shell.place(x=0, y=0, relwidth=1, relheight=1)
        canvas = tk.Canvas(shell, bg="#ffffff", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True, padx=(pad, 0), pady=pad)
        inner = tk.Frame(canvas, bg="#ffffff")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))

        for idx, option in enumerate(options):
            item = tk.Label(
                inner,
                text=option,
                bg="#ffffff",
                fg=COLOR_TEXT,
                font=(FONT_FAMILY, 10),
                anchor="w",
                padx=12,
            )
            item.place(x=0, y=idx * item_h, relwidth=1, height=item_h)

            item.bind("<Enter>", lambda _e, w=item: w.configure(bg="#f0f4f8"))
            item.bind("<Leave>", lambda _e, w=item: w.configure(bg="#ffffff"))
            item.bind("<Button-1>", lambda _e, value=option, f=field: self._select_popup_value(f, variable, value))

        inner.configure(height=len(options) * item_h)

        root = self.winfo_toplevel()
        bind_id = [None]

        def _close(_event=None):
            if bind_id[0]:
                root.unbind("<Button-1>", bind_id[0])
                bind_id[0] = None
            self._draw_selector_field(field, variable.get(), active=False)
            try:
                popup.destroy()
            except Exception:
                pass
            self._selector_popup = None
            self._selector_close_fn = None

        self._selector_popup = popup
        self._selector_close_fn = _close
        bind_id[0] = root.bind("<Button-1>", lambda _e: _close(), "+")
        popup.bind("<Escape>", _close)

    def _select_popup_value(self, field: tk.Canvas, variable: tk.StringVar, value: str):
        variable.set(value)
        on_pick = getattr(field, "_selector_on_pick", None)
        if on_pick:
            on_pick(value)
        self._close_selector_popup()

    def _close_selector_popup(self):
        if self._selector_close_fn is not None:
            self._selector_close_fn()

    # ------------------------------------------------------------------

    def _build_output_area(self):
        out_frame = tk.Frame(self, bg=COLOR_BG)
        out_frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        tk.Label(
            out_frame,
            text="Interpretation:",
            font=(FONT_FAMILY, 10, "normal"),
            bg=COLOR_BG, fg="#30455c",
        ).pack(anchor="w", pady=(0, 4))

        text_frame = tk.Frame(out_frame, bg=COLOR_BG)
        text_frame.pack(fill="both", expand=True)

        text_shell = tk.Canvas(
            text_frame,
            bg=COLOR_BG,
            highlightthickness=0,
        )
        text_shell.pack(fill="both", expand=True)

        self._output_text = tk.Text(
            text_shell,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff", fg=COLOR_TEXT,
            relief="flat", bd=0,
            wrap="word",
            state="disabled",
            insertbackground=COLOR_ACCENT,
            padx=12, pady=10,
            highlightthickness=0,
        )
        text_window = text_shell.create_window((12, 12), window=self._output_text, anchor="nw")

        def _draw_output_shell():
            width = text_shell.winfo_width()
            height = text_shell.winfo_height()
            if width <= 1 or height <= 1:
                return
            text_shell.delete("shell_bg")
            pts = _rrect_pts(1, 1, width - 1, height - 1, 6)
            bg_id = text_shell.create_polygon(
                *pts,
                fill="#ffffff",
                outline="#e6e6e6",
                width=1,
                tags=("shell_bg",),
            )
            text_shell.tag_lower(bg_id)

        def _resize_output_shell(_event=None):
            width = text_shell.winfo_width()
            height = text_shell.winfo_height()
            if width <= 1 or height <= 1:
                return
            _draw_output_shell()
            text_shell.coords(text_window, 12, 12)
            text_shell.itemconfigure(text_window, width=max(1, width - 24), height=max(1, height - 24))

        text_shell.bind("<Configure>", _resize_output_shell)

        # Configure text tags for section headers
        self._output_text.tag_configure(
            "header",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            foreground=COLOR_ACCENT,
            spacing1=12, spacing3=4,
        )
        self._output_text.tag_configure(
            "body",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            foreground=COLOR_TEXT,
            spacing1=2,
        )

    # ------------------------------------------------------------------

    def _build_action_bar(self):
        bar = tk.Frame(self, bg=COLOR_BG)
        bar.pack(fill="x", padx=16, pady=(4, 12))

        self._gen_btn = self._build_action_button(
            bar,
            label="Generate Interpretation",
            command=self._on_generate,
            kind="primary",
            icon="generate",
        )
        self._gen_btn.pack(side="left")

        # Status label
        self._status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(
            bar, textvariable=self._status_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_BG, fg=COLOR_TEXT_LIGHT,
        )
        self._status_lbl.pack(side="left", padx=12)

        # Download buttons (right-aligned)
        self._pdf_btn = self._build_action_button(
            bar,
            label="Download as PDF",
            command=self._download_pdf,
            kind="secondary",
            icon="file",
        )
        self._pdf_btn.pack(side="right", padx=(4, 0))
        self._txt_btn = self._build_action_button(
            bar,
            label="Download as TXT",
            command=self._download_txt,
            kind="secondary",
            icon="file",
        )
        self._txt_btn.pack(side="right", padx=(4, 0))

    def _build_action_button(self, parent: tk.Misc, label: str, command, kind: str, icon: str) -> tk.Canvas:
        btn_font = tkFont.Font(family=FONT_FAMILY, size=11)
        text_w = btn_font.measure(label)
        bg = "#30455c" if kind == "primary" else TOPBAR_EXCEL_BG
        hover_bg = "#37506d" if kind == "primary" else TOPBAR_EXCEL_HOVER_BG
        fg = "#f5f7fa" if kind == "primary" else TOPBAR_EXCEL_FG
        border = "#30455c" if kind == "primary" else TOPBAR_EXCEL_BORDER
        btn_w = TOPBAR_EXCEL_PADX + TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP + text_w + TOPBAR_EXCEL_PADX

        btn = tk.Canvas(
            parent,
            width=btn_w + 2,
            height=TOPBAR_EXCEL_HEIGHT + 2,
            bg=COLOR_BG,
            highlightthickness=0,
            cursor=CURSOR_HAND,
        )
        btn._label = label
        btn._kind = kind

        hover = {"value": 0.0, "job": None}

        def _draw(color: str):
            btn.delete("all")
            pts = _rrect_pts(1, 1, btn_w + 1, TOPBAR_EXCEL_HEIGHT + 1, TOPBAR_EXCEL_RADIUS)
            btn.create_polygon(*pts, fill=color, outline=border, width=1)
            cy = 1 + TOPBAR_EXCEL_HEIGHT // 2
            content_w = TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP + text_w
            ix = 1 + (btn_w - content_w) // 2
            iy = 1 + (TOPBAR_EXCEL_HEIGHT - TOPBAR_EXCEL_ICON_SIZE) // 2
            if icon == "generate":
                self._draw_generate_icon(btn, ix, iy, fg)
            else:
                self._draw_file_corner_icon(btn, ix, iy, fg)
            btn.create_text(
                ix + TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP,
                cy,
                text=label,
                fill=fg,
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
                    _draw(hover_bg if target else bg)
                    hover["job"] = None
                    return
                hover["value"] += diff * 0.3
                _draw(hover_bg if hover["value"] >= 0.5 else bg)
                hover["job"] = btn.after(16, _tick)

            _tick()

        btn.bind("<Enter>", lambda _e: _animate(1.0))
        btn.bind("<Leave>", lambda _e: _animate(0.0))
        btn.bind("<Button-1>", lambda _e: command())
        _draw(bg)
        return btn

    def _set_action_button_state(self, btn: tk.Canvas, disabled: bool, label: Optional[str] = None):
        if label is not None:
            btn._label = label
        state = "disabled" if disabled else "normal"
        btn.configure(cursor="watch" if disabled else CURSOR_HAND)
        if disabled:
            btn.unbind("<Button-1>")
        else:
            if btn is self._gen_btn:
                btn.bind("<Button-1>", lambda _e: self._on_generate())
        # force redraw via rebuild helper
        kind = getattr(btn, "_kind", "secondary")
        text = getattr(btn, "_label", "")
        btn_font = tkFont.Font(family=FONT_FAMILY, size=11)
        text_w = btn_font.measure(text)
        fg = "#f5f7fa" if kind == "primary" else TOPBAR_EXCEL_FG
        bg = "#6b7280" if disabled and kind == "primary" else ("#30455c" if kind == "primary" else TOPBAR_EXCEL_BG)
        border = "#6b7280" if disabled and kind == "primary" else ("#30455c" if kind == "primary" else TOPBAR_EXCEL_BORDER)
        btn.delete("all")
        pts = _rrect_pts(1, 1, btn.winfo_width() - 1, btn.winfo_height() - 1, TOPBAR_EXCEL_RADIUS)
        btn.create_polygon(*pts, fill=bg, outline=border, width=1)
        cy = btn.winfo_height() / 2
        content_w = TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP + text_w
        ix = 1 + (btn.winfo_width() - 2 - content_w) // 2
        iy = 1 + (TOPBAR_EXCEL_HEIGHT - TOPBAR_EXCEL_ICON_SIZE) // 2
        if kind == "primary":
            self._draw_generate_icon(btn, ix, iy, fg)
        else:
            self._draw_file_corner_icon(btn, ix, iy, fg)
        btn.create_text(ix + TOPBAR_EXCEL_ICON_SIZE + TOPBAR_EXCEL_ICON_GAP, cy, text=text, fill=fg, anchor="w", font=btn_font)

    def _draw_file_corner_icon(self, canvas: tk.Canvas, ox: int, oy: int, fg: str):
        s = TOPBAR_EXCEL_ICON_SIZE / 24.0
        lw = 1.35
        kw = dict(fill=fg, width=lw, capstyle="round", joinstyle="round")
        canvas.create_line(12*s+ox, 22*s+oy, 18*s+ox, 22*s+oy, 20*s+ox, 20*s+oy, 20*s+ox, 8*s+oy, **kw)
        canvas.create_line(20*s+ox, 8*s+oy, 14*s+ox, 2*s+oy, 6*s+ox, 2*s+oy, 4*s+ox, 4*s+oy, 4*s+ox, 10*s+oy, **kw)
        canvas.create_line(14*s+ox, 2*s+oy, 14*s+ox, 7*s+oy, 20*s+ox, 7*s+oy, **kw)
        canvas.create_line(3*s+ox, 16*s+oy, 3*s+ox, 14.5*s+oy, 3.5*s+ox, 14*s+oy, 10.5*s+ox, 14*s+oy, 11*s+ox, 14.5*s+oy, 11*s+ox, 16*s+oy, **kw)
        canvas.create_line(6*s+ox, 22*s+oy, 8*s+ox, 22*s+oy, **kw)
        canvas.create_line(7*s+ox, 14*s+oy, 7*s+ox, 22*s+oy, **kw)

    def _draw_generate_icon(self, canvas: tk.Canvas, ox: int, oy: int, fg: str):
        s = TOPBAR_EXCEL_ICON_SIZE / 24.0
        lw = 1.35
        kw = dict(fill=fg, width=lw, capstyle="round", joinstyle="round")
        pts = [
            15.033*s+ox, 9.44*s+oy,
            10.968*s+ox, 7.088*s+oy,
            10*s+ox, 7.648*s+oy,
            10*s+ox, 12.352*s+oy,
            10.968*s+ox, 12.912*s+oy,
            15.033*s+ox, 10.56*s+oy,
        ]
        canvas.create_polygon(*pts, outline=fg, fill="", width=lw)
        canvas.create_line(12*s+ox, 17*s+oy, 12*s+ox, 21*s+oy, **kw)
        canvas.create_line(8*s+ox, 21*s+oy, 16*s+ox, 21*s+oy, **kw)
        canvas.create_line(4*s+ox, 3*s+oy, 20*s+ox, 3*s+oy, 22*s+ox, 5*s+oy, 22*s+ox, 15*s+oy, 20*s+ox, 17*s+oy, 4*s+ox, 17*s+oy, 2*s+ox, 15*s+oy, 2*s+ox, 5*s+oy, 4*s+ox, 3*s+oy, **kw)

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def _on_generate(self):
        if self._running:
            return

        engine  = self._engine_var.get()
        model   = self._model_var.get()
        api_key = self._api_key_var.get().strip()

        if not api_key:
            messagebox.showwarning(
                "API Key Required",
                "Please enter your API key before generating.",
                parent=self,
            )
            return

        prompt = build_prompt(self._result)

        self._running = True
        self._set_action_button_state(self._gen_btn, True, "Generating...")
        self._status_var.set(f"Calling {engine} / {model} ...")
        self._set_output("")

        def _worker():
            try:
                response = call_llm(engine, model, api_key, prompt)
                self.after(0, lambda: self._on_success(response))
            except Exception as exc:
                self.after(0, lambda e=str(exc): self._on_error(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_success(self, response: str):
        self._running = False
        self._response = response
        self._set_action_button_state(self._gen_btn, False, "Generate Interpretation")
        self._status_var.set("Done.")
        self._render_response(response)
        # Clear API key from memory immediately
        self._api_key_var.set("")

    def _on_error(self, error: str):
        self._running = False
        self._set_action_button_state(self._gen_btn, False, "Generate Interpretation")
        self._status_var.set("Error.")
        # Clear API key from memory immediately
        self._api_key_var.set("")
        messagebox.showerror(
            "LLM Error",
            f"The request failed:\n\n{error}",
            parent=self,
        )

    def _set_output(self, text: str):
        self._output_text.config(state="normal")
        self._output_text.delete("1.0", "end")
        self._output_text.insert("1.0", text)
        self._output_text.config(state="disabled")

    def _render_response(self, text: str):
        """Render with section headers bolded in navy."""
        self._output_text.config(state="normal")
        self._output_text.delete("1.0", "end")

        for line in text.splitlines():
            stripped = line.strip()
            # Detect section headers (## or numbered like "1. ")
            is_header = (
                stripped.startswith("##") or
                any(stripped.startswith(f"{i}.") for i in range(1, 8))
            )
            clean = stripped.lstrip("#").strip()
            if is_header:
                self._output_text.insert("end", clean + "\n", "header")
            else:
                self._output_text.insert("end", line + "\n", "body")

        self._output_text.config(state="disabled")
        self._output_text.see("1.0")

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    def _download_txt(self):
        if not self._response:
            messagebox.showinfo("Nothing to Save",
                                "Generate an interpretation first.",
                                parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save interpretation as TXT",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            initialfile="policy_interpretation.txt",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._response)
        messagebox.showinfo("Saved", f"Saved to:\n{path}", parent=self)

    def _download_pdf(self):
        if not self._response:
            messagebox.showinfo("Nothing to Save",
                                "Generate an interpretation first.",
                                parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save interpretation as PDF",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf"), ("All files", "*.*")],
            initialfile="policy_interpretation.pdf",
        )
        if not path:
            return
        try:
            self._write_pdf(path)
            messagebox.showinfo("Saved", f"Saved to:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("PDF Error", str(exc), parent=self)

    def _write_pdf(self, path: str):
        """Write the response to a PDF using reportlab if available,
        otherwise fall back to a plain-text PDF via fpdf2."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer
            )

            doc    = SimpleDocTemplate(path, pagesize=A4,
                                       leftMargin=2*cm, rightMargin=2*cm,
                                       topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            h_style = ParagraphStyle(
                "Section",
                parent=styles["Heading2"],
                textColor=colors.HexColor("#2c4a6e"),
                spaceAfter=6,
            )
            b_style = ParagraphStyle(
                "Body",
                parent=styles["Normal"],
                spaceAfter=8,
                leading=14,
            )

            story = []
            for line in self._response.splitlines():
                stripped = line.strip()
                is_header = (
                    stripped.startswith("##") or
                    any(stripped.startswith(f"{i}.") for i in range(1, 8))
                )
                clean = stripped.lstrip("#").strip()
                if not clean:
                    story.append(Spacer(1, 6))
                elif is_header:
                    story.append(Paragraph(clean, h_style))
                else:
                    story.append(Paragraph(
                        line.replace("&", "&amp;").replace("<", "&lt;"),
                        b_style))
            doc.build(story)

        except ImportError:
            # Fallback: fpdf2
            try:
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=20)

                for line in self._response.splitlines():
                    stripped = line.strip()
                    is_header = (
                        stripped.startswith("##") or
                        any(stripped.startswith(f"{i}.") for i in range(1,8))
                    )
                    clean = stripped.lstrip("#").strip()
                    if not clean:
                        pdf.ln(4)
                    elif is_header:
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.set_text_color(44, 74, 110)
                        pdf.multi_cell(0, 8, clean)
                        pdf.set_text_color(0, 0, 0)
                    else:
                        pdf.set_font("Helvetica", "", 10)
                        pdf.multi_cell(0, 6, line)
                pdf.output(path)

            except ImportError:
                raise ImportError(
                    "PDF export requires reportlab or fpdf2.\n"
                    "Install with:  pip install reportlab\n"
                    "or:            pip install fpdf2"
                )
