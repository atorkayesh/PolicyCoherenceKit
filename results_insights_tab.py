# =============================================================================
# Policy Coherence Kit -- results_insights_tab.py
# Extended dashboard-style summary tab shown before the detailed analysis tabs.
# =============================================================================

import math
import tkinter as tk
from collections import Counter
from typing import Dict, List, Optional, Tuple

from aggregator import AggregationResult
from coherence_scores_tab import compute_scores
from range_of_influence_tab import compute_entropy
from network_tab import compute_centrality
from constants import (
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL,
    FONT_SIZE_HEADER,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_ACCENT2,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_BORDER,
)

_CARD_BG = "#ffffff"
_CARD_BORDER = "#d9d5ce"
_POS = "#2A9D8F"
_NEG = "#C8643B"
_MID = "#E7B34A"
_SCATTER_BG = "#fbfcfd"
_SOFT_BG = "#f7f8fa"
_TEAL_BAR = "#2b7a78"


class _WrapFrame(tk.Frame):
    def __init__(self, *args, gap=6, row_gap=6, **kwargs):
        super().__init__(*args, **kwargs)
        self._items = []
        self._gap = gap
        self._row_gap = row_gap
        self.bind("<Configure>", self._reflow)

    def add(self, widget):
        self._items.append(widget)

    def _reflow(self, _event=None):
        width = self.winfo_width()
        if width <= 1:
            return
        x = y = row_h = 0
        for widget in self._items:
            widget.update_idletasks()
            w = widget.winfo_reqwidth()
            h = widget.winfo_reqheight()
            if x and x + w > width:
                x = 0
                y += row_h + self._row_gap
                row_h = 0
            widget.place(x=x, y=y)
            x += w + self._gap
            row_h = max(row_h, h)
        self.configure(height=y + row_h)


def _method_label(method: str) -> str:
    return {
        "average": "Average",
        "majority": "Majority Rule",
        "weighted": "Weighted",
    }.get(method, method.title())


def _build_graph_stats(result: AggregationResult) -> Dict[str, object]:
    n = result.n
    pos = neg = zero = 0
    strongest_pos = None
    strongest_neg = None
    strongest_pos_pair = None
    strongest_neg_pair = None

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            score = result.scores.get((i, j), 0.0) or 0.0
            if score > 0:
                pos += 1
                if strongest_pos is None or score > strongest_pos:
                    strongest_pos = score
                    strongest_pos_pair = (i, j)
            elif score < 0:
                neg += 1
                if strongest_neg is None or score < strongest_neg:
                    strongest_neg = score
                    strongest_neg_pair = (i, j)
            else:
                zero += 1

    max_edges = n * (n - 1) if n > 1 else 1
    density = round((pos + neg) / max_edges, 3)
    polarity = round(pos / (pos + neg), 3) if (pos + neg) else 0.5

    return {
        "positive_edges": pos,
        "negative_edges": neg,
        "zero_edges": zero,
        "density": density,
        "polarity": polarity,
        "strongest_pos": strongest_pos if strongest_pos is not None else 0.0,
        "strongest_neg": strongest_neg if strongest_neg is not None else 0.0,
        "strongest_pos_pair": strongest_pos_pair,
        "strongest_neg_pair": strongest_neg_pair,
    }


def _agreement_stats(result: AggregationResult) -> Dict[str, object]:
    rows = []
    dm_count = max(1, result.decision_makers or len(result.decision_maker_names) or 1)
    for i in range(result.n):
        for j in range(result.n):
            if i == j:
                continue
            values = [float(v) for v in result.source_scores.get((i, j), [])]
            if not values:
                continue
            counts = Counter(values)
            agreement_ratio = round(max(counts.values()) / dm_count, 3)
            spread = round(max(values) - min(values), 2)
            rows.append({
                "i": i,
                "j": j,
                "pair": f"{result.codes[i]} -> {result.codes[j]}",
                "score": result.scores.get((i, j), 0.0) or 0.0,
                "agreement_ratio": agreement_ratio,
                "spread": spread,
            })

    contested = sorted(
        rows,
        key=lambda row: (row["agreement_ratio"], -row["spread"], -abs(row["score"]))
    )[:5]
    consensus = sorted(
        [row for row in rows if abs(row["score"]) > 0.0],
        key=lambda row: (-row["agreement_ratio"], -abs(row["score"]))
    )[:5]
    average_agreement = round(
        sum(row["agreement_ratio"] for row in rows) / len(rows), 3
    ) if rows else 1.0

    return {
        "rows": rows,
        "contested": contested,
        "strong_consensus": consensus,
        "average_agreement": average_agreement,
    }


