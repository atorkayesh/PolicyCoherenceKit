"""
The legacy run flow (`app.py:2533-2611`) as one request step, used by the preview, analysis, chart, export and
explanation endpoints.

Steps: completeness (422) → effective method (fewer than 3 decision-makers force Average; weights, median choice
and tie choices are then ignored) → weights or median choice → aggregate → apply tie choices (atomic, unlike the
legacy dialog) → optionally require every tie resolved (first unresolved tie in row-major order).
"""

import asyncio
from typing import Dict, List, Optional, Tuple

from constants.aggregation_constants import AGGREGATION_MESSAGES, AGGREGATION_RULES, AggregationMethod, MedianChoice
from constants.rating_constants import RATING_SCORES
from errors.analysis_errors import InvalidTieChoiceError, InvalidWeightsError, UnresolvedTieError
from features.aggregation_feature import AggregationFeature, aggregation_feature
from features.matrix_check_feature import MatrixCheckFeature, matrix_check_feature
from models.aggregation_models import (
    AggregationData,
    AggregationRun,
    RatingMatrix,
    TieData,
    TiedCell,
    TieOption,
    TieVote,
)
from models.analysis_request_models import AnalysisRequest, TieChoice
from models.error_models import ErrorContextData
from utils.aggregation_label_utils import aggregation_labeler
from utils.matrix_utils import matrix_converter


