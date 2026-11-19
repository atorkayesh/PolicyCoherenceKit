"""Range of influence (Shannon entropy) categories (`range_of_influence_tab.py:55-63, 130-141, 221-225`)."""

from typing import Dict, List

# Category, threshold text, fill and text colour, in legacy order.
ENTROPY_CATEGORIES: List[Dict[str, str]] = [
    {"label": "Low", "threshold_text": "H < 25% of max", "fill": "#a3a3a3", "text": "#ffffff"},
    {"label": "Low-to-Medium", "threshold_text": "25% ≤ H < 50% of max", "fill": "#a7f3d0", "text": "#2d2d2d"},
    {"label": "Medium-to-High", "threshold_text": "50% ≤ H < 75% of max", "fill": "#34d399", "text": "#ffffff"},
    {"label": "High", "threshold_text": "H ≥ 75% of max", "fill": "#059669", "text": "#ffffff"},
]

# Upper bounds of the ratio `H / Hmax` for the first three categories.
ENTROPY_RATIO_CUTOFFS = (0.25, 0.50, 0.75)
