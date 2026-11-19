"""
`AnalysisData` (`POST /analysis`): every number exactly as the legacy app computes and rounds it.

Text is returned wherever the legacy display precision is lower than the stored one or the text comes from a
template; the browser formats the remaining numbers like Python's `format` and never re-rounds.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from models.aggregation_models import AggregationData
from models.insights_models import InsightsData


class CoherenceScoreRow(BaseModel):
    """OI, II, WOI and WII of one policy (`coherence_scores_tab.py:107-142`) with their colour-band keys."""

    code: str
    policy: str
    oi: int
    ii: int
    woi: float
    wii: float
    oi_band: str
    ii_band: str
    woi_band: str
    wii_band: str


class EntropyRow(BaseModel):
    """Shannon entropy of one policy's outgoing influence (`range_of_influence_tab.py:82-127`)."""

    code: str
    policy: str
    entropy: float
    category: str


class RangeOfInfluenceData(BaseModel):
    """Entropy rows and the maximum entropy."""

    hmax: float = Field(description="round(Hmax, 4); 1.0 for 2 policies")
    rows: List[EntropyRow]


class PcaPoint(BaseModel):
    """One policy on the PC1/PC2 plane."""

    index: int
    code: str
    policy: str
    label: str = Field(description="Hover text `{code}:  {policy}`")
    x: float
    y: float
    entropy_category: str


class PcaBounds(BaseModel):
    """Axis limits as `pca_tab.py:436-442` maps points: a zero range is drawn as a range of 1.0 from the minimum."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float


class PcaData(BaseModel):
    """Everything the PCA scatter draws (`pca_tab.py:65-121, 185-196, 416-470`)."""

    valid: bool
    explained: List[float]
    total_explained: float
    points: List[PcaPoint]
    bounds: Optional[PcaBounds]
    x_axis_label: Optional[str]
    y_axis_label: Optional[str]
    stats_text: Optional[str]
    message: Optional[str]


class NetworkEdge(BaseModel):
    """A non-zero directed relation, in row-major order."""

    source: int
    target: int
    score: float
    sign: str = Field(description="`positive` or `negative`")
    width: float = Field(description="Legacy `_thickness`: 4, 2.5 or 1 px")
    two_way: bool = Field(description="True when the reverse relation is also non-zero (L7)")


class CentralityRow(BaseModel):
    """Betweenness and closeness of one policy (`network_tab.py:275-320`)."""

    code: str
    policy: str
    betweenness: float
    closeness: float


class NetworkData(BaseModel):
    """The network summary (legacy info bar `network_tab.py:381-393`), edges and centrality."""

    node_count: int
    edge_count: int
    density: float
    isolated_count: int
    stats_text: str
    edges: List[NetworkEdge]
    centrality: List[CentralityRow] = Field(description="Index order")
    centrality_ranking: List[str] = Field(description="Codes by betweenness, descending (stable)")


class AnalysisData(BaseModel):
    """Every analysis of the aggregated matrix."""

    project_name: str
    aggregation: AggregationData
    coherence_scores: List[CoherenceScoreRow]
    range_of_influence: RangeOfInfluenceData
    pca: PcaData
    network: NetworkData
    insights: InsightsData
