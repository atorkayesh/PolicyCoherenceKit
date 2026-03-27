# =============================================================================
# Policy Coherence Kit -- aggregator.py
# Pure aggregation logic. No tkinter, no UI.
#
# Public API
# ----------
# check_completeness(matrices)         -> list of (dm_name, [(code_r, code_c), ...])
# aggregate_average(matrices)          -> AggregationResult
# aggregate_majority(matrices)         -> AggregationResult  (may contain TiedCell entries)
# aggregate_weighted(matrices,weights) -> AggregationResult
# resolve_ties(result)                 -> AggregationResult
#
# AggregationResult
# -----------------
# .scores   : dict (i,j) -> float   (rounded to 2 dp; None for unresolved ties)
# .ties     : list of TiedCell       (only populated by aggregate_majority)
# .n        : int
# .codes    : list[str]
# .policies : list[str]
# .method   : str
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter

from constants import RATING_SCORES, DIAGONAL_VALUE
from models import PolicyMatrix


# =============================================================================
# Data structures
# =============================================================================

@dataclass
class TiedCell:
    """Represents a majority-rule tie that needs manual resolution."""
    row:         int
    col:         int
    code_r:      str
    code_c:      str
    tied_labels: List[str]           # labels that are tied, sorted high -> low
    chosen:      Optional[str] = None  # filled in by the UI after user picks


@dataclass
class AggregationResult:
    """
    Output of any aggregation method.

    scores   : (row, col) -> float, rounded to 2 decimal places.
                Diagonal is always 0.0.
                None for unresolved majority ties (before resolve_ties()).
    ties     : non-empty only when aggregate_majority finds tied cells.
    n        : number of policies
    codes    : policy codes  (P1, P2, ...)
    policies : full policy names
    method   : 'average' | 'majority' | 'weighted'

    Cached analysis results (populated lazily by analysis tabs):
    _cached_scores    : coherence scores (OI, II, WOI, WII)
    _cached_entropy   : entropy/range of influence data
    _cached_centrality: network centrality data
    _cached_graph     : network graph structure
    """
    scores:   Dict[Tuple[int, int], float]
    ties:     List[TiedCell]
    n:        int
    codes:    List[str]
    policies: List[str]
    method:   str
    # Cached analysis results (populated lazily)
    _cached_scores:     Optional[List[dict]] = field(default=None, repr=False)
    _cached_entropy:    Optional[List[dict]] = field(default=None, repr=False)
    _cached_centrality: Optional[List[dict]] = field(default=None, repr=False)
    _cached_graph:      Optional[Dict]       = field(default=None, repr=False)


# =============================================================================
# Pre-aggregation completeness check
# =============================================================================

def check_completeness(
    matrices: List[PolicyMatrix],
) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """
    Scan every matrix for unfilled off-diagonal cells.

    Returns a list of (decision_maker_name, [(code_row, code_col), ...])
    for every matrix that has at least one blank cell.
    Returns an empty list if all matrices are complete.
    """
    incomplete = []
    for matrix in matrices:
        blanks = []
        n = len(matrix.policies)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if not matrix.get_rating(i, j):
                    blanks.append((matrix.codes[i], matrix.codes[j]))
        if blanks:
            incomplete.append((matrix.decision_maker, blanks))
    return incomplete


# =============================================================================
# Aggregation methods
# =============================================================================

def aggregate_average(matrices: List[PolicyMatrix]) -> AggregationResult:
    """
    Average the numeric scores of all decision-makers per cell.
    Scores are rounded to 2 decimal places.
    """
    _validate_matrices(matrices)
    n        = len(matrices[0].policies)
    codes    = matrices[0].codes
    policies = matrices[0].policies
    scores: Dict[Tuple[int, int], float] = {}

    for i in range(n):
        for j in range(n):
            if i == j:
                scores[(i, j)] = 0.0
                continue
            values = [RATING_SCORES[m.get_rating(i, j)] for m in matrices]
            scores[(i, j)] = round(sum(values) / len(values), 2)

    return AggregationResult(
        scores=scores, ties=[], n=n,
        codes=codes, policies=policies, method="average",
    )


