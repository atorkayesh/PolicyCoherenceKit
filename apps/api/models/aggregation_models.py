"""
Aggregation models.

Internal dataclasses port the legacy `PolicyMatrix` (`models.py:13-44`), `TiedCell` and `AggregationResult`
(`aggregator.py:37-90`) without the `_cached_*` fields: the stateless API recomputes every request. The Pydantic
models are the `AggregationData` response (API Contract).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from constants.aggregation_constants import AggregationMethod, MedianChoice
from constants.rating_constants import DIAGONAL_LABEL

Cell = Tuple[int, int]


@dataclass
class RatingMatrix:
    """One decision-maker's matrix; the diagonal is always Neutral and unset cells read as `""`."""

    decision_maker: str
    policies: List[str]
    codes: List[str]
    data: Dict[Cell, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for i in range(len(self.policies)):
            self.data[(i, i)] = DIAGONAL_LABEL

    def get_rating(self, row: int, col: int) -> str:
        """Return the rating of a cell, or `""` when unset."""
        return self.data.get((row, col), "")


@dataclass
class TiedCell:
    """A majority-rule tie; `tied_labels` are sorted by score, high to low."""

    row: int
    col: int
    code_r: str
    code_c: str
    tied_labels: List[str]
    chosen: Optional[str] = None


@dataclass
class AggregationResult:
    """Output of an aggregation method (legacy fields, no caches)."""

    scores: Dict[Cell, Optional[float]]
    ties: List[TiedCell]
    n: int
    codes: List[str]
    policies: List[str]
    method: str
    decision_makers: int = 0
    decision_maker_names: List[str] = field(default_factory=list)
    source_scores: Dict[Cell, List[float]] = field(default_factory=dict)
    ordinal_cells: Dict[Cell, Tuple[str, ...]] = field(default_factory=dict)
    median_even_choice: Optional[str] = None


@dataclass
class AggregationRun:
    """An aggregation as the request asked for it: the result plus the request-level facts."""

    result: AggregationResult
    matrices: List[RatingMatrix]
    requested_method: AggregationMethod
    method_forced: bool
    weights: Optional[List[float]]


class TieOption(BaseModel):
    """One tied rating."""

    label: str
    score: int


class TieVote(BaseModel):
    """One decision-maker's rating of a tied cell."""

    decision_maker: str
    rating: str


class TieData(BaseModel):
    """A tied cell and its options (legacy order: score descending)."""

    row: int
    col: int
    code_row: str
    code_col: str
    policy_row: str
    policy_col: str
    tied_options: List[TieOption]
    votes: List[TieVote]
    chosen: Optional[str]


class AggregationData(BaseModel):
    """The aggregated matrix and the method actually used."""

    requested_method: AggregationMethod
    method: AggregationMethod
    method_label: str
    method_forced: bool = Field(
        description="True whenever fewer than 3 decision-makers force Average, whatever method was requested"
    )
    decision_maker_count: int
    decision_makers: List[str]
    policies: List[str]
    codes: List[str]
    weights: Optional[List[float]]
    median_choice: Optional[MedianChoice] = Field(description="Set only for median with an even count")
    scores: List[List[Optional[float]]] = Field(description="n x n; null for unresolved ties")
    bands: List[List[str]] = Field(description="Rating label of each cell's colour band")
    ordinal_cells: Optional[List[List[List[str]]]] = Field(description="Median only: middle label(s) per cell")
    ties: List[TieData]
    ready: bool = Field(description="True when every tie has a valid choice")