def _quadrant_label(net: float, prominence: float, threshold: float) -> str:
    if prominence >= threshold and net > 0.05:
        return "System Driver"
    if prominence >= threshold and net < -0.05:
        return "System Dependent"
    if prominence < threshold and net > 0.05:
        return "Strategic Lever"
    if prominence < threshold and net < -0.05:
        return "Vulnerable Node"
    return "Balanced"


def _build_narrative(result: AggregationResult, insights: Dict[str, object]) -> List[str]:
    top_driver = insights["top_driver"]
    top_dependent = insights["top_dependent"]
    top_prominent = insights["top_prominent"]
    graph = insights["graph"]
    agreement = insights["agreement"]

    lines = []
    if top_driver:
        lines.append(
            f"{top_driver['code']} emerges as the strongest net driver ({top_driver['net']:+.2f}), "
            f"suggesting a comparatively high outward effect on the policy system."
        )
    if top_dependent:
        lines.append(
            f"{top_dependent['code']} is the most structurally dependent policy ({top_dependent['net']:+.2f}), "
            f"receiving substantially more influence than it exerts."
        )
    if top_prominent:
        lines.append(
            f"{top_prominent['code']} shows the highest overall prominence ({top_prominent['prominence']:.2f}), "
            f"making it a central policy for interpretation and intervention sequencing."
        )
    lines.append(
        f"The aggregated structure contains {graph['positive_edges']} positive and {graph['negative_edges']} negative relations "
        f"with density {graph['density']:.3f} and a positive polarity share of {graph['polarity']:.3f}."
    )
    lines.append(
        f"Average inter-rater agreement is {agreement['average_agreement']:.3f}, which helps separate robust links from contested relations."
    )
    return lines[:4]


