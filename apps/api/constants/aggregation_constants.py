"""
Aggregation methods, rules, limits and messages.

Method options use one label source (label fix L1) and the legacy descriptions (`aggregation_dialog.py:60-81`,
with the L2 weight text); median options are `aggregation_dialog.py:258-269`. Messages and titles are the legacy
dialog texts (`dialogs.py:1080-1124`, `aggregation_dialog.py:570-613, 779-787`, `app.py:2546-2556`,
`aggregator.py:351-354`) with the L2 and L11 fixes, plus the new messages listed in the plan's business rules.
"""

from enum import Enum
from typing import Dict, List


class AggregationMethod(str, Enum):
    """Aggregation methods, in dialog order."""

    AVERAGE = "average"
    MEDIAN = "median"
    MAJORITY = "majority"
    WEIGHTED = "weighted"


class MedianChoice(str, Enum):
    """Which middle label an even-count median uses."""

    LOWER = "lower"
    UPPER = "upper"


METHOD_LABELS: Dict[str, str] = {
    "average": "Average",
    "majority": "Majority Rule",
    "weighted": "Weighted",
    "median": "Median",
}

METHOD_DESCRIPTIONS: Dict[str, str] = {
    "average": "Each decision-maker is weighted equally. Cell score = mean of all scores.",
    "median": "Uses the ordered middle rating(s) and avoids assuming equal spacing.",
    "majority": "The most common rating wins. Ties are flagged for manual resolution.",
    "weighted": "You assign a weight (0–1) to each DM. Weights must sum to 1.0 (±0.01).",
}

MEDIAN_OPTIONS: List[Dict[str, str]] = [
    {
        "key": "lower",
        "label": "Lower Median",
        "description": "Use the lower of the two middle ratings in the ordered scale.",
    },
    {
        "key": "upper",
        "label": "Upper Median",
        "description": "Use the upper of the two middle ratings in the ordered scale.",
    },
]

AGGREGATION_RULES = {
    "MIN_POLICIES": 2,
    "MAX_POLICIES": 100,
    "MIN_DECISION_MAKERS": 1,
    "MAX_DECISION_MAKERS": 50,
    "METHOD_CHOICE_MIN_DECISION_MAKERS": 3,
    "FORCED_METHOD": AggregationMethod.AVERAGE,
    "DEFAULT_METHOD": AggregationMethod.AVERAGE,
    "DEFAULT_MEDIAN_CHOICE": MedianChoice.LOWER,
    "WEIGHT_MIN": 0.0,
    "WEIGHT_MAX": 1.0,
    "WEIGHT_SUM_TARGET": 1.0,
    "WEIGHT_SUM_TOLERANCE": 0.01,
    "BLANK_CELLS_SHOWN": 10,
}

# Setup validation (`dialogs.py:1080-1124`) plus the request limits and the control-character rule (new).
SETUP_MESSAGES = {
    "PROJECT_NAME_REQUIRED": ("Project Name Required", "Please enter a project name."),
    "DECISION_MAKERS_REQUIRED": ("Decision-Makers Required", "Please enter at least one decision-maker name."),
    "DECISION_MAKER_BLANK": ("Decision-Makers Required", "Please enter a name for every decision-maker."),
    "DUPLICATE_DECISION_MAKERS": ("Duplicate Decision-Makers", "Decision-maker names must be unique."),
    "EXISTING_DECISION_MAKERS": (
        "Existing Decision-Makers",
        "These decision-maker names already exist in the project:\n\n{names}",
    ),
    "TOO_MANY_DECISION_MAKERS": ("Too Many Decision-Makers", "Please enter at most 50 decision-makers."),
    "TOO_MANY_POLICIES": ("Too Many Policies", "Please enter at most 100 policy names."),
    "TOO_FEW_POLICIES": ("Too Few Policies", "Please enter at least 2 policy names."),
    "POLICY_BLANK": ("Too Few Policies", "Please enter a name for every policy."),
    "DUPLICATE_POLICIES": ("Duplicate Policies", "Policy names must be unique."),
    "CONTROL_CHARACTERS": ("Invalid Name", "Names must not contain control characters."),
    "RATINGS_SHAPE": ("Invalid Ratings", 'Ratings for "{dm}" must be {n} x {n}.'),
    "UNRECOGNISED_RATING": ("Invalid Ratings", 'Unrecognised rating "{value}" for "{dm}" at {row} → {col}.'),
}

AGGREGATION_MESSAGES = {
    "INCOMPLETE": ("Incomplete Matrices", "Please fill all cells before aggregating.\n\n{lines}"),
    "INCOMPLETE_LINE": "  {dm}: {cells}{suffix}",
    "INCOMPLETE_SUFFIX": " (+{count} more)",
    "CELL": "{row} → {col}",
    "WEIGHT_COUNT": ("Invalid Weights", "Expected {n} weights, got {k}."),
    "WEIGHT_MISSING": ("Missing Weight", 'Please enter a weight for "{dm}".'),
    "WEIGHT_INVALID": ("Invalid Value", '"{raw}" is not a valid number for "{dm}". Use a decimal like 0.3.'),
    "WEIGHT_RANGE": ("Out of Range", 'Weight for "{dm}" must be between 0.0 and 1.0.'),
    "WEIGHT_SUM": (
        "Weights Do Not Sum to 1",
        "Current sum is {total}.\nPlease adjust the weights so they sum to 1.0 (±0.01).",
    ),
    "WEIGHT_SUM_TEXT": "Sum: {total}",
    "WEIGHT_SUM_UNPARSABLE": "Sum: —",
    "UNRESOLVED_TIE": ("Unresolved Tie", "Please select a rating for cell {row} → {col}."),
    "INVALID_TIE_CHOICE": ("Invalid Tie Choice", '"{rating}" is not one of the tied ratings for cell {row} → {col}.'),
    "DUPLICATE_TIE_CHOICE": ("Invalid Tie Choice", "Cell {row} → {col} has more than one tie choice."),
    "INVALID_FOCUS": ("Invalid Focus Policy", "The focus policy must be between 0 and {last}."),
}
