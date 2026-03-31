# =============================================================================
# Policy Coherence Kit -- results_insights_tab.py
# Extended dashboard-style summary tab shown before the detailed analysis tabs.
# =============================================================================

import math
import re
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
from theme import (
    RESULTS_CARD_BG as _CARD_BG,
    RESULTS_CARD_BORDER as _CARD_BORDER,
    RESULTS_CARD_RADIUS as _CARD_RADIUS,
    RESULTS_CARD_INSET as _CARD_INSET,
    RESULTS_CARD_GAP as _CARD_GAP,
    RESULTS_SCATTER_BG as _SCATTER_BG,
    RESULTS_SCATTER_BORDER as _SCATTER_BORDER,
    RESULTS_SCATTER_AXIS as _SCATTER_AXIS,
    RESULTS_SCATTER_GUIDE as _SCATTER_GUIDE,
    RESULTS_SCATTER_LABEL as _SCATTER_LABEL,
    RESULTS_SOFT_BG as _SOFT_BG,
    RESULTS_SOFT_BORDER as _SOFT_BORDER,
    RESULTS_TEAL_BAR as _TEAL_BAR,
    RESULTS_BANNER_BG as _BANNER_BG,
    RESULTS_BANNER_BORDER as _BANNER_BORDER,
    RESULTS_BANNER_LEFT_BG as _BANNER_LEFT_BG,
    RESULTS_BANNER_RIGHT_BG as _BANNER_RIGHT_BG,
    RESULTS_BANNER_TITLE_COLOR as _BANNER_TITLE_COLOR,
    RESULTS_BANNER_TITLE_SIZE as _BANNER_TITLE_SIZE,
    RESULTS_BANNER_TEXT_COLOR as _BANNER_TEXT_COLOR,
    RESULTS_BANNER_TEXT_SIZE as _BANNER_TEXT_SIZE,
    RESULTS_BANNER_EMPH_COLOR as _BANNER_EMPH_COLOR,
    RESULTS_BANNER_RELATION_COLOR as _BANNER_RELATION_COLOR,
    RESULTS_BANNER_SUPPORTING_WRAP as _BANNER_SUPPORTING_WRAP,
    RESULTS_BANNER_OUTER_PADX as _BANNER_OUTER_PADX,
    RESULTS_BANNER_OUTER_PADY as _BANNER_OUTER_PADY,
    RESULTS_BANNER_COLUMN_GAP as _BANNER_COLUMN_GAP,
    RESULTS_BANNER_TITLE_GAP as _BANNER_TITLE_GAP,
    RESULTS_BANNER_TEXT_GAP as _BANNER_TEXT_GAP,
    RESULTS_BANNER_SUPPORTING_BOTTOM as _BANNER_SUPPORTING_BOTTOM,
    RESULTS_BANNER_INTERPRETATION_LABEL as _BANNER_INTERPRETATION_LABEL,
    RESULTS_BANNER_INTERPRETATION_TEXT as _BANNER_INTERPRETATION_TEXT,
    RESULTS_BANNER_STATS_PADX as _BANNER_STATS_PADX,
    RESULTS_BANNER_STATS_TOP as _BANNER_STATS_TOP,
    RESULTS_BANNER_STATS_GAP as _BANNER_STATS_GAP,
    RESULTS_BANNER_STATS_BOTTOM as _BANNER_STATS_BOTTOM,
    RESULTS_BANNER_META_HEIGHT as _BANNER_META_HEIGHT,
    RESULTS_BANNER_META_RADIUS as _BANNER_META_RADIUS,
    RESULTS_BANNER_META_TEXT_SIZE as _BANNER_META_TEXT_SIZE,
    RESULTS_BANNER_STAT_HEIGHT_DELTA as _BANNER_STAT_HEIGHT_DELTA,
    RESULTS_BANNER_TAG_HEIGHT as _BANNER_TAG_HEIGHT,
    RESULTS_BANNER_TAG_RADIUS as _BANNER_TAG_RADIUS,
    RESULTS_BANNER_TAG_TEXT_SIZE as _BANNER_TAG_TEXT_SIZE,
    RESULTS_BANNER_TAG_TOP_DRIVER_BG as _BANNER_TAG_TOP_DRIVER_BG,
    RESULTS_BANNER_TAG_TOP_DRIVER_FG as _BANNER_TAG_TOP_DRIVER_FG,
    RESULTS_BANNER_TAG_STRONGEST_BG as _BANNER_TAG_STRONGEST_BG,
    RESULTS_BANNER_TAG_STRONGEST_FG as _BANNER_TAG_STRONGEST_FG,
    RESULTS_BANNER_TAG_CONTESTED_BG as _BANNER_TAG_CONTESTED_BG,
    RESULTS_BANNER_TAG_CONTESTED_FG as _BANNER_TAG_CONTESTED_FG,
    RESULTS_BANNER_METHOD_BG as _BANNER_METHOD_BG,
    RESULTS_BANNER_METHOD_FG as _BANNER_METHOD_FG,
    RESULTS_BANNER_POLICIES_BG as _BANNER_POLICIES_BG,
    RESULTS_BANNER_POLICIES_FG as _BANNER_POLICIES_FG,
    RESULTS_BANNER_DMS_BG as _BANNER_DMS_BG,
    RESULTS_BANNER_DMS_FG as _BANNER_DMS_FG,
    RESULTS_HEALTH_BAR_BG as _HEALTH_BAR_BG,
    RESULTS_LINK_COLOR as _LINK_COLOR,
    RESULTS_AGREEMENT_ACCENT as _AGREEMENT_ACCENT,
    RESULTS_CONFIG_PILL_FG as _CONFIG_PILL_FG,
    RESULTS_PROMINENCE_BAR_BG as _PROMINENCE_BAR_BG,
    RESULTS_RANKING_BAR_BG as _RANKING_BAR_BG,
    RESULTS_HEATMAP_BG as _HEATMAP_BG,
    RESULTS_HEATMAP_DIAGONAL as _HEATMAP_DIAGONAL,
    RESULTS_CANVAS_LIGHT_TEXT as _CANVAS_LIGHT_TEXT,
    RESULTS_ON_ACCENT_TEXT as _ON_ACCENT_TEXT,
    RESULTS_DRIVER as _DRIVER,
    RESULTS_DEPENDENT as _DEPENDENT,
    RESULTS_BALANCED as _BALANCED,
    RESULTS_HEAT_LOW as _HEAT_LOW,
    RESULTS_HEAT_HIGH as _HEAT_HIGH,
    RESULTS_SURFACE as _SURFACE,
    RESULTS_SOFT_RED as _SOFT_RED,
    RESULTS_SOFT_GREEN as _SOFT_GREEN,
    RESULTS_SOFT_ORANGE as _SOFT_ORANGE,
    RESULTS_SOFT_BLUE as _SOFT_BLUE,
    RESULTS_SOFT_PURPLE as _SOFT_PURPLE,
    RESULTS_POSITIVE as _POS,
    RESULTS_NEGATIVE as _NEG,
    RESULTS_MID as _MID,
)


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


