"""
Analysis request: the project plus the aggregation settings (API Contract, shared request models).

Fewer than three decision-makers force Average; weights are used for Weighted only, the median choice for an even
decision-maker count only, and tie choices for Majority Rule only (choices for cells that are not tied are ignored).
"""

from typing import List, Optional

from pydantic import BaseModel, Field, FiniteFloat

from constants.aggregation_constants import AggregationMethod, MedianChoice
from models.project_models import ProjectInput


class TieChoice(BaseModel):
    """The rating chosen for one tied cell."""

    row: int = Field(description="0-based influencing policy index")
    col: int = Field(description="0-based influenced policy index")
    rating: str = Field(description="One of the cell's tied ratings")


class AggregationSettings(BaseModel):
    """How the decision-makers' matrices are combined."""

    method: AggregationMethod = AggregationMethod.AVERAGE
    weights: Optional[List[FiniteFloat]] = Field(
        default=None, description="Weighted only: one weight in [0, 1] per decision-maker"
    )
    median_choice: Optional[MedianChoice] = Field(
        default=None, description="Median with an even decision-maker count only; default lower"
    )
    tie_choices: List[TieChoice] = Field(default_factory=list, description="Majority Rule only")


class AnalysisRequest(ProjectInput):
    """The project and its aggregation settings; every results endpoint recomputes from it."""

    aggregation: AggregationSettings = Field(default_factory=AggregationSettings)
