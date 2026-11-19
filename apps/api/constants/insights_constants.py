"""
Results Insights cut-offs, captions and labels (`results_insights_tab.py:503-509, 529-604, 953-1084`).

The texts are the legacy ones with label fixes L11 (one arrow), L12 (`Rating agreement`) and L13 (sign wording).
"""

INSIGHTS_THRESHOLDS = {
    "NET_CUTOFF": 0.05,
    "STABLE_AGREEMENT": 0.75,
    "WORKABLE_AGREEMENT": 0.5,
    "HIGH_DISAGREEMENT_RATIO": 0.5,
    "LOW_CONFLICT_RATIO": 0.2,
    "MODERATE_CONFLICT_RATIO": 0.4,
    "HEALTH_BASE": 50,
    "HEALTH_NEUTRAL_PENALTY": 0.35,
    "MAX_SCORE": 3,
    "CONTESTED_SHOWN": 5,
}

INSIGHTS_ARROWS = {"DIRECTED": "→", "UNDIRECTED": "↔"}

INSIGHTS_TEXT = {
    "INTERPRETATION_LABEL": "Interpretation:",
    "NOT_AVAILABLE": "N/A",
    "NO_RELATION": "No non-zero relation",
    "NO_CONTESTED_TAG": "None",
    "NO_CONTESTED_LINK": "No contested link",
    "NO_STRONG_LINK": "No strong link",
    "NO_STRONG_OUTGOING_LINK": "No strong outgoing link",
    "STABLE": "Stable",
    "STRONGEST_RELATION": "Strongest relation",
    "HIGH_DISAGREEMENT": "⚠ High disagreement",
    "MODERATE_DISAGREEMENT": "Moderate disagreement",
    "LOW_CONFLICT": "Low systemic conflict",
    "MODERATE_CONFLICT": "Moderate conflict pressure",
    "HIGH_CONFLICT": "High conflict pressure",
    "MOST_CONTESTED_VALUE_LABEL": "Rating agreement",
    "TAG_TOP_DRIVER": "Top Driving Policy: {value}",
    "TAG_STRONGEST_LINK": "Strongest Link: {value}",
    "TAG_CONTESTED": "Contested: {value}",
}

INTERPRETATIONS = {
    "STABLE_CONTESTED": "The system is relatively stable, but one important relation still lacks consensus.",
    "WORKABLE_CONTESTED": (
        "The system shows a workable pattern overall, though a few relations still need careful interpretation."
    ),
    "CONTESTED": "The system remains contested, so the strongest signals should be treated as provisional.",
    "STABLE": "The system is highly consistent across decision-makers, so the main structure looks robust.",
    "MODERATE": "The system is moderately stable, with some signals requiring additional scrutiny.",
}
