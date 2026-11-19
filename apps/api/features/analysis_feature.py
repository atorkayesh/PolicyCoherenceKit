"""
`POST /analysis`: request → aggregation flow → every analysis → `AnalysisData`, as `_create_analysis_tabs` and the
analysis tabs compute them (`app.py:2613`, the `*_tab.py` compute functions). CPU-bound work runs in a thread.
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

from features.aggregation_flow_feature import AggregationFlowFeature, aggregation_flow_feature
from features.centrality_feature import CentralityFeature, centrality_feature
from features.coherence_scores_feature import CoherenceScoresFeature, coherence_scores_feature
from features.entropy_feature import EntropyFeature, entropy_feature
from features.insights_feature import InsightsFeature, insights_feature
from features.insights_text_feature import InsightsTextFeature, insights_text_feature
from features.pca_feature import PcaFeature, pca_feature
from models.aggregation_models import AggregationRun
from models.analysis_request_models import AnalysisRequest
from models.analysis_result_models import AnalysisData
from models.insights_models import AgreementStats, ContestedPair, GraphStats, HealthStats, InsightsData, InsightsRow
from utils.graph_utils import GraphAnalyzer, graph_analyzer


@dataclass
class AnalysisOutput:
    """The legacy analysis rows of one run, shared by the analysis, XLSX export and prompt."""

    run: AggregationRun
    graph: Dict
    scores: List[Dict]
    entropy: List[Dict]
    centrality: List[Dict]


class AnalysisFeature:
    """Runs every analysis of an aggregated matrix."""

    def __init__(
        self,
        flow: Optional[AggregationFlowFeature] = None,
        scores: Optional[CoherenceScoresFeature] = None,
        entropy: Optional[EntropyFeature] = None,
        pca: Optional[PcaFeature] = None,
        centrality: Optional[CentralityFeature] = None,
        insights: Optional[InsightsFeature] = None,
        texts: Optional[InsightsTextFeature] = None,
        graphs: Optional[GraphAnalyzer] = None,
    ):
        """Create the feature; every dependency defaults to its shared instance."""
        self._flow = flow or aggregation_flow_feature
        self._scores = scores or coherence_scores_feature
        self._entropy = entropy or entropy_feature
        self._pca = pca or pca_feature
        self._centrality = centrality or centrality_feature
        self._insights = insights or insights_feature
        self._texts = texts or insights_text_feature
        self._graphs = graphs or graph_analyzer

    async def analyze(self, request: AnalysisRequest) -> AnalysisData:
        """
        Run the analysis in a worker thread.

        Args:
            request: Validated analysis request

        Returns:
            AnalysisData: Aggregation and every analysis
        """
        return await asyncio.to_thread(self.analyze_sync, request)

    def compute(self, request: AnalysisRequest) -> AnalysisOutput:
        """
        Aggregate (every tie resolved) and compute the legacy rows.

        Args:
            request: Validated analysis request

        Returns:
            AnalysisOutput: The run, graph, scores, entropy and centrality rows
        """
        run = self._flow.run(request)
        result = run.result
        graph = self._graphs.build_graph(result)
        return AnalysisOutput(
            run=run,
            graph=graph,
            scores=self._scores.compute_scores(result),
            entropy=self._entropy.compute_entropy(result),
            centrality=self._centrality.compute_centrality(result, graph),
        )

    def analyze_sync(self, request: AnalysisRequest) -> AnalysisData:
        """
        Run the analysis.

        Args:
            request: Validated analysis request

        Returns:
            AnalysisData: Aggregation and every analysis
        """
        output = self.compute(request)
        result = output.run.result
        return AnalysisData(
            project_name=request.project_name,
            aggregation=self._flow.aggregation_data(output.run),
            coherence_scores=self._scores.rows(output.scores, result.n),
            range_of_influence=self._entropy.data(output.entropy),
            pca=self._pca.data(result, output.entropy),
            network=self._centrality.data(result, output.graph, output.centrality),
            insights=self._insights_data(output),
        )

    def _insights_data(self, output: AnalysisOutput) -> InsightsData:
        result = output.run.result
        insights = self._insights.compute(result, output.scores, output.entropy, output.centrality)
        fields = InsightsRow.model_fields
        graph = insights["graph"]
        agreement = insights["agreement"]
        return InsightsData(
            rows=[InsightsRow(**{key: row[key] for key in fields}) for row in insights["rows"]],
            graph=self._graph_stats(graph),
            agreement=AgreementStats(
                average_agreement=agreement["average_agreement"],
                average_correlation=agreement["average_correlation"],
                contested=[ContestedPair(**row) for row in agreement["contested"]],
            ),
            health=HealthStats(**insights["health"]),
            texts=self._texts.texts(result, insights),
        )

    def _graph_stats(self, graph: Dict) -> GraphStats:
        pairs = {key: self._pair(graph[key]) for key in ("strongest_pos_pair", "strongest_neg_pair")}
        return GraphStats(**{**graph, **pairs})

    def _pair(self, pair) -> Optional[List[int]]:
        return list(pair) if pair else None


analysis_feature = AnalysisFeature()
