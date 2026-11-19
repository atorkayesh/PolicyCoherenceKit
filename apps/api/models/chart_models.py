"""`NetworkChartData` (`POST /analysis/charts/network`): everything the browser's ECharts graph draws."""

from typing import List, Optional

from pydantic import BaseModel, Field

from constants.chart_constants import NetworkLayout


class ChartCanvas(BaseModel):
    """Logical canvas of the layout (px; y grows downwards as in the legacy canvas)."""

    width: int
    height: int


class ChartNode(BaseModel):
    """A node in legacy draw order."""

    index: int
    code: str
    policy: str
    label: str = Field(description="Hover text `{code}:  {policy}`")
    x: float
    y: float
    isolated: bool
    is_focus: bool
    radius: int
    fill: str


class ChartEdge(BaseModel):
    """A directed edge in legacy draw order."""

    source: int
    target: int
    score: float
    sign: str
    colour: str
    width: float
    two_way: bool = Field(description="Both directions exist; the browser curves them to opposite sides (L7)")
    label: Optional[str] = Field(description="`{score:+.2f}` in the ego view, else null")


class ChartStats(BaseModel):
    """The full-network info bar."""

    node_count: int
    edge_count: int
    density: float
    isolated_count: int
    text: str


class NetworkChartData(BaseModel):
    """One network layout, full or ego view."""

    layout: NetworkLayout
    layout_label: str
    focus: Optional[int]
    canvas: ChartCanvas
    title: Optional[str] = Field(description="Ego view only")
    empty_message: Optional[str] = Field(description="Ego view without edges (L8: shown below the node)")
    nodes: List[ChartNode]
    edges: List[ChartEdge]
    stats: ChartStats