def aggregate_majority(matrices: List[PolicyMatrix]) -> AggregationResult:
    """
    For each cell, take the most common rating (mode) across decision-makers.

    - Unique winner  -> convert its label to a float score.
    - Tie            -> score stays None; a TiedCell is recorded for UI resolution.

    After the UI resolves all ties, call resolve_ties(result) to finalise scores.
    """
    _validate_matrices(matrices)
    n        = len(matrices[0].policies)
    codes    = matrices[0].codes
    policies = matrices[0].policies
    scores: Dict[Tuple[int, int], float] = {}
    ties:   List[TiedCell] = []

    for i in range(n):
        for j in range(n):
            if i == j:
                scores[(i, j)] = 0.0
                continue

            labels    = [m.get_rating(i, j) for m in matrices]
            counter   = Counter(labels)
            max_count = max(counter.values())
            winners   = [lbl for lbl, cnt in counter.items() if cnt == max_count]

            if len(winners) == 1:
                scores[(i, j)] = float(RATING_SCORES[winners[0]])
            else:
                scores[(i, j)] = None   # resolved later
                ties.append(TiedCell(
                    row=i, col=j,
                    code_r=codes[i], code_c=codes[j],
                    tied_labels=sorted(
                        winners,
                        key=lambda lbl: RATING_SCORES[lbl],
                        reverse=True,
                    ),
                ))

    return AggregationResult(
        scores=scores, ties=ties, n=n,
        codes=codes, policies=policies, method="majority",
    )


def resolve_ties(result: AggregationResult) -> AggregationResult:
    """
    After the UI has set TiedCell.chosen for every unresolved tie,
    write the chosen scores back into result.scores.
    Raises ValueError if any tie is still unresolved.
    Returns the same result object (mutated in place) for convenience.
    """
    for tie in result.ties:
        if tie.chosen is None:
            raise ValueError(
                f"Tie at {tie.code_r} -> {tie.code_c} has not been resolved."
            )
        result.scores[(tie.row, tie.col)] = float(RATING_SCORES[tie.chosen])
    return result


def aggregate_weighted(
    matrices: List[PolicyMatrix],
    weights:  List[float],
) -> AggregationResult:
    """
    Weighted average of numeric scores across decision-makers.

    weights : list of floats in [0.0, 1.0], one per matrix, must sum to 1.0.
    Raises ValueError for invalid weights.
    Scores are rounded to 2 decimal places.
    """
    _validate_matrices(matrices)
    _validate_weights(weights, len(matrices))

    n        = len(matrices[0].policies)
    codes    = matrices[0].codes
    policies = matrices[0].policies
    scores: Dict[Tuple[int, int], float] = {}

    for i in range(n):
        for j in range(n):
            if i == j:
                scores[(i, j)] = 0.0
                continue
            value = sum(
                w * RATING_SCORES[m.get_rating(i, j)]
                for w, m in zip(weights, matrices)
            )
            scores[(i, j)] = round(value, 2)

    return AggregationResult(
        scores=scores, ties=[], n=n,
        codes=codes, policies=policies, method="weighted",
    )


# =============================================================================
# Internal validators
# =============================================================================

def _validate_matrices(matrices: List[PolicyMatrix]):
    """Raise if the list is empty or matrices have inconsistent policy lists."""
    if not matrices:
        raise ValueError("No matrices provided for aggregation.")
    ref = matrices[0].policies
    for m in matrices[1:]:
        if m.policies != ref:
            raise ValueError(
                f'Matrix "{m.decision_maker}" has a different policy list '
                f'from "{matrices[0].decision_maker}". '
                "All matrices must share the same policies to be aggregated."
            )


def _validate_weights(weights: List[float], n: int):
    """Raise if weights length, range, or sum are invalid."""
    if len(weights) != n:
        raise ValueError(f"Expected {n} weights, got {len(weights)}.")
    for i, w in enumerate(weights):
        if not (0.0 <= w <= 1.0):
            raise ValueError(
                f"Weight {i + 1} is {w:.4f} — must be between 0.0 and 1.0."
            )
    total = round(sum(weights), 10)
    if abs(total - 1.0) > 0.01:
        raise ValueError(
            f"Weights sum to {round(total, 4)} — must sum to exactly 1.0."
        )
