"""Responses of `POST /matrices/check` and the request and response of `POST /weights/check`."""

from typing import List, Optional

from pydantic import BaseModel, Field

from constants.aggregation_constants import AggregationMethod


class BlankCell(BaseModel):
    """A blank off-diagonal cell."""

    row: int
    col: int
    code_row: str
    code_col: str


class DecisionMakerCompleteness(BaseModel):
    """How far one decision-maker's matrix is filled."""

    name: str
    filled: int
    total: int
    complete: bool
    blank_count: int
    blank_cells: List[BlankCell] = Field(description="The first 10 blanks in row-major order")


class AggregationOptions(BaseModel):
    """Which aggregation choices the decision-maker count allows."""

    decision_maker_count: int
    method_choice_available: bool = Field(description="False below 3 decision-makers (Average is forced)")
    forced_method: Optional[AggregationMethod]
    median_choice_applies: bool = Field(description="True for an even decision-maker count of at least 3")


class MatrixCheckData(BaseModel):
    """Completeness of every matrix and the aggregation options."""

    complete: bool
    decision_makers: List[DecisionMakerCompleteness]
    incomplete_message: Optional[str] = Field(description="The legacy `Incomplete Matrices` text, or null")
    aggregation_options: AggregationOptions


class WeightCheckRequest(BaseModel):
    """The raw weight inputs, one per decision-maker."""

    decision_makers: List[str]
    weights: List[Optional[str]]


class WeightError(BaseModel):
    """One weight-dialog message."""

    index: Optional[int] = Field(description="Decision-maker index, or null for the sum")
    decision_maker: Optional[str]
    title: str
    message: str


class WeightCheckData(BaseModel):
    """Live sum, colour rule and validation of the weight inputs (`aggregation_dialog.py:558-613`)."""

    total: Optional[float] = Field(description="Sum of the non-empty inputs, or null when one does not parse")
    sum_text: str
    within_tolerance: bool
    valid: bool
    weights: List[Optional[float]]
    errors: List[WeightError]
    first_error: Optional[WeightError]
