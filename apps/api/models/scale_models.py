"""`ScalesData` (`GET /scales`): the rating scale, methods, rules, bands, layouts and limits, from constants only."""

from typing import List, Optional

from pydantic import BaseModel


class RatingScaleItem(BaseModel):
    """One rating label with its score and cell colours."""

    label: str
    score: int
    fill: str
    text: str


class OptionItem(BaseModel):
    """A selectable option."""

    key: str
    label: str
    description: str


class ScaleRules(BaseModel):
    """Limits and aggregation rules."""

    min_policies: int
    max_policies: int
    min_decision_makers: int
    max_decision_makers: int
    method_choice_min_decision_makers: int
    forced_method: str
    default_method: str
    default_median_choice: str
    weight_min: float
    weight_max: float
    weight_sum_target: float
    weight_sum_tolerance: float


class CountBand(BaseModel):
    """OI/II colour band."""

    key: str
    min_ratio: Optional[float]
    fill: str
    text: str


class ValueBand(BaseModel):
    """WOI/WII colour band."""

    key: str
    fill: str
    text: str


class EntropyCategory(BaseModel):
    """Range of influence category."""

    label: str
    threshold_text: str
    fill: str
    text: str


class LayoutOption(BaseModel):
    """A network layout."""

    key: str
    label: str


class NetworkScale(BaseModel):
    """Network layouts and colours."""

    layouts: List[LayoutOption]
    default_layout: str
    positive_colour: str
    negative_colour: str
    isolated_colour: str
    node_colour: str
    focus_colour: str
    node_text_colour: str
    layout_canvas: List[int]


class PcaScale(BaseModel):
    """PCA scatter colours."""

    point_colour: str
    axis_colour: str


class ScaleTexts(BaseModel):
    """Labels the web app shows next to API values."""

    most_contested_value_label: str


class ImportScale(BaseModel):
    """Upload limits."""

    accept: List[str]
    max_bytes: int


class ScalesData(BaseModel):
    """Everything the web app needs to render inputs and results."""

    ratings: List[RatingScaleItem]
    diagonal_label: str
    methods: List[OptionItem]
    median_choices: List[OptionItem]
    rules: ScaleRules
    count_bands: List[CountBand]
    value_bands: List[ValueBand]
    entropy_categories: List[EntropyCategory]
    network: NetworkScale
    pca: PcaScale
    texts: ScaleTexts
    imports: ImportScale
