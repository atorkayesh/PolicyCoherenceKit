"""
Coherence rating scale, verbatim from the legacy `constants.py:14-49, 92-100` and `aggregation_tab.py:59-67`.

The order matters: most synergistic first, most conflicting last (drop-down, legend and error texts use it).
"""

from typing import Dict, List

RATING_LABELS: List[str] = [
    "Indivisible",
    "Reinforcing",
    "Enabling",
    "Neutral",
    "Constraining",
    "Counteracting",
    "Cancelling",
]

DIAGONAL_LABEL = "Neutral"

RATING_SCORES: Dict[str, int] = {
    "Indivisible": 3,
    "Reinforcing": 2,
    "Enabling": 1,
    "Neutral": 0,
    "Constraining": -1,
    "Counteracting": -2,
    "Cancelling": -3,
}

RATING_FILLS: Dict[str, str] = {
    "Indivisible": "#0B6E6E",
    "Reinforcing": "#2A9D8F",
    "Enabling": "#6BAF92",
    "Neutral": "#B0B7C3",
    "Constraining": "#E9C46A",
    "Counteracting": "#E76F51",
    "Cancelling": "#9B2226",
}

RATING_TEXT_COLOURS: Dict[str, str] = {
    "Indivisible": "#ffffff",
    "Reinforcing": "#ffffff",
    "Enabling": "#2d2d2d",
    "Neutral": "#555555",
    "Constraining": "#2d2d2d",
    "Counteracting": "#ffffff",
    "Cancelling": "#ffffff",
}

# Aggregated-grid colour buckets (`aggregation_tab.py:59-67`). The key order (3 ... -3) is what makes
# `_score_bucket` break ties toward +infinity, so it must not change.
SCORE_TO_RATING: Dict[int, str] = {
    3: "Indivisible",
    2: "Reinforcing",
    1: "Enabling",
    0: "Neutral",
    -1: "Constraining",
    -2: "Counteracting",
    -3: "Cancelling",
}
