# =============================================================================
# Policy Coherence Kit -- llm_tab.py
# LLMInterpretationTab: LLM-powered structured interpretation of analysis.
#
# - User selects engine, model, enters API key (never saved)
# - Clicking "Generate Interpretation" assembles a structured prompt from
#   all analysis results and calls the selected LLM API
# - Response is displayed in a structured scrollable text area
# - Downloadable as .txt or .pdf
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional

from aggregator import AggregationResult
from coherence_scores_tab import compute_scores
from range_of_influence_tab import compute_entropy
from network_tab import compute_centrality
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER, FONT_SIZE_TITLE,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
    COLOR_BUTTON, COLOR_BUTTON_FG,
    CURSOR_HAND,
)

# =============================================================================
# Engine / model registry
# =============================================================================

ENGINES = {
    "Groq (Free)": {
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-groq-70b-8192-tool-use-preview",
            "gemma2-9b-it",
            "mixtral-8x7b-32768",
        ],
        "base_url": "https://api.groq.com/openai/v1",
        "style": "openai_compat",
    },
    "OpenAI": {
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
        ],
        "base_url": "https://api.openai.com/v1",
        "style": "openai_compat",
    },
    "Anthropic": {
        "models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
        "base_url": "https://api.anthropic.com",
        "style": "anthropic",
    },
    "Google Gemini": {
        "models": [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash",
        ],
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "style": "gemini",
    },
    "Mistral": {
        "models": [
            "mistral-small-latest",
            "mistral-medium-latest",
            "open-mistral-7b",
        ],
        "base_url": "https://api.mistral.ai/v1",
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


def _call_anthropic(api_key: str, model: str,
                     system: str, user: str) -> str:
    data = _http_post(
        url="https://api.anthropic.com/v1/messages",
        payload={
            "model": model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        return data["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected response structure:\n{data}")


def _call_gemini(api_key: str, model: str,
                  system: str, user: str) -> str:
    combined = f"{system}\n\n{user}"
    data = _http_post(
        url=(f"https://generativelanguage.googleapis.com/v1beta/models/"
             f"{model}:generateContent?key={api_key}"),
        payload={
            "contents": [{"parts": [{"text": combined}]}],
            "generationConfig": {
                "maxOutputTokens": 4096,
                "temperature": 0.3,
            },
        },
        headers={"Content-Type": "application/json"},
    )
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
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
    elif style == "anthropic":
        return _call_anthropic(api_key, model, SYSTEM_PROMPT, prompt)
    elif style == "gemini":
        return _call_gemini(api_key, model, SYSTEM_PROMPT, prompt)
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
        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        self._build_info_bar()
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)
        self._build_config_panel()
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill="x", pady=4)
        self._build_output_area()
        self._build_action_bar()
        self._update_models()

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
            text=f"LLM Interpretation  —  {method_label}",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
        ).pack(side="left", padx=16)

        tk.Label(
            bar,
            text="API key is used once and never stored.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------------

    def _build_config_panel(self):
        panel = tk.Frame(self, bg=COLOR_BG)
        panel.pack(fill="x", padx=16, pady=8)

        # Engine
        tk.Label(panel, text="Engine:",
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT, width=10, anchor="w",
                 ).grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")

        engine_cb = ttk.Combobox(
            panel, textvariable=self._engine_var,
            values=list(ENGINES.keys()),
            state="readonly", width=22,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        )
        engine_cb.grid(row=0, column=1, padx=(0, 24), pady=4, sticky="w")
        engine_cb.bind("<<ComboboxSelected>>",
                       lambda e: self._update_models())

        # Model
        tk.Label(panel, text="Model:",
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT, width=10, anchor="w",
                 ).grid(row=0, column=2, padx=(0, 8), pady=4, sticky="w")

        self._model_cb = ttk.Combobox(
            panel, textvariable=self._model_var,
            state="readonly", width=30,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        )
        self._model_cb.grid(row=0, column=3, padx=(0, 24), pady=4, sticky="w")

        # API Key
        tk.Label(panel, text="API Key:",
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT, width=10, anchor="w",
                 ).grid(row=1, column=0, padx=(0, 8), pady=4, sticky="w")

        key_entry = tk.Entry(
            panel, textvariable=self._api_key_var,
            show="•",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff", fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief="solid", bd=1, width=55,
        )
        key_entry.grid(row=1, column=1, columnspan=3,
                       padx=(0, 24), pady=4, sticky="w")

        # Show/hide toggle
        self._show_key = tk.BooleanVar(value=False)

        def _toggle_key():
            key_entry.config(show="" if self._show_key.get() else "•")

        tk.Checkbutton(
            panel, text="Show key",
            variable=self._show_key,
            command=_toggle_key,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, activebackground=COLOR_BG,
            cursor=CURSOR_HAND,
        ).grid(row=1, column=4, padx=4, pady=4, sticky="w")

    # ------------------------------------------------------------------

    def _update_models(self):
        engine = self._engine_var.get()
        models = ENGINES[engine]["models"]
        self._model_cb.config(values=models)
        self._model_var.set(models[0])

    # ------------------------------------------------------------------

    def _build_output_area(self):
        out_frame = tk.Frame(self, bg=COLOR_BG)
        out_frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        tk.Label(
            out_frame,
            text="Interpretation:",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(anchor="w", pady=(0, 4))

        text_frame = tk.Frame(out_frame, bg=COLOR_BG)
        text_frame.pack(fill="both", expand=True)

        self._output_text = tk.Text(
            text_frame,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg="#ffffff", fg=COLOR_TEXT,
            relief="solid", bd=1,
            wrap="word",
            state="disabled",
            insertbackground=COLOR_ACCENT,
            padx=12, pady=10,
        )
        sb = ttk.Scrollbar(text_frame, command=self._output_text.yview)
        self._output_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._output_text.pack(side="left", fill="both", expand=True)

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

        # Generate button
        self._gen_btn = tk.Button(
            bar,
            text="  Generate Interpretation",
            command=self._on_generate,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_BUTTON, fg=COLOR_BUTTON_FG,
            activebackground=COLOR_ACCENT2,
            relief="flat", padx=14, pady=6,
            cursor=CURSOR_HAND,
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
        for label, cmd in [
            ("Download as TXT", self._download_txt),
            ("Download as PDF", self._download_pdf),
        ]:
            tk.Button(
                bar, text=label, command=cmd,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_PANEL, fg=COLOR_ACCENT,
                relief="flat", padx=8, pady=5,
                cursor=CURSOR_HAND,
            ).pack(side="right", padx=(4, 0))

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
        self._gen_btn.config(state="disabled", text="  Generating...")
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
        self._gen_btn.config(state="normal", text="  Generate Interpretation")
        self._status_var.set("Done.")
        self._render_response(response)
        # Clear API key from memory immediately
        self._api_key_var.set("")

    def _on_error(self, error: str):
        self._running = False
        self._gen_btn.config(state="normal", text="  Generate Interpretation")
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