def compute_insights(result: AggregationResult) -> Dict[str, object]:
    score_rows = compute_scores(result)
    entropy_rows = compute_entropy(result)
    centrality_rows = compute_centrality(result)
    graph_stats = _build_graph_stats(result)
    agreement = _agreement_stats(result)

    entropy_by_code = {row["code"]: row for row in entropy_rows}
    centrality_by_code = {row["code"]: row for row in centrality_rows}

    enriched = []
    prominences = []
    for idx, row in enumerate(score_rows):
        net = round(row["woi"] - row["wii"], 2)
        prominence = round(
            sum(abs(result.scores.get((idx, j), 0.0) or 0.0) for j in range(result.n) if j != idx) +
            sum(abs(result.scores.get((j, idx), 0.0) or 0.0) for j in range(result.n) if j != idx),
            2,
        )
        enriched_row = {
            **row,
            "net": net,
            "prominence": prominence,
            "entropy": entropy_by_code[row["code"]]["entropy"],
            "entropy_category": entropy_by_code[row["code"]]["category"],
            "betweenness": centrality_by_code[row["code"]]["betweenness"],
            "closeness": centrality_by_code[row["code"]]["closeness"],
        }
        enriched.append(enriched_row)
        prominences.append(prominence)

    threshold = sorted(prominences)[len(prominences) // 2] if prominences else 0.0
    for row in enriched:
        row["quadrant"] = _quadrant_label(row["net"], row["prominence"], threshold)

    drivers = [row for row in enriched if row["net"] > 0.05]
    dependents = [row for row in enriched if row["net"] < -0.05]
    balanced = [row for row in enriched if -0.05 <= row["net"] <= 0.05]

    insights = {
        "rows": enriched,
        "drivers": drivers,
        "dependents": dependents,
        "balanced": balanced,
        "top_driver": max(enriched, key=lambda row: row["net"], default=None),
        "top_dependent": min(enriched, key=lambda row: row["net"], default=None),
        "top_prominent": max(enriched, key=lambda row: row["prominence"], default=None),
        "top_broker": max(enriched, key=lambda row: row["betweenness"], default=None),
        "top_prominence_rows": sorted(enriched, key=lambda row: row["prominence"], reverse=True)[:5],
        "top_driver_rows": sorted(enriched, key=lambda row: row["net"], reverse=True)[:5],
        "top_dependent_rows": sorted(enriched, key=lambda row: row["net"])[:5],
        "graph": graph_stats,
        "agreement": agreement,
        "quadrant_threshold": threshold,
    }
    insights["narrative"] = _build_narrative(result, insights)
    return insights


class ResultsInsightsTab(tk.Frame):
    def __init__(self, parent, result: AggregationResult, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._result = result
        self._insights = compute_insights(result)
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        scroll = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=COLOR_BG)
        canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self._build_top_dashboard(body)
        self._build_analysis_grid(body)
        self._build_bottom_grid(body)

    def _build_info_bar(self):
        bar = tk.Frame(self, bg=COLOR_PANEL, pady=8)
        bar.pack(fill="x")

        tk.Label(
            bar,
            text=f"Results Insights  -  {_method_label(self._result.method)}",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            bg=COLOR_PANEL, fg=COLOR_ACCENT,
        ).pack(side="left", padx=16)

        graph = self._insights["graph"]
        subtitle = (
            f"{self._result.n} policies  |  "
            f"{self._result.decision_makers} decision-makers  |  "
            f"density: {graph['density']}  |  agreement: {self._insights['agreement']['average_agreement']:.3f}"
        )
        tk.Label(
            bar,
            text=subtitle,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
            bg=COLOR_PANEL, fg=COLOR_TEXT_LIGHT,
        ).pack(side="left", padx=6)

    def _build_top_dashboard(self, parent: tk.Frame):
        panel = tk.Frame(parent, bg=COLOR_BG)
        panel.pack(fill="x", padx=16, pady=(10, 10))
        panel.grid_columnconfigure(0, weight=5, uniform="hero")
        panel.grid_columnconfigure(1, weight=5, uniform="hero")
        panel.grid_columnconfigure(2, weight=5, uniform="hero")

        self._summary_panel(panel).grid(row=0, column=0, padx=6, sticky="nsew")
        self._configuration_panel(panel).grid(row=0, column=1, padx=6, sticky="nsew")
        self._group_ranking_panel(panel).grid(row=0, column=2, padx=6, sticky="nsew")

    def _summary_panel(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Summary Insights", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(card, text="Key structural signals from the aggregated analysis.", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(anchor="w", padx=16, pady=(0, 12))

        grid = tk.Frame(card, bg=_CARD_BG)
        grid.pack(fill="x", padx=12, pady=(0, 12))
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1, uniform="summarybox")

        stats = [
            ("Driving Factors", str(len(self._insights["drivers"])), "Policies acting as net drivers."),
            ("Dependent Factors", str(len(self._insights["dependents"])), "Policies primarily influenced by others."),
            ("Top Prominence", self._value_text(self._insights["top_prominent"], "prominence"), "Highest overall structural load."),
            ("Strongest Relation", f"{self._insights['graph']['strongest_pos']:+.2f}", self._format_pair(self._insights["graph"]["strongest_pos_pair"])),
        ]
        for idx, (title, value, caption) in enumerate(stats):
            self._mini_stat_card(grid, title, value, caption).grid(row=idx // 2, column=idx % 2, padx=4, pady=4, sticky="nsew")
        return card

    def _configuration_panel(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Analysis Configuration", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=16, pady=(14, 10))

        config = tk.Frame(card, bg=_CARD_BG)
        config.pack(fill="x", padx=16)
        rows = [
            ("Result Type", _method_label(self._result.method)),
            ("Decision-Makers", str(self._result.decision_makers)),
            ("Policies", str(self._result.n)),
            ("Density", f"{self._insights['graph']['density']:.3f}"),
            ("Agreement", f"{self._insights['agreement']['average_agreement']:.3f}"),
        ]
        for label, value in rows:
            line = tk.Frame(config, bg=_CARD_BG)
            line.pack(fill="x", pady=2)
            tk.Label(line, text=label, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="left")
            tk.Label(line, text=value, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_CARD_BG, fg=COLOR_ACCENT).pack(side="right")

        tk.Frame(card, bg=COLOR_BORDER, height=1).pack(fill="x", padx=16, pady=12)
        self._compact_group_block(card, "Effect Group (Dependent Factors)", self._insights["dependents"], _NEG).pack(fill="x", padx=16, pady=(0, 14))
        return card

    def _group_ranking_panel(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        self._compact_group_block(card, "Cause Group (Driving Factors)", self._insights["drivers"], _POS).pack(fill="x", padx=16, pady=(14, 14))
        tk.Frame(card, bg=COLOR_BORDER, height=1).pack(fill="x", padx=16, pady=(0, 12))
        self._prominence_strip_block(card).pack(fill="x", padx=16, pady=(0, 14))
        return card

    def _compact_group_block(self, parent: tk.Frame, title: str, rows: List[dict], accent: str) -> tk.Frame:
        frame = tk.Frame(parent, bg=_CARD_BG)
        tk.Label(frame, text=title, font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", pady=(0, 8))
        wrap = _WrapFrame(frame, bg=_CARD_BG, gap=6, row_gap=8)
        wrap.pack(fill="x")
        if not rows:
            tk.Label(wrap, text="None", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).place(x=0, y=0)
            wrap.configure(height=20)
            return frame
        for row in rows:
            chip = tk.Label(
                wrap,
                text=row["code"],
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg=accent, fg="#ffffff",
                padx=10, pady=6,
            )
            wrap.add(chip)
        return frame

    def _prominence_strip_block(self, parent: tk.Frame) -> tk.Frame:
        frame = tk.Frame(parent, bg=_CARD_BG)
        tk.Label(frame, text="Prominence and Relation Analysis", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", pady=(0, 10))
        rows = self._insights["top_prominence_rows"][:4]
        max_value = max((row["prominence"] for row in rows), default=1.0) or 1.0
        for row in rows:
            line = tk.Frame(frame, bg=_CARD_BG)
            line.pack(fill="x", pady=5)
            tk.Label(line, text=row["code"], width=5, anchor="w", font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(side="left")
            bar_host = tk.Frame(line, bg="#e7eef0", height=8)
            bar_host.pack(side="left", fill="x", expand=True, padx=8)
            bar_host.pack_propagate(False)
            tk.Frame(bar_host, bg=_TEAL_BAR, height=8).place(relx=0, rely=0, relheight=1, relwidth=max(0.04, row["prominence"] / max_value))
            tk.Label(line, text=f"P {row['prominence']:.4f}", width=10, anchor="e", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="left", padx=(8, 4))
            tk.Label(line, text=f"R {row['net']:+.4f}", width=10, anchor="e", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="left")
        return frame

    def _mini_stat_card(self, parent: tk.Frame, title: str, value: str, caption: str) -> tk.Frame:
        card = tk.Frame(parent, bg=_SOFT_BG, highlightbackground="#eef0f2", highlightthickness=1)
        tk.Label(card, text=title, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_SOFT_BG, fg=COLOR_TEXT_LIGHT, anchor="w").pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(card, text=value, font=(FONT_FAMILY, FONT_SIZE_HEADER + 5, "bold"), bg=_SOFT_BG, fg=COLOR_ACCENT, anchor="w").pack(fill="x", padx=12)
        tk.Label(card, text=caption, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_SOFT_BG, fg=COLOR_TEXT_LIGHT, wraplength=220, justify="left", anchor="w").pack(fill="x", padx=12, pady=(8, 12))
        return card

    def _build_analysis_grid(self, parent: tk.Frame):
        row = tk.Frame(parent, bg=COLOR_BG)
        row.pack(fill="x", padx=16, pady=8)
        row.grid_columnconfigure(0, weight=3, uniform="analysis")
        row.grid_columnconfigure(1, weight=2, uniform="analysis")

        self._scatter_card(row).grid(row=0, column=0, padx=6, sticky="nsew")
        self._relations_card(row).grid(row=0, column=1, padx=6, sticky="nsew")

    def _build_bottom_grid(self, parent: tk.Frame):
        row = tk.Frame(parent, bg=COLOR_BG)
        row.pack(fill="x", padx=16, pady=(8, 16))
        for col in range(3):
            row.grid_columnconfigure(col, weight=1, uniform="bottom")

        self._configuration_card(row).grid(row=0, column=0, padx=6, sticky="nsew")
        self._ranking_card(row).grid(row=0, column=1, padx=6, sticky="nsew")
        self._agreement_card(row).grid(row=0, column=2, padx=6, sticky="nsew")

    def _metric_card(self, parent: tk.Frame, title: str, main: str, sub: str) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text=title, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, anchor="w").pack(fill="x", padx=14, pady=(12, 8))
        tk.Label(card, text=main, font=(FONT_FAMILY, FONT_SIZE_HEADER + 2, "bold"), bg=_CARD_BG, fg=COLOR_ACCENT, anchor="w", justify="left").pack(fill="x", padx=14)
        tk.Label(card, text=sub, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, anchor="w", justify="left").pack(fill="x", padx=14, pady=(6, 12))
        return card

    def _scatter_card(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Cause-Effect Positioning", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            card,
            text="X-axis shows net influence. Y-axis shows prominence. The dashed guides separate high and low prominence as well as driver and dependent zones.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, wraplength=620, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))
        canvas = tk.Canvas(card, bg=_SCATTER_BG, width=620, height=320, highlightthickness=1, highlightbackground="#e2e6ea")
        canvas.pack(fill="x", padx=14, pady=(0, 12))
        self._draw_scatter(canvas)
        return card

    def _draw_scatter(self, canvas: tk.Canvas):
        rows = self._insights["rows"]
        if not rows:
            return
        w = int(canvas.cget("width"))
        h = int(canvas.cget("height"))
        m = 42

        min_net = min(row["net"] for row in rows)
        max_net = max(row["net"] for row in rows)
        min_prom = min(row["prominence"] for row in rows)
        max_prom = max(row["prominence"] for row in rows)

        if math.isclose(min_net, max_net):
            min_net -= 1.0
            max_net += 1.0
        if math.isclose(min_prom, max_prom):
            min_prom = 0.0
            max_prom += 1.0

        def sx(value):
            return m + (value - min_net) / (max_net - min_net) * (w - 2 * m)

        def sy(value):
            return h - m - (value - min_prom) / (max_prom - min_prom) * (h - 2 * m)

        canvas.create_line(m, h - m, w - m, h - m, fill="#90a0ad")
        canvas.create_line(m, m, m, h - m, fill="#90a0ad")
        canvas.create_line(sx(0.0), m, sx(0.0), h - m, fill="#d4dbe1", dash=(4, 4))
        canvas.create_line(m, sy(self._insights["quadrant_threshold"]), w - m, sy(self._insights["quadrant_threshold"]), fill="#d4dbe1", dash=(4, 4))
        canvas.create_text(w - m - 56, m + 8, text="Drivers", anchor="nw", fill="#9aa6b2", font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(m + 8, m + 8, text="Dependents", anchor="nw", fill="#9aa6b2", font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(w - m - 62, h - m - 20, text="Strategic", anchor="nw", fill="#9aa6b2", font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(m + 8, h - m - 20, text="Vulnerable", anchor="nw", fill="#9aa6b2", font=(FONT_FAMILY, FONT_SIZE_SMALL))

        for row in rows:
            x = sx(row["net"])
            y = sy(row["prominence"])
            color = _POS if row["net"] > 0.05 else _NEG if row["net"] < -0.05 else _MID
            canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=color, outline="#ffffff", width=1.5)
            canvas.create_text(x + 11, y, text=row["code"], anchor="w", fill=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"))

        canvas.create_text(w / 2, h - 12, text="Net influence", fill=COLOR_TEXT_LIGHT, font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(14, h / 2, text="Prominence", angle=90, fill=COLOR_TEXT_LIGHT, font=(FONT_FAMILY, FONT_SIZE_SMALL))

    def _relations_card(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Critical Relations", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 8))
        self._relation_list(card, "Strong Consensus Links", self._insights["agreement"]["strong_consensus"], _POS).pack(fill="x", padx=14, pady=(0, 10))
        self._relation_list(card, "Most Contested Links", self._insights["agreement"]["contested"], _NEG).pack(fill="x", padx=14, pady=(0, 12))
        return card

    def _relation_list(self, parent: tk.Frame, title: str, rows: List[dict], accent: str) -> tk.Frame:
        frame = tk.Frame(parent, bg=_CARD_BG)
        tk.Label(frame, text=title, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_CARD_BG, fg=accent).pack(anchor="w", pady=(0, 6))
        if not rows:
            tk.Label(frame, text="No relations available", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(anchor="w")
            return frame
        for row in rows:
            text = f"{row['pair']}  |  agree {row['agreement_ratio']:.2f}  |  spread {row['spread']:.2f}  |  agg {row['score']:+.2f}"
            tk.Label(frame, text=text, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, anchor="w", justify="left").pack(anchor="w", pady=2)
        return frame

    def _configuration_card(self, parent: tk.Frame) -> tk.Frame:
        graph = self._insights["graph"]
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Analysis Configuration", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 10))

        items = [
            ("Method", _method_label(self._result.method)),
            ("Policies", str(self._result.n)),
            ("Decision-makers", str(self._result.decision_makers)),
            ("Positive edges", str(graph["positive_edges"])),
            ("Negative edges", str(graph["negative_edges"])),
            ("Zero edges", str(graph["zero_edges"])),
            ("Polarity share", f"{graph['polarity']:.3f}"),
            ("Average agreement", f"{self._insights['agreement']['average_agreement']:.3f}"),
            ("Unresolved ties", str(len([tie for tie in self._result.ties if tie.chosen is None]))),
        ]

        for label, value in items:
            line = tk.Frame(card, bg=_CARD_BG)
            line.pack(fill="x", padx=14, pady=3)
            tk.Label(line, text=label, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="left")
            tk.Label(line, text=value, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_CARD_BG, fg=COLOR_ACCENT).pack(side="right")
        return card

    def _ranking_card(self, parent: tk.Frame) -> tk.Frame:
        rows = self._insights["top_prominence_rows"]
        max_value = max((row["prominence"] for row in rows), default=1.0) or 1.0

        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Prominence and Net Influence", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(card, text="Top policies by total influence load, with signed driver or dependency balance.", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, wraplength=360, justify="left").pack(anchor="w", padx=14, pady=(0, 12))
        for row in rows:
            self._ranking_row(card, row, max_value).pack(fill="x", padx=14, pady=5)
        return card

    def _ranking_row(self, parent: tk.Frame, row: dict, max_value: float) -> tk.Frame:
        outer = tk.Frame(parent, bg=_CARD_BG)
        tk.Label(outer, text=row["code"], width=6, anchor="w", font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_CARD_BG, fg=COLOR_ACCENT).pack(side="left")
        bar_host = tk.Frame(outer, bg="#eef2f4", height=12)
        bar_host.pack(side="left", fill="x", expand=True, padx=10)
        bar_host.pack_propagate(False)
        fill = tk.Frame(bar_host, bg=COLOR_ACCENT, height=12)
        fill.place(relx=0, rely=0, relheight=1, relwidth=max(0.03, row["prominence"] / max_value))
        metrics = f"P {row['prominence']:.2f}   N {row['net']:+.2f}"
        tk.Label(outer, text=metrics, width=18, anchor="e", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="right")
        return outer

    def _agreement_card(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Agreement and Sensitivity", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 6))
        tk.Label(card, text="Lowest agreement relations identify where the aggregate outcome is less stable across decision-makers.", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, wraplength=360, justify="left").pack(anchor="w", padx=14, pady=(0, 10))

        for row in self._insights["agreement"]["contested"][:4]:
            pill = tk.Frame(card, bg="#f7f8fa")
            pill.pack(fill="x", padx=14, pady=4)
            tone = _NEG if row["agreement_ratio"] < 0.6 else _MID
            tk.Label(pill, text=row["pair"], font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg="#f7f8fa", fg=COLOR_TEXT).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(pill, text=f"Agreement {row['agreement_ratio']:.2f}   Spread {row['spread']:.2f}   Aggregate {row['score']:+.2f}", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg="#f7f8fa", fg=tone).pack(anchor="w", padx=10, pady=(2, 8))
        return card

    def _format_policy(self, row: dict) -> str:
        if not row:
            return "N/A"
        return f"{row['code']}  {row['policy']}"

    def _format_metric(self, row: dict, key: str) -> str:
        if not row:
            return ""
        if key == "betweenness":
            return f"Betweenness {row[key]:.4f}"
        if key == "prominence":
            return f"Prominence {row[key]:.2f}"
        return f"Net influence {row[key]:+.2f}"

    def _format_pair(self, pair: Optional[Tuple[int, int]]) -> str:
        if not pair:
            return "No non-zero relation"
        i, j = pair
        return f"{self._result.codes[i]} -> {self._result.codes[j]}"

    def _value_text(self, row: Optional[dict], key: str) -> str:
        if not row:
            return "N/A"
        return f"{row[key]:.4f}" if key == "prominence" else f"{row[key]:+.4f}"
