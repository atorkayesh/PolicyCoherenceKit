"""
Colour bands of the result tables, verbatim from `coherence_scores_tab.py:73-100`.

Value bands colour WOI and WII with per-cell thresholds applied to row and column sums (kept, see Known Tkinter
Behaviour Kept 18); count bands colour OI and II by `count / (n - 1)`.
"""

from typing import Dict, List

# (key, fill, text colour), in threshold order: > 1.5, > 0.5, > 0, == 0, >= -0.5, >= -1.5, otherwise.
VALUE_BANDS: List[Dict[str, str]] = [
    {"key": "strong_positive", "fill": "#177e40", "text": "#ffffff"},
    {"key": "positive", "fill": "#25c263", "text": "#ffffff"},
    {"key": "weak_positive", "fill": "#88edaf", "text": "#2d2d2d"},
    {"key": "zero", "fill": "#d9d9d9", "text": "#555555"},
    {"key": "weak_negative", "fill": "#f5c07a", "text": "#2d2d2d"},
    {"key": "negative", "fill": "#e07b39", "text": "#ffffff"},
    {"key": "strong_negative", "fill": "#ef4444", "text": "#ffffff"},
]

VALUE_THRESHOLDS = {"STRONG": 1.5, "MODERATE": 0.5, "ZERO": 0.0}

# Count bands by the share of other policies reached; `none` is used when n <= 1.
COUNT_BANDS: List[Dict] = [
    {"key": "very_high", "min_ratio": 0.75, "fill": "#7799b9", "text": "#ffffff"},
    {"key": "high", "min_ratio": 0.5, "fill": "#a6bcd3", "text": "#1f2937"},
    {"key": "medium", "min_ratio": 0.25, "fill": "#d0dbe7", "text": "#1f2937"},
    {"key": "low", "min_ratio": None, "fill": "#eae7e0", "text": "#666666"},
    {"key": "none", "min_ratio": None, "fill": "#d9d9d9", "text": "#555555"},
]
