"""
The four aggregation methods, ported verbatim from `aggregator.py:126-330`, and the colour band of a cell
(`aggregation_tab.py:82-86`).

Kept exactly: integer sums before dividing (Average), the generator `sum` left to right (Weighted), `Counter`
insertion order and the score-descending tie labels (Majority), the stable ascending sort of labels (Median, which
never averages), Python's half-to-even `round`, and `-0.0` from rounding small negative weighted sums. Validation
of matrices, weights and the median choice happens before these functions run (`aggregation_flow_feature.py`).
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple

from constants.rating_constants import DIAGONAL_LABEL, RATING_SCORES, SCORE_TO_RATING
from models.aggregation_models import AggregationResult, Cell, RatingMatrix, TiedCell


class AggregationFeature:
    """Aggregates decision-maker matrices."""

    def average(self, matrices: List[RatingMatrix]) -> AggregationResult:
        """Mean of the integer scores per cell, rounded to 2 dp (`aggregator.py:126-155`)."""
        n, codes, policies, scores, source_scores = self._start(matrices)
        for i in range(n):
            for j in range(n):
                if i == j:
                    scores[(i, j)] = 0.0
                    source_scores[(i, j)] = [0.0 for _ in matrices]
                    continue
                values = [RATING_SCORES[m.get_rating(i, j)] for m in matrices]
                scores[(i, j)] = round(sum(values) / len(values), 2)
                source_scores[(i, j)] = [float(v) for v in values]
        return self._result(matrices, scores, source_scores, "average")

    def majority(self, matrices: List[RatingMatrix]) -> AggregationResult:
        """Most common label per cell; ties keep `None` and become `TiedCell`s (`aggregator.py:158-210`)."""
        n, codes, policies, scores, source_scores = self._start(matrices)
        ties: List[TiedCell] = []
        for i in range(n):
            for j in range(n):
                if i == j:
                    scores[(i, j)] = 0.0
                    source_scores[(i, j)] = [0.0 for _ in matrices]
                    continue
                labels = [m.get_rating(i, j) for m in matrices]
                values = [float(RATING_SCORES[label]) for label in labels]
                source_scores[(i, j)] = values
                counter = Counter(labels)
                max_count = max(counter.values())
                winners = [lbl for lbl, cnt in counter.items() if cnt == max_count]
                if len(winners) == 1:
                    scores[(i, j)] = float(RATING_SCORES[winners[0]])
                else:
                    scores[(i, j)] = None
                    ties.append(
                        TiedCell(
                            row=i,
                            col=j,
                            code_r=codes[i],
                            code_c=codes[j],
                            tied_labels=sorted(winners, key=lambda lbl: RATING_SCORES[lbl], reverse=True),
                        )
                    )
        result = self._result(matrices, scores, source_scores, "majority")
        result.ties = ties
        return result

    def median(self, matrices: List[RatingMatrix], even_choice: str = "lower") -> AggregationResult:
        """Ordinal median; even counts keep both middle labels and score the chosen one (`aggregator.py:213-270`)."""
        n, codes, policies, scores, source_scores = self._start(matrices)
        ordinal_cells: Dict[Cell, Tuple[str, ...]] = {}
        for i in range(n):
            for j in range(n):
                if i == j:
                    scores[(i, j)] = 0.0
                    source_scores[(i, j)] = [0.0 for _ in matrices]
                    ordinal_cells[(i, j)] = (DIAGONAL_LABEL,)
                    continue
                labels = [m.get_rating(i, j) for m in matrices]
                ordered = sorted(labels, key=lambda lbl: RATING_SCORES[lbl])
                source_scores[(i, j)] = [float(RATING_SCORES[label]) for label in labels]
                mid = len(ordered) // 2
                if len(ordered) % 2 == 1:
                    median_labels: Tuple[str, ...] = (ordered[mid],)
                    selected_label = ordered[mid]
                else:
                    median_labels = (ordered[mid - 1], ordered[mid])
                    selected_label = ordered[mid - 1] if even_choice == "lower" else ordered[mid]
                ordinal_cells[(i, j)] = median_labels
                scores[(i, j)] = float(RATING_SCORES[selected_label])
        result = self._result(matrices, scores, source_scores, "median")
        result.ordinal_cells = ordinal_cells
        result.median_even_choice = even_choice if len(matrices) % 2 == 0 else None
        return result

    def weighted(self, matrices: List[RatingMatrix], weights: List[float]) -> AggregationResult:
        """`round(sum(w * score), 2)`, weights not renormalised (`aggregator.py:289-330`)."""
        n, codes, policies, scores, source_scores = self._start(matrices)
        for i in range(n):
            for j in range(n):
                if i == j:
                    scores[(i, j)] = 0.0
                    source_scores[(i, j)] = [0.0 for _ in matrices]
                    continue
                raw_values = [float(RATING_SCORES[m.get_rating(i, j)]) for m in matrices]
                value = sum(w * raw for w, raw in zip(weights, raw_values, strict=False))
                scores[(i, j)] = round(value, 2)
                source_scores[(i, j)] = raw_values
        return self._result(matrices, scores, source_scores, "weighted")

    def resolve_tie(self, result: AggregationResult, tie: TiedCell) -> None:
        """Write a tie's chosen score into the result (`aggregator.py:273-286`, one tie at a time)."""
        result.scores[(tie.row, tie.col)] = float(RATING_SCORES[tie.chosen])

    def score_band(self, score: Optional[float]) -> str:
        """
        Colour band of an aggregated cell (`_score_bucket`): nearest integer of the clamped score, ties toward +∞.

        Args:
            score: Aggregated score, or None for an unresolved tie

        Returns:
            str: The rating label of the band (`Neutral` for None)
        """
        if score is None:
            return SCORE_TO_RATING[0]
        clamped = max(-3.0, min(3.0, score))
        return SCORE_TO_RATING[min(SCORE_TO_RATING, key=lambda bucket: abs(bucket - clamped))]

    def _start(self, matrices: List[RatingMatrix]):
        """Return `n`, codes, policies and empty score dicts, read from the first matrix as legacy does."""
        return len(matrices[0].policies), matrices[0].codes, matrices[0].policies, {}, {}

    def _result(self, matrices: List[RatingMatrix], scores, source_scores, method: str) -> AggregationResult:
        return AggregationResult(
            scores=scores,
            ties=[],
            n=len(matrices[0].policies),
            codes=matrices[0].codes,
            policies=matrices[0].policies,
            method=method,
            decision_makers=len(matrices),
            decision_maker_names=[m.decision_maker for m in matrices],
            source_scores=source_scores,
        )


aggregation_feature = AggregationFeature()
