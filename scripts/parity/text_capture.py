"""
Capture the legacy Results Insights texts and the AI prompt (plan Phase 2.2 and 2.5).

The story, interpretation, health and strongest-link helpers are called directly. Card texts come from the
legacy card builders: `ResultsInsightsTab` is built with `__new__`, `_signal_card` is patched to return its
arguments, and `tk.Label` inside `results_insights_tab` is replaced by a recorder for the two cards that build
labels directly (`_top_driver_card`, `_top_dependent_card`). Only the banner tags and the overview agreement value,
built inline in `_key_insight_main_card` / `_key_insight_stats_card`, are hand-copied below with their lines.
"""

from typing import Dict, List

import llm_tab
import results_insights_tab as rit


class _LabelRecorder:
    """Stands in for `tk.Label`: records the `text` of every label, in creation order."""

    def __init__(self, texts: List[str]) -> None:
        self._texts = texts

    def __call__(self, *_args, **kwargs):
        self._texts.append(kwargs.get("text"))
        return self

    def pack(self, *_args, **_kwargs) -> None:
        return None


class _FakeTk:
    """Replaces the `tk` module seen by `results_insights_tab` while a card builder runs."""

    def __init__(self, texts: List[str]) -> None:
        self.Label = _LabelRecorder(texts)


def _label_texts(tab, builder) -> List[str]:
    """Run a card builder that creates labels directly and return their texts."""
    texts: List[str] = []
    original = rit.tk
    rit.tk = _FakeTk(texts)
    try:
        builder(None)
    finally:
        rit.tk = original
    return texts


def _signal(*args, **kwargs) -> Dict:
    """Stands in for `_signal_card(parent, title, main, sub, color, bg, caption, ...)`."""
    _parent, title, main, sub, _colour, _bg, caption = args
    return {"title": title, "main": main, "value_text": sub, "caption": caption}


def card_texts(result, insights: Dict) -> Dict:
    """Texts of the five signal cards, captured from the legacy builders."""
    tab = rit.ResultsInsightsTab.__new__(rit.ResultsInsightsTab)
    tab._result = result
    tab._insights = insights
    tab._signal_card = _signal
    tab._card = lambda _parent, _bg=None: (None, None)
    driver = _label_texts(tab, tab._top_driver_card)
    dependent = _label_texts(tab, tab._top_dependent_card)
    return {
        "top_driver": {"hero": driver[0], "label": driver[1], "value_text": driver[2]},
        "top_dependent": {"hero": dependent[0], "label": dependent[1], "value_text": dependent[2]},
        "strongest_link": tab._strongest_link_card(None),
        "most_contested": tab._most_contested_card(None),
        "conflict_ratio": tab._conflict_ratio_card(None),
    }


def tag_texts(result, insights: Dict) -> Dict:
    """Hand-copied from `results_insights_tab.py:825-835` (inline `tk.Label` texts of the banner tags)."""
    tab = rit.ResultsInsightsTab.__new__(rit.ResultsInsightsTab)
    tab._result = result
    contested = insights["agreement"]["contested"]
    return {
        # :825
        "top_driver": f"Top Driving Policy: {tab._format_policy(insights['top_driver'])}",
        # :830
        "strongest_link": (
            f"Strongest Link: {tab._format_pair(insights['graph']['strongest_pos_pair']).replace('->', '→')}"
        ),
        # :835
        "contested": f"Contested: {(contested[0]['pair'].replace('->', '→') if contested else 'None')}",
    }


def overview_texts(insights: Dict) -> Dict:
    """Hand-copied from `results_insights_tab.py:879` (the Analysis Overview agreement value)."""
    return {"agreement": f"{insights['agreement']['average_agreement']:.2f}"}


def texts(result, insights: Dict, status: str) -> Dict:
    """Every displayed Results Insights text (raw legacy output, before label fixes) plus the status line."""
    top = insights["top_driver"]
    strongest = rit._strongest_link(result, top["index"]) if top else None
    return {
        "story": rit._build_story_banner(result, insights),
        "interpretation": rit._build_supporting_interpretation(insights),
        "health": rit._build_system_health(insights, result),
        "strongest_link": strongest,
        "cards": card_texts(result, insights),
        "tags": tag_texts(result, insights),
        "overview": overview_texts(insights),
        "status": status,
    }


def prompt(result) -> str:
    """`llm_tab.build_prompt(result)`."""
    return llm_tab.build_prompt(result)
