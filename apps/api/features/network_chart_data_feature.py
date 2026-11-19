"""
Network chart data (`network_tab.py:890-1165`): node positions on the 600 x 600 logical canvas, edges, colours
and texts, built as `_redraw_network` (`:903-907`) and `_redraw_ego` (`:1052-1090`) build them. The browser draws
it with ECharts; the API renders no image.

Ego view: only the ego's edges, the ego first then its neighbours by index, the ego at radius 22 in the focus
colour. Without neighbours the ego is drawn alone at the canvas centre in the isolated colour at radius 18, and
`empty_message` is returned for the browser to show below it (L8).
"""

import asyncio
from typing import Dict, List, Optional

from constants.aggregation_constants import AGGREGATION_MESSAGES
from constants.chart_constants import (
    NETWORK_LAYOUT_CANVAS,
    NETWORK_LAYOUT_LABELS,
    NETWORK_STYLE,
    NETWORK_TEXT,
    NetworkLayout,
)
from errors.analysis_errors import InvalidFocusPolicyError
from features.analysis_feature import AnalysisFeature, analysis_feature
from features.centrality_feature import CentralityFeature, centrality_feature
from models.analysis_request_models import AnalysisRequest
from models.chart_models import ChartCanvas, ChartEdge, ChartNode, ChartStats, NetworkChartData
from models.error_models import ErrorContextData
from utils.graph_utils import GraphAnalyzer, graph_analyzer
from utils.network_layout_utils import NetworkLayouter, network_layouter


class NetworkChartDataFeature:
    """Builds `NetworkChartData`."""

    def __init__(
        self,
        analysis: Optional[AnalysisFeature] = None,
        centrality: Optional[CentralityFeature] = None,
        layouter: Optional[NetworkLayouter] = None,
        graphs: Optional[GraphAnalyzer] = None,
    ):
        """Create the feature; every dependency defaults to its shared instance."""
        self._analysis = analysis or analysis_feature
        self._centrality = centrality or centrality_feature
        self._layouter = layouter or network_layouter
        self._graphs = graphs or graph_analyzer

    async def chart(self, request: AnalysisRequest, layout: NetworkLayout, focus: Optional[int]) -> NetworkChartData:
        """Build the chart data in a worker thread (see `chart_sync`)."""
        return await asyncio.to_thread(self.chart_sync, request, layout, focus)

    def chart_sync(self, request: AnalysisRequest, layout: NetworkLayout, focus: Optional[int]) -> NetworkChartData:
        """
        Build the chart data.

        Args:
            request: Validated analysis request (every tie resolved)
            layout: Layout
            focus: 0-based policy index for the ego view, or None for the full network

        Returns:
            NetworkChartData: Nodes, edges, texts and the full-network stats

        Raises:
            InvalidFocusPolicyError: When `focus` is not a policy index
        """
        n = len(request.policies)
        if focus is not None and not 0 <= focus < n:
            title, message = AGGREGATION_MESSAGES["INVALID_FOCUS"]
            raise InvalidFocusPolicyError(
                "focus out of range", public_message=message.format(last=n - 1), data=ErrorContextData(title=title)
            )
        output = self._analysis.compute(request)
        result = output.run.result
        graph = output.graph
        edges = graph["edges"]
        if focus is None:
            node_ids = list(range(n))
            used = edges
        else:
            used = [(i, j, s) for (i, j, s) in edges if i == focus or j == focus]
            neighbours = sorted({i for i, _, _ in used if i != focus} | {j for _, j, _ in used if j != focus})
            node_ids = [focus] + neighbours
        positions = self._layouter.positions(
            layout, node_ids, used, NETWORK_LAYOUT_CANVAS, output.centrality, result.codes
        )
        stats = self._centrality.stats(result, graph)
        width, height = NETWORK_LAYOUT_CANVAS
        return NetworkChartData(
            layout=layout,
            layout_label=NETWORK_LAYOUT_LABELS[layout],
            focus=focus,
            canvas=ChartCanvas(width=width, height=height),
            title=None
            if focus is None
            else NETWORK_TEXT["EGO_TITLE"].format(code=result.codes[focus], policy=result.policies[focus]),
            empty_message=NETWORK_TEXT["EGO_EMPTY"].format(code=result.codes[focus])
            if focus is not None and len(node_ids) == 1
            else None,
            nodes=self._nodes(result, node_ids, positions, used, focus),
            edges=self._edges(used, focus is not None),
            stats=ChartStats(**stats),
        )

    def _nodes(self, result, node_ids: List[int], positions: Dict, edges, focus: Optional[int]) -> List[ChartNode]:
        connected = {i for i, _, _ in edges} | {j for _, j, _ in edges}
        alone = focus is not None and len(node_ids) == 1
        nodes = []
        for idx in node_ids:
            isolated = idx not in connected
            is_focus = idx == focus
            if is_focus and not alone:
                fill, radius = NETWORK_STYLE["FOCUS_COLOUR"], NETWORK_STYLE["FOCUS_RADIUS"]
            else:
                fill = NETWORK_STYLE["ISOLATED_COLOUR"] if isolated else NETWORK_STYLE["NODE_COLOUR"]
                radius = NETWORK_STYLE["NODE_RADIUS"]
            x, y = positions[idx]
            code, policy = result.codes[idx], result.policies[idx]
            nodes.append(
                ChartNode(
                    index=idx,
                    code=code,
                    policy=policy,
                    label=NETWORK_TEXT["HOVER_LABEL"].format(code=code, policy=policy),
                    x=x,
                    y=y,
                    isolated=isolated,
                    is_focus=is_focus,
                    radius=radius,
                    fill=fill,
                )
            )
        return nodes

    def _edges(self, edges, ego: bool) -> List[ChartEdge]:
        pairs = {(i, j) for i, j, _ in edges}
        return [
            ChartEdge(
                source=i,
                target=j,
                score=s,
                sign="positive" if s > 0 else "negative",
                colour=NETWORK_STYLE["POSITIVE_COLOUR" if s > 0 else "NEGATIVE_COLOUR"],
                width=self._graphs.thickness(s),
                two_way=(j, i) in pairs,
                label=NETWORK_TEXT["EDGE_LABEL"].format(score=s) if ego else None,
            )
            for i, j, s in edges
        ]


network_chart_data_feature = NetworkChartDataFeature()