def _hex_interp(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _rrect_pts(x1: float, y1: float, x2: float, y2: float, r: float, steps: int = 10) -> List[float]:
    pts = []
    for cx, cy, a0 in [
        (x2 - r, y1 + r, -90),
        (x2 - r, y2 - r, 0),
        (x1 + r, y2 - r, 90),
        (x1 + r, y1 + r, 180),
    ]:
        for i in range(steps + 1):
            a = math.radians(a0 + 90 * i / steps)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


class _RoundedCard(tk.Canvas):
    def __init__(self, parent, bg: str, radius: int = _CARD_RADIUS, border: Optional[str] = None, border_width: int = 0):
        super().__init__(parent, bg=COLOR_BG, highlightthickness=0, bd=0)
        self._fill = bg
        self._radius = radius
        self._border = border or bg
        self._border_width = border_width
        self._initial_height_locked = False
        self._body = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self._window = self.create_window(0, 0, window=self._body, anchor="nw")
        self.bind("<Configure>", self._redraw)
        self._body.bind("<Configure>", self._sync_body)

    @property
    def body(self) -> tk.Frame:
        return self._body

    def _sync_body(self, _event=None):
        # Lock the canvas height from the initial content request, then let the
        # parent grid own later sizing so cards cannot keep pushing the page
        # beyond the available analysis viewport.
        if not self._initial_height_locked:
            req_h = self._body.winfo_reqheight() + (_CARD_INSET * 2)
            current_h = int(self.cget("height")) if str(self.cget("height")).isdigit() else 0
            self.configure(height=max(req_h, current_h))
            self._initial_height_locked = True
        self._redraw()

    def _redraw(self, _event=None):
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1:
            width = self._body.winfo_reqwidth() + (_CARD_INSET * 2)
        if height <= 1:
            height = self._body.winfo_reqheight() + (_CARD_INSET * 2)
        self.delete("card_bg")
        pts = _rrect_pts(1, 1, width - 1, height - 1, self._radius)
        self.create_polygon(
            *pts,
            fill=self._fill,
            outline=self._border,
            width=self._border_width,
            smooth=True,
            tags="card_bg",
        )
        self.tag_lower("card_bg")
        self.coords(self._window, _CARD_INSET, _CARD_INSET)
        self.itemconfigure(
            self._window,
            width=max(1, width - (_CARD_INSET * 2)),
            height=max(1, height - (_CARD_INSET * 2)),
        )


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


def _role_for_row(row: dict) -> Tuple[str, str, str]:
    net = row["net"]
    if net > 0.05:
        return "Strategic Driver", _DRIVER, "↑"
    if net < -0.05:
        return "System Dependent", _DEPENDENT, "↓"
    return "Balanced Node", _BALANCED, "•"


def _strongest_link(result: AggregationResult, row_index: int) -> Tuple[str, float]:
    best_pair = None
    best_score = 0.0
    for j in range(result.n):
        if j == row_index:
            continue
        score = result.scores.get((row_index, j), 0.0) or 0.0
        if abs(score) > abs(best_score):
            best_score = score
            best_pair = (row_index, j)
    if best_pair is None:
        return "No strong outgoing link", 0.0
    _, j = best_pair
    tone = "Reinforcing" if best_score > 0 else "Constraining"
    return f"{result.codes[row_index]} -> {result.codes[j]} ({best_score:+.2f} {tone})", best_score


def _build_story_banner(result: AggregationResult, insights: Dict[str, object]) -> str:
    top_driver = insights["top_driver"]
    contested = insights["agreement"]["contested"][0] if insights["agreement"]["contested"] else None
    if not top_driver:
        return "The current result set is too sparse to describe a clear system story."
    link_text, score = _strongest_link(result, top_driver["index"])
    stable_phrase = "stable" if insights["agreement"]["average_agreement"] >= 0.75 else "not yet fully stable"
    if contested:
        return (
            f"{top_driver['code']} emerges as the principal driver shaping the system, exerting its strongest influence "
            f"through the {'reinforcing' if score > 0 else 'constraining'} relationship {link_text}, which indicates a "
            f"{stable_phrase} and structurally significant interaction. In contrast, the linkage "
            f"{contested['pair']} remains contested across decision-makers, reflecting a lack of consensus and "
            f"highlighting an area of uncertainty within the system."
        )
    if abs(score) > 0:
        return (
            f"{top_driver['code']} emerges as the principal driver shaping the system, exerting its strongest influence "
            f"through the {'reinforcing' if score > 0 else 'constraining'} relationship {link_text}, which indicates a "
            f"{stable_phrase} and structurally significant interaction. At the same time, the broader pattern shows "
            f"an average agreement level of {insights['agreement']['average_agreement']:.2f}, suggesting that the "
            f"dominant structure is interpretable with reasonable confidence."
        )
    return (
        f"{top_driver['code']} emerges as the principal driver shaping the system, but no single outgoing relationship "
        f"yet dominates strongly enough to define the structure on its own. This suggests the system remains diffuse, "
        f"with influence spread across multiple pathways that should be interpreted with care."
    )


def _build_system_health(insights: Dict[str, object], result: AggregationResult) -> Dict[str, int]:
    graph = insights["graph"]
    max_edges = max(1, result.n * (result.n - 1))
    synergy = round((graph["positive_edges"] / max_edges) * 100)
    conflict = round((graph["negative_edges"] / max_edges) * 100)
    uncertainty = round((1 - insights["agreement"]["average_agreement"]) * 100)
    score = max(0, min(100, 50 + synergy - conflict - round(uncertainty * 0.7)))
    return {
        "score": score,
        "synergy": synergy,
        "conflict": conflict,
        "uncertainty": uncertainty,
    }


def _build_supporting_interpretation(insights: Dict[str, object]) -> str:
    contested = insights["agreement"]["contested"][0] if insights["agreement"]["contested"] else None
    agreement = insights["agreement"]["average_agreement"]
    if contested and agreement >= 0.75:
        return "Interpretation: The system is relatively stable, but one important relation still lacks consensus."
    if contested and agreement >= 0.5:
        return "Interpretation: The system shows a workable pattern overall, though a few relations still need careful interpretation."
    if contested:
        return "Interpretation: The system remains contested, so the strongest signals should be treated as provisional."
    if agreement >= 0.75:
        return "Interpretation: The system is highly consistent across decision-makers, so the main structure looks robust."
    return "Interpretation: The system is moderately stable, with some signals requiring additional scrutiny."


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
            "index": idx,
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
        self._story = _build_story_banner(result, self._insights)
        self._health = _build_system_health(self._insights, result)
        self._build()

    def _build(self):
        for child in self.winfo_children():
            child.destroy()
        page = tk.Frame(self, bg=COLOR_BG)
        page.pack(fill="both", expand=True, padx=24, pady=(24, 0))

        shell = tk.Frame(page, bg=COLOR_BG)
        shell.pack(fill="both", expand=True, pady=(0, 12))
        for col in range(3):
            shell.grid_columnconfigure(col, weight=1, uniform="insights")
        shell.grid_rowconfigure(0, weight=2, uniform="insight-rows")
        shell.grid_rowconfigure(1, weight=1, uniform="insight-rows")
        shell.grid_rowconfigure(2, weight=1, uniform="insight-rows")

        self._build_key_insight(shell, row=0)
        self._build_primary_signal_row(shell, row=1)
        self._build_secondary_signal_row(shell, row=2)

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

    def _card(self, parent: tk.Frame, bg: str = _CARD_BG) -> Tuple[_RoundedCard, tk.Frame]:
        card = _RoundedCard(parent, bg=bg, radius=_CARD_RADIUS)
        return card, card.body

    def _build_key_insight(self, parent: tk.Frame, row: int):
        section = tk.Frame(parent, bg=COLOR_BG)
        section.grid(row=row, column=0, columnspan=3, sticky="nsew")
        gap = _CARD_GAP // 2
        section.grid_columnconfigure(0, weight=1, uniform="key-insight")
        section.grid_columnconfigure(1, weight=1, uniform="key-insight")
        section.grid_rowconfigure(0, weight=1)
        self._key_insight_main_card(section).grid(row=0, column=0, sticky="nsew", padx=gap, pady=gap)
        self._key_insight_stats_card(section).grid(row=0, column=1, sticky="nsew", padx=gap, pady=gap)

    def _build_primary_signal_row(self, parent: tk.Frame, row: int):
        gap = _CARD_GAP // 2
        self._system_health_card(parent).grid(row=row, column=0, sticky="nsew", padx=gap, pady=gap)
        self._top_driver_card(parent).grid(row=row, column=1, sticky="nsew", padx=gap, pady=gap)
        self._top_dependent_card(parent).grid(row=row, column=2, sticky="nsew", padx=gap, pady=gap)

    def _build_secondary_signal_row(self, parent: tk.Frame, row: int):
        gap = _CARD_GAP // 2
        self._strongest_link_card(parent).grid(row=row, column=0, sticky="nsew", padx=gap, pady=gap)
        self._most_contested_card(parent).grid(row=row, column=1, sticky="nsew", padx=gap, pady=gap)
        self._agreement_score_card(parent).grid(row=row, column=2, sticky="nsew", padx=gap, pady=gap)

    def _key_insight_main_card(self, parent: tk.Frame) -> tk.Frame:
        card = _RoundedCard(parent, bg=_BANNER_LEFT_BG, radius=_CARD_RADIUS, border=_BANNER_LEFT_BG, border_width=1)
        body = card.body
        policy_colors = {row["code"]: _role_for_row(row)[1] for row in self._insights["rows"]}
        pad_x = _BANNER_OUTER_PADX
        pad_y = _BANNER_OUTER_PADY
        title_gap = _BANNER_TITLE_GAP
        text_gap = _BANNER_TEXT_GAP
        supporting_gap = _BANNER_SUPPORTING_BOTTOM
        top = tk.Frame(body, bg=_BANNER_LEFT_BG)
        top.pack(fill="x", anchor="n")
        tk.Label(
            top,
            text="Key Insights",
            font=(FONT_FAMILY, _BANNER_TITLE_SIZE, "normal"),
            bg=_BANNER_LEFT_BG,
            fg=_BANNER_TITLE_COLOR,
        ).pack(anchor="w", padx=pad_x, pady=(pad_y, title_gap))
        story = tk.Text(
            top,
            height=6,
            wrap="word",
            bg=_BANNER_LEFT_BG,
            fg=_BANNER_TEXT_COLOR,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(FONT_FAMILY, _BANNER_TEXT_SIZE, "normal"),
        )
        story.pack(fill="x", padx=pad_x, pady=(0, text_gap))
        story.insert("1.0", self._story)
        story_text = self._story
        relation_pattern = r"P\d+\s*->\s*P\d+(?:\s*\([^)]+\))?"
        relation_ranges = []
        for match in re.finditer(relation_pattern, story_text):
            relation_ranges.append((match.start(), match.end()))
            story.tag_add("relation", f"1.{match.start()}", f"1.{match.end()}")
        for match in re.finditer(r"P\d+\b", story_text):
            if any(start <= match.start() and match.end() <= end for start, end in relation_ranges):
                continue
            code = match.group(0)
            tag = f"policy_{code}"
            story.tag_add(tag, f"1.{match.start()}", f"1.{match.end()}")
            story.tag_configure(
                tag,
                foreground=policy_colors.get(code, _BANNER_EMPH_COLOR),
                font=(FONT_FAMILY, _BANNER_TEXT_SIZE, "bold"),
            )
        story.tag_configure(
            "relation",
            foreground=_BANNER_RELATION_COLOR,
            font=(FONT_FAMILY, _BANNER_TEXT_SIZE, "bold"),
        )
        story.configure(state="disabled")

        interpretation = _build_supporting_interpretation(self._insights)
        prefix = "Interpretation:"
        detail = interpretation[len(prefix):].lstrip() if interpretation.startswith(prefix) else interpretation
        bottom = tk.Frame(body, bg=_BANNER_LEFT_BG)
        bottom.pack(fill="x", side="bottom")
        supporting = tk.Frame(bottom, bg=_BANNER_LEFT_BG)
        supporting.pack(anchor="w", fill="x", padx=pad_x, pady=(0, 8))
        tk.Label(
            supporting,
            text=prefix,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "normal"),
            bg=_BANNER_LEFT_BG,
            fg=_BANNER_INTERPRETATION_LABEL,
        ).pack(side="left")
        tk.Label(
            supporting,
            text=f" {detail}",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "normal"),
            bg=_BANNER_LEFT_BG,
            fg=_BANNER_INTERPRETATION_TEXT,
            wraplength=_BANNER_SUPPORTING_WRAP,
            justify="left",
        ).pack(side="left")

        tags = tk.Frame(bottom, bg=_BANNER_LEFT_BG)
        tags.pack(fill="x", padx=pad_x, pady=(0, pad_y))
        tags.grid_rowconfigure(0, minsize=_BANNER_TAG_HEIGHT)
        for col in range(3):
            tags.grid_columnconfigure(col, weight=1, uniform="insight-tags")
        tag_items = [
            (
                f"Top Driver: {self._insights['top_driver']['code'] if self._insights['top_driver'] else 'N/A'}",
                _BANNER_TAG_TOP_DRIVER_BG,
                _BANNER_TAG_TOP_DRIVER_FG,
            ),
            (
                f"Strongest Link: {self._format_pair(self._insights['graph']['strongest_pos_pair']).replace('->', '→')}",
                _BANNER_TAG_STRONGEST_BG,
                _BANNER_TAG_STRONGEST_FG,
            ),
            (
                f"Contested: {(self._insights['agreement']['contested'][0]['pair'].replace('->', '→') if self._insights['agreement']['contested'] else 'None')}",
                _BANNER_TAG_CONTESTED_BG,
                _BANNER_TAG_CONTESTED_FG,
            ),
        ]
        for idx, (text, bg, fg) in enumerate(tag_items):
            tag = tk.Frame(tags, bg=bg, highlightthickness=0, bd=0, height=_BANNER_TAG_HEIGHT)
            tag.grid_propagate(False)
            row = 0
            col = idx
            colspan = 1
            tag.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=4, pady=(0, 4))
            tk.Label(
                tag,
                text=text,
                font=(FONT_FAMILY, _BANNER_TAG_TEXT_SIZE, "normal"),
                bg=bg,
                fg=fg,
                wraplength=180,
                justify="center",
            ).pack(expand=True, fill="both", padx=10)
        return card

    def _key_insight_stats_card(self, parent: tk.Frame) -> tk.Frame:
        card = _RoundedCard(parent, bg=_BANNER_RIGHT_BG, radius=_CARD_RADIUS, border=_BANNER_RIGHT_BG, border_width=1)
        body = card.body
        pad_x = _BANNER_OUTER_PADX
        pad_y = _BANNER_OUTER_PADY
        title_gap = _BANNER_TITLE_GAP
        row_gap = 16
        value_width = 160

        tk.Label(
            body,
            text="Analysis Overview",
            font=(FONT_FAMILY, _BANNER_TITLE_SIZE, "normal"),
            bg=_BANNER_RIGHT_BG,
            fg=_BANNER_TITLE_COLOR,
        ).pack(anchor="w", padx=pad_x, pady=(pad_y, title_gap))

        stats = [
            (str(self._result.n), "Policies", "#1D4ED8", "#475569"),
            (str(self._result.decision_makers), "Decision-makers", "#0F766E", "#475569"),
            (_method_label(self._result.method), "Method", "#7C3AED", "#475569"),
            (f"{self._insights['agreement']['average_agreement']:.2f}", "Agreement", "#059669", "#475569"),
        ]
        for idx, (value, label, value_fg, label_fg) in enumerate(stats):
            row = tk.Frame(body, bg=_BANNER_RIGHT_BG)
            row.pack(
                anchor="w",
                fill="x",
                padx=pad_x,
                pady=(0, row_gap if idx < len(stats) - 1 else pad_y),
            )
            row.grid_columnconfigure(0, minsize=value_width)
            row.grid_columnconfigure(1, weight=1)
            tk.Label(
                row,
                text=value,
                font=(FONT_FAMILY, 30, "bold"),
                bg=_BANNER_RIGHT_BG,
                fg=value_fg,
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            tk.Label(
                row,
                text=label,
                font=(FONT_FAMILY, 10, "normal"),
                bg=_BANNER_RIGHT_BG,
                fg=label_fg,
                anchor="w",
            ).grid(row=0, column=1, sticky="w")
        return card

    def _system_health_card(self, parent: tk.Frame) -> tk.Frame:
        card, body = self._card(parent, _SURFACE)
        tk.Label(body, text="System Health", font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_SURFACE, fg=COLOR_TEXT_LIGHT).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(body, text=f"{self._health['score']}", font=(FONT_FAMILY, FONT_SIZE_HEADER + 18, "bold"), bg=_SURFACE, fg=COLOR_ACCENT).pack(anchor="w", padx=16)
        for label, value, color in [
            ("Synergy", self._health["synergy"], _DRIVER),
            ("Conflict", self._health["conflict"], _NEG),
            ("Uncertainty", self._health["uncertainty"], _MID),
        ]:
            row = tk.Frame(body, bg=_SURFACE)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=label, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_SURFACE, fg=COLOR_TEXT_LIGHT, width=11, anchor="w").pack(side="left")
            bar = tk.Frame(row, bg=_HEALTH_BAR_BG, height=8)
            bar.pack(side="left", fill="x", expand=True, padx=(6, 8))
            bar.pack_propagate(False)
            tk.Frame(bar, bg=color, height=8).place(relx=0, rely=0, relheight=1, relwidth=max(0.03, min(1.0, value / 100)))
            tk.Label(row, text=f"{value}", font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_SURFACE, fg=color, width=4, anchor="e").pack(side="left")
        return card

    def _top_driver_card(self, parent: tk.Frame) -> tk.Frame:
        row = self._insights["top_driver"]
        return self._metric_signal_card(parent, row["code"] if row else "N/A", "Top Driver", f"{row['net']:+.2f} ↑" if row else "N/A", _DRIVER, _SOFT_GREEN)

    def _top_dependent_card(self, parent: tk.Frame) -> tk.Frame:
        row = self._insights["top_dependent"]
        return self._metric_signal_card(parent, row["code"] if row else "N/A", "Most Dependent", f"{row['net']:+.2f} ↓" if row else "N/A", _DEPENDENT, _SOFT_ORANGE)

    def _strongest_link_card(self, parent: tk.Frame) -> tk.Frame:
        graph = self._insights["graph"]
        pair = self._format_pair(graph["strongest_pos_pair"])
        value = f"{graph['strongest_pos']:+.2f} Reinforcing" if graph["strongest_pos_pair"] else "No strong link"
        return self._signal_card(parent, "Strongest Link", pair, value, _LINK_COLOR, _SOFT_BLUE, "Strongest relation")

    def _most_contested_card(self, parent: tk.Frame) -> tk.Frame:
        contested = self._insights["agreement"]["contested"][0] if self._insights["agreement"]["contested"] else None
        main = contested["pair"].replace("->", "↔") if contested else "No contested link"
        sub = f"Agreement: {contested['agreement_ratio']:.2f}" if contested else "Stable"
        caption = "⚠ High disagreement" if contested and contested["agreement_ratio"] < 0.5 else "Moderate disagreement"
        return self._signal_card(parent, "Most Contested", main, sub, _NEG, _SOFT_RED, caption)

    def _agreement_score_card(self, parent: tk.Frame) -> tk.Frame:
        score = self._insights["agreement"]["average_agreement"]
        if score >= 0.75:
            label = "Strong consensus"
        elif score >= 0.5:
            label = "Moderate consensus"
        else:
            label = "Low consensus"
        return self._metric_signal_card(parent, f"{score:.2f}", "Agreement Level", label, _AGREEMENT_ACCENT, _SOFT_PURPLE)

    def _analysis_config_card(self, parent: tk.Frame) -> tk.Frame:
        card, body = self._card(parent, _CARD_BG)
        tk.Label(body, text="Analysis Config", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=18, pady=(14, 10))
        wrap = _WrapFrame(body, bg=_CARD_BG, gap=8, row_gap=10)
        wrap.pack(fill="x", padx=18, pady=(0, 18))
        tags = [
            f"Method: {_method_label(self._result.method)}",
            f"Policies: {self._result.n}",
            f"DMs: {self._result.decision_makers}",
            f"Density: {self._insights['graph']['density']:.2f}",
            f"Agreement: {self._insights['agreement']['average_agreement']:.2f}",
        ]
        for text in tags:
            pill = tk.Label(wrap, text=text, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_SURFACE, fg=_CONFIG_PILL_FG, padx=12, pady=7)
            wrap.add(pill)
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
                bg=accent, fg=_ON_ACCENT_TEXT,
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
            bar_host = tk.Frame(line, bg=_PROMINENCE_BAR_BG, height=8)
            bar_host.pack(side="left", fill="x", expand=True, padx=8)
            bar_host.pack_propagate(False)
            tk.Frame(bar_host, bg=_TEAL_BAR, height=8).place(relx=0, rely=0, relheight=1, relwidth=max(0.04, row["prominence"] / max_value))
            tk.Label(line, text=f"P {row['prominence']:.4f}", width=10, anchor="e", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="left", padx=(8, 4))
            tk.Label(line, text=f"R {row['net']:+.4f}", width=10, anchor="e", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="left")
        return frame

    def _mini_stat_card(self, parent: tk.Frame, title: str, value: str, caption: str) -> tk.Frame:
        card = tk.Frame(parent, bg=_SOFT_BG, highlightbackground=_SOFT_BORDER, highlightthickness=1)
        tk.Label(card, text=title, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_SOFT_BG, fg=COLOR_TEXT_LIGHT, anchor="w").pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(card, text=value, font=(FONT_FAMILY, FONT_SIZE_HEADER + 5, "bold"), bg=_SOFT_BG, fg=COLOR_ACCENT, anchor="w").pack(fill="x", padx=12)
        tk.Label(card, text=caption, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_SOFT_BG, fg=COLOR_TEXT_LIGHT, wraplength=220, justify="left", anchor="w").pack(fill="x", padx=12, pady=(8, 12))
        return card

    def _build_analysis_grid(self, parent: tk.Frame, row: int):
        pass

    def _build_heatmap_section(self, parent: tk.Frame, row: int):
        pass

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
            text="X-axis shows net influence. Y-axis shows prominence. Drivers sit on the right, dependents on the left, and higher positions indicate stronger system visibility.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, wraplength=980, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))
        canvas = tk.Canvas(card, bg=_SCATTER_BG, width=980, height=260, highlightthickness=1, highlightbackground=_SCATTER_BORDER)
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

        canvas.create_line(m, h - m, w - m, h - m, fill=_SCATTER_AXIS)
        canvas.create_line(m, m, m, h - m, fill=_SCATTER_AXIS)
        canvas.create_line(sx(0.0), m, sx(0.0), h - m, fill=_SCATTER_GUIDE, dash=(4, 4))
        canvas.create_line(m, sy(self._insights["quadrant_threshold"]), w - m, sy(self._insights["quadrant_threshold"]), fill=_SCATTER_GUIDE, dash=(4, 4))
        canvas.create_text(w - m - 56, m + 8, text="Drivers", anchor="nw", fill=_SCATTER_LABEL, font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(m + 8, m + 8, text="Dependents", anchor="nw", fill=_SCATTER_LABEL, font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(w - m - 62, h - m - 20, text="Strategic", anchor="nw", fill=_SCATTER_LABEL, font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(m + 8, h - m - 20, text="Vulnerable", anchor="nw", fill=_SCATTER_LABEL, font=(FONT_FAMILY, FONT_SIZE_SMALL))

        for row in rows:
            x = sx(row["net"])
            y = sy(row["prominence"])
            color = _role_for_row(row)[1]
            canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=color, outline=_CANVAS_LIGHT_TEXT, width=1.5)
            canvas.create_text(x + 11, y, text=row["code"], anchor="w", fill=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"))

        canvas.create_text(w / 2, h - 12, text="Net influence", fill=COLOR_TEXT_LIGHT, font=(FONT_FAMILY, FONT_SIZE_SMALL))
        canvas.create_text(14, h / 2, text="Prominence", angle=90, fill=COLOR_TEXT_LIGHT, font=(FONT_FAMILY, FONT_SIZE_SMALL))

    def _relations_card(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Critical Relations", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 8))
        self._relation_list(card, "Strong Consensus Links", self._insights["agreement"]["strong_consensus"], _POS).pack(fill="x", padx=14, pady=(0, 10))
        self._relation_list(card, "Most Contested Links", self._insights["agreement"]["contested"], _NEG).pack(fill="x", padx=14, pady=(0, 12))
        return card

    def _agreement_heatmap_card(self, parent: tk.Frame) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_CARD_BORDER, highlightthickness=1)
        tk.Label(card, text="Conflict and Consensus Heatmap", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(card, text="Dark cells indicate strong agreement. Lighter cells flag contested policy relationships.", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT, wraplength=980, justify="left").pack(anchor="w", padx=14, pady=(0, 10))
        canvas = tk.Canvas(card, bg=_HEATMAP_BG, width=980, height=190, highlightthickness=1, highlightbackground=_SCATTER_BORDER)
        canvas.pack(fill="x", padx=14, pady=(0, 12))
        self._draw_agreement_heatmap(canvas)
        return card

    def _draw_agreement_heatmap(self, canvas: tk.Canvas):
        n = self._result.n
        if n <= 0:
            return
        w = int(canvas.cget("width"))
        h = int(canvas.cget("height"))
        label_w = 54
        label_h = 24
        cell = min((w - label_w - 16) / max(1, n), (h - label_h - 16) / max(1, n))
        x0 = label_w
        y0 = label_h
        agreement_map = {(row["i"], row["j"]): row["agreement_ratio"] for row in self._insights["agreement"]["rows"]}

        for idx, code in enumerate(self._result.codes):
            cx = x0 + idx * cell + cell / 2
            cy = y0 + idx * cell + cell / 2
            canvas.create_text(cx, 12, text=code, fill=COLOR_TEXT_LIGHT, font=(FONT_FAMILY, FONT_SIZE_SMALL))
            canvas.create_text(18, cy, text=code, fill=COLOR_TEXT_LIGHT, font=(FONT_FAMILY, FONT_SIZE_SMALL))

        for i in range(n):
            for j in range(n):
                x1 = x0 + j * cell
                y1 = y0 + i * cell
                x2 = x1 + cell
                y2 = y1 + cell
                if i == j:
                    fill = _HEATMAP_DIAGONAL
                    label = "—"
                else:
                    ratio = agreement_map.get((i, j), 0.0)
                    fill = _hex_interp(_HEAT_LOW, _HEAT_HIGH, ratio)
                    label = f"{ratio:.2f}"
                canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=_CANVAS_LIGHT_TEXT, width=1)
                canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=_CANVAS_LIGHT_TEXT if i != j and agreement_map.get((i, j), 0.0) > 0.58 else COLOR_TEXT, font=(FONT_FAMILY, 9, "bold" if i != j else "normal"))

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
        tk.Label(card, text="System Overview", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=14, pady=(12, 10))

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

    def _ranking_card(self, parent: tk.Frame, compact: bool = False) -> tk.Frame:
        rows = self._insights["top_prominence_rows"]
        max_value = max((row["prominence"] for row in rows), default=1.0) or 1.0

        card, body = self._card(parent, _CARD_BG)
        tk.Label(body, text="Prominence Ranking", font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"), bg=_CARD_BG, fg=COLOR_TEXT).pack(anchor="w", padx=18, pady=(14, 6))
        tk.Label(body, text="Top 4 policies by prominence.", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(anchor="w", padx=18, pady=(0, 10))
        for row in rows[:4]:
            self._ranking_row(body, row, max_value, compact=compact).pack(fill="x", padx=18, pady=4)
        return card

    def _ranking_row(self, parent: tk.Frame, row: dict, max_value: float, compact: bool = False) -> tk.Frame:
        outer = tk.Frame(parent, bg=_CARD_BG)
        role_label, color, arrow = _role_for_row(row)
        tk.Label(outer, text=f"{arrow} {row['code']}", width=7, anchor="w", font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=_CARD_BG, fg=color).pack(side="left")
        bar_h = 6 if compact else 8
        bar_host = tk.Frame(outer, bg=_RANKING_BAR_BG, height=bar_h)
        bar_host.pack(side="left", fill="x", expand=True, padx=10)
        bar_host.pack_propagate(False)
        fill = tk.Frame(bar_host, bg=color, height=bar_h)
        fill.place(relx=0, rely=0, relheight=1, relwidth=max(0.03, row["prominence"] / max_value))
        metrics = f"P {row['prominence']:.2f}"
        tk.Label(outer, text=metrics, width=9, anchor="e", font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=_CARD_BG, fg=COLOR_TEXT_LIGHT).pack(side="right")
        return outer

    def _metric_signal_card(self, parent: tk.Frame, hero: str, label: str, value: str, color: str, bg: str) -> tk.Frame:
        card, body = self._card(parent, bg)
        tk.Label(body, text=hero, font=(FONT_FAMILY, FONT_SIZE_HEADER + 6, "bold"), bg=bg, fg=COLOR_TEXT).pack(anchor="w", padx=16, pady=(16, 4))
        tk.Label(body, text=label, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=bg, fg=COLOR_TEXT_LIGHT).pack(anchor="w", padx=16)
        tk.Label(body, text=value, font=(FONT_FAMILY, FONT_SIZE_HEADER + 2, "bold"), bg=bg, fg=color).pack(anchor="w", padx=16, pady=(10, 16))
        return card

    def _signal_card(self, parent: tk.Frame, title: str, main: str, sub: str, color: str, bg: str, caption: str) -> tk.Frame:
        card, body = self._card(parent, bg)
        wrap = 240
        tk.Label(body, text=title, font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"), bg=bg, fg=color).pack(anchor="w", padx=16, pady=(16, 6))
        tk.Label(body, text=main, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), bg=bg, fg=COLOR_TEXT, justify="left", wraplength=wrap).pack(anchor="w", padx=16)
        tk.Label(body, text=sub, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), bg=bg, fg=color, justify="left", wraplength=wrap).pack(anchor="w", padx=16, pady=(8, 2))
        tk.Label(body, text=caption, font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=bg, fg=COLOR_TEXT_LIGHT).pack(anchor="w", padx=16, pady=(0, 16))
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