class AggregationFlowFeature:
    """Turns an analysis request into an aggregation result."""

    def __init__(self, aggregation: Optional[AggregationFeature] = None, checks: Optional[MatrixCheckFeature] = None):
        """
        Create the feature.

        Args:
            aggregation: Aggregation methods; defaults to the shared instance
            checks: Completeness check; defaults to the shared instance
        """
        self._aggregation = aggregation or aggregation_feature
        self._checks = checks or matrix_check_feature

    def run(self, request: AnalysisRequest, require_resolved: bool = True) -> AggregationRun:
        """
        Aggregate the request.

        Args:
            request: Validated analysis request
            require_resolved: Raise for the first tie without a choice (analysis endpoints)

        Returns:
            AggregationRun: The result with ties resolved where choices were given

        Raises:
            IncompleteMatricesError: A cell is blank
            InvalidWeightsError: Weighted with missing, out-of-range or badly summed weights
            InvalidTieChoiceError: A choice is not a tied rating, or a cell has two choices
            UnresolvedTieError: `require_resolved` and a tie has no choice
        """
        matrices = self._checks.rating_matrices(request)
        self._checks.require_complete(matrices)
        settings = request.aggregation
        requested = settings.method
        forced = len(matrices) < AGGREGATION_RULES["METHOD_CHOICE_MIN_DECISION_MAKERS"]
        method = AggregationMethod.AVERAGE if forced else requested
        weights = None
        if method == AggregationMethod.AVERAGE:
            result = self._aggregation.average(matrices)
        elif method == AggregationMethod.MEDIAN:
            choice = (settings.median_choice or AGGREGATION_RULES["DEFAULT_MEDIAN_CHOICE"]).value
            result = self._aggregation.median(matrices, even_choice=choice)
        elif method == AggregationMethod.MAJORITY:
            result = self._aggregation.majority(matrices)
            self._apply_tie_choices(result, settings.tie_choices)
        else:
            weights = self._check_weights(settings.weights, matrices)
            result = self._aggregation.weighted(matrices, weights)
        if require_resolved:
            self.require_resolved(result.ties)
        return AggregationRun(result, matrices, requested, forced, weights)

    async def preview(self, request: AnalysisRequest) -> AggregationData:
        """
        Aggregate without requiring every tie to be resolved (the tie step).

        Args:
            request: Validated analysis request; tie choices may be partial

        Returns:
            AggregationData: Scores with null for unresolved ties and `ready = false` until all are chosen
        """
        run = await asyncio.to_thread(self.run, request, False)
        return self.aggregation_data(run)

    def aggregation_data(self, run: AggregationRun) -> AggregationData:
        """
        Package an aggregation for the client.

        Args:
            run: Aggregation run

        Returns:
            AggregationData: Method facts, scores, colour bands, median labels and ties
        """
        result = run.result
        n = result.n
        scores = matrix_converter.to_grid(result.scores, n)
        ordinal = matrix_converter.to_grid(result.ordinal_cells, n) if result.ordinal_cells else None
        return AggregationData(
            requested_method=run.requested_method,
            method=AggregationMethod(result.method),
            method_label=aggregation_labeler.method_label(result),
            method_forced=run.method_forced,
            decision_maker_count=result.decision_makers,
            decision_makers=result.decision_maker_names,
            policies=result.policies,
            codes=result.codes,
            weights=run.weights,
            median_choice=MedianChoice(result.median_even_choice) if result.median_even_choice else None,
            scores=scores,
            bands=[[self._aggregation.score_band(score) for score in row] for row in scores],
            ordinal_cells=[[list(cell) for cell in row] for row in ordinal] if ordinal else None,
            ties=[self._tie_data(tie, run) for tie in result.ties],
            ready=all(tie.chosen is not None for tie in result.ties),
        )

    def _tie_data(self, tie: TiedCell, run: AggregationRun) -> TieData:
        policies = run.result.policies
        return TieData(
            row=tie.row,
            col=tie.col,
            code_row=tie.code_r,
            code_col=tie.code_c,
            policy_row=policies[tie.row],
            policy_col=policies[tie.col],
            tied_options=[TieOption(label=label, score=RATING_SCORES[label]) for label in tie.tied_labels],
            votes=[
                TieVote(decision_maker=m.decision_maker, rating=m.get_rating(tie.row, tie.col)) for m in run.matrices
            ],
            chosen=tie.chosen,
        )

    def require_resolved(self, ties: List[TiedCell]) -> None:
        """
        Raise for the first tie without a choice (row-major order).

        Raises:
            UnresolvedTieError: With the tie dialog's message (L11 arrow)
        """
        for tie in ties:
            if tie.chosen is None:
                self._raise(UnresolvedTieError, "UNRESOLVED_TIE", row=tie.code_r, col=tie.code_c)

    def _apply_tie_choices(self, result, choices: List[TieChoice]) -> None:
        """Validate every choice first, then write the chosen scores (`resolve_ties`, atomic)."""
        n = result.n
        by_cell: Dict[Tuple[int, int], str] = {}
        for choice in choices:
            if not (0 <= choice.row < n and 0 <= choice.col < n):
                continue
            cell = (choice.row, choice.col)
            if cell in by_cell:
                codes = result.codes
                self._raise(InvalidTieChoiceError, "DUPLICATE_TIE_CHOICE", row=codes[cell[0]], col=codes[cell[1]])
            by_cell[cell] = choice.rating
        for tie in result.ties:
            rating = by_cell.get((tie.row, tie.col))
            if rating is not None and rating not in tie.tied_labels:
                self._raise(InvalidTieChoiceError, "INVALID_TIE_CHOICE", rating=rating, row=tie.code_r, col=tie.code_c)
        for tie in result.ties:
            rating = by_cell.get((tie.row, tie.col))
            if rating is not None:
                tie.chosen = rating
                self._aggregation.resolve_tie(result, tie)

    def _check_weights(self, weights: Optional[List[float]], matrices: List[RatingMatrix]) -> List[float]:
        """Count (aggregator text), then range per decision-maker and the sum (weight dialog texts, L2)."""
        given = list(weights or [])
        if len(given) != len(matrices):
            self._raise(InvalidWeightsError, "WEIGHT_COUNT", n=len(matrices), k=len(given))
        for weight, matrix in zip(given, matrices, strict=False):
            if not (AGGREGATION_RULES["WEIGHT_MIN"] <= weight <= AGGREGATION_RULES["WEIGHT_MAX"]):
                self._raise(InvalidWeightsError, "WEIGHT_RANGE", dm=matrix.decision_maker)
        total = round(sum(given), 10)
        if abs(total - AGGREGATION_RULES["WEIGHT_SUM_TARGET"]) > AGGREGATION_RULES["WEIGHT_SUM_TOLERANCE"]:
            self._raise(InvalidWeightsError, "WEIGHT_SUM", total=round(total, 4))
        return given

    def _raise(self, error_class, key: str, **values) -> None:
        """Raise a flow error with the message-box title (the log detail never holds user data)."""
        title, message = AGGREGATION_MESSAGES[key]
        raise error_class(key, public_message=message.format(**values), data=ErrorContextData(title=title))


aggregation_flow_feature = AggregationFlowFeature()
