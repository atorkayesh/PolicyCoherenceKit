"""
Network centrality (`network_tab.py:275-320`), the info-bar statistics (`network_tab.py:381-393`) and the
centrality ranking (`network_tab.py:1263`).

Known Tkinter Behaviour Kept 7, 8 and 21: betweenness is normalised by `(n-1)(n-2)` (1 when n ≤ 2) and rounded to
4 dp; closeness uses outgoing distances, `(reachable / (n-1)) / mean(distance)`, and can exceed 1; the ranking is a
stable sort by betweenness, descending.
"""

from typing import Dict, List, Optional

from constants.chart_constants import NETWORK_TEXT
from models.aggregation_models import AggregationResult
from models.analysis_result_models import CentralityRow, NetworkData, NetworkEdge
from utils.graph_utils import GraphAnalyzer, graph_analyzer


class CentralityFeature:
    """Computes centrality and the network summary."""

    def __init__(self, graphs: Optional[GraphAnalyzer] = None):
        """
        Create the feature.

        Args:
            graphs: Graph algorithms; defaults to the shared instance
        """
        self._graphs = graphs or graph_analyzer

    def compute_centrality(self, result: AggregationResult, graph: Dict) -> List[Dict]:
        """
        Compute betweenness and closeness of every policy, in index order.

        Args:
            result: Aggregation result
            graph: Output of `GraphAnalyzer.build_graph`

        Returns:
            List[Dict]: `{code, policy, betweenness, closeness}`
        """
        n = result.n
        adj = graph["adj"]
        btw_raw = self._graphs.brandes_betweenness(n, adj)
        norm_btw = (n - 1) * (n - 2) if n > 2 else 1
        btw = {i: round(btw_raw[i] / norm_btw, 4) for i in range(n)}
        INF = float("inf")
        clo = {}
        for i in range(n):
            d_i = self._graphs.dijkstra_simple(n, adj, i)
            finite = [d for j, d in enumerate(d_i) if j != i and d != INF]
            if not finite:
                clo[i] = 0.0
            else:
                avg = sum(finite) / len(finite)
                clo[i] = round((len(finite) / (n - 1)) / avg if avg > 0 else 0.0, 4)
        return [
            {"code": result.codes[i], "policy": result.policies[i], "betweenness": btw[i], "closeness": clo[i]}
            for i in range(n)
        ]

    def stats(self, result: AggregationResult, graph: Dict) -> Dict:
        """
        The legacy info bar: edge count, density, isolated count and the stats line.

        Args:
            result: Aggregation result
            graph: Output of `GraphAnalyzer.build_graph`

        Returns:
            Dict: `node_count`, `edge_count`, `density`, `isolated_count`, `text`
        """
        n_edges = len(graph["edges"])
        n_nodes = result.n
        isolated = sum(1 for i in range(n_nodes) if not any(k[0] == i or k[1] == i for k in graph["weights"]))
        max_edges = n_nodes * (n_nodes - 1) if n_nodes > 1 else 1
        density = round(n_edges / max_edges, 3)
        text = NETWORK_TEXT["STATS"].format(nodes=n_nodes, edges=n_edges, density=density)
        if isolated:
            text += NETWORK_TEXT["STATS_ISOLATED"].format(isolated=isolated)
        return {
            "node_count": n_nodes,
            "edge_count": n_edges,
            "density": density,
            "isolated_count": isolated,
            "text": text,
        }

    def ranking(self, rows: List[Dict]) -> List[str]:
        """
        Codes sorted by betweenness, descending (stable: ties keep index order).

        Args:
            rows: Output of `compute_centrality`

        Returns:
            List[str]: Policy codes
        """
        return [row["code"] for row in sorted(rows, key=lambda row: row["betweenness"], reverse=True)]

    def edges(self, graph: Dict) -> List[NetworkEdge]:
        """
        The non-zero relations with sign, width and the two-way flag (L7, display only).

        Args:
            graph: Output of `GraphAnalyzer.build_graph`

        Returns:
            List[NetworkEdge]: Row-major order
        """
        weights = graph["weights"]
        return [
            NetworkEdge(
                source=i,
                target=j,
                score=s,
                sign="positive" if s > 0 else "negative",
                width=self._graphs.thickness(s),
                two_way=(j, i) in weights,
            )
            for i, j, s in graph["edges"]
        ]

    def data(self, result: AggregationResult, graph: Dict, rows: List[Dict]) -> NetworkData:
        """
        Package the network summary.

        Args:
            result: Aggregation result
            graph: Output of `GraphAnalyzer.build_graph`
            rows: Output of `compute_centrality`

        Returns:
            NetworkData: Stats, edges, centrality and ranking
        """
        stats = self.stats(result, graph)
        return NetworkData(
            node_count=stats["node_count"],
            edge_count=stats["edge_count"],
            density=stats["density"],
            isolated_count=stats["isolated_count"],
            stats_text=stats["text"],
            edges=self.edges(graph),
            centrality=[CentralityRow(**row) for row in rows],
            centrality_ranking=self.ranking(rows),
        )


centrality_feature = CentralityFeature()
