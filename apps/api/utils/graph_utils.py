"""
Directed weighted graph and shortest paths, ported verbatim from `network_tab.py:80-85, 127-272` (pure Python,
heapq, no networkx: networkx's directed closeness uses incoming distances).

Edges are every non-zero score, positive and negative, in row-major order, with distance `1 / abs(score)`.
Known Tkinter Behaviour Kept 7: equal-length paths are counted when `abs(new - d) < 1e-9`, and back-propagation
visits `(d, v)` pairs sorted in reverse.
"""

import heapq
from typing import Dict, List, Tuple

from models.aggregation_models import AggregationResult

EQUAL_PATH_TOLERANCE = 1e-9


class GraphAnalyzer:
    """Builds the graph and runs Dijkstra and Brandes."""

    def build_graph(self, result: AggregationResult) -> Dict:
        """
        Build the adjacency structure (`_build_graph`).

        Args:
            result: Aggregation result

        Returns:
            Dict: `edges` [(i, j, score)], `weights`, `dist`, `adj`, `adj_rev` and `n`
        """
        n = result.n
        scores = result.scores
        edges, weights, dist = [], {}, {}
        adj: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(n)}
        adj_rev: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                s = scores.get((i, j), 0.0) or 0.0
                if s != 0.0:
                    edges.append((i, j, s))
                    weights[(i, j)] = s
                    d = 1.0 / abs(s)
                    dist[(i, j)] = d
                    adj[i].append((j, d))
                    adj_rev[j].append((i, d))
        return {"edges": edges, "weights": weights, "dist": dist, "adj": adj, "adj_rev": adj_rev, "n": n}

    def thickness(self, score: float) -> float:
        """
        Edge width in px (`_thickness`): |score| ≥ 2.5 → 4.0, ≥ 1.5 → 2.5, else 1.0.

        Args:
            score: Edge score

        Returns:
            float: Line width
        """
        a = abs(score)
        if a >= 2.5:
            return 4.0
        if a >= 1.5:
            return 2.5
        return 1.0

    def dijkstra_with_paths(self, n: int, adj: Dict, source: int) -> Tuple[List[float], List[List[int]], List[int]]:
        """
        Dijkstra with shortest-path counting (`_dijkstra_with_paths`).

        Returns:
            Tuple: distances (inf if unreachable), predecessor lists, shortest-path counts
        """
        INF = float("inf")
        d = [INF] * n
        d[source] = 0.0
        sigma = [0] * n
        sigma[source] = 1
        pred: List[List[int]] = [[] for _ in range(n)]
        pq = [(0.0, source)]
        visited = [False] * n
        while pq:
            _dist_u, u = heapq.heappop(pq)
            if visited[u]:
                continue
            visited[u] = True
            for v, w in adj.get(u, []):
                new_dist = d[u] + w
                if new_dist < d[v]:
                    d[v] = new_dist
                    pred[v] = [u]
                    sigma[v] = sigma[u]
                    heapq.heappush(pq, (new_dist, v))
                elif abs(new_dist - d[v]) < EQUAL_PATH_TOLERANCE:
                    pred[v].append(u)
                    sigma[v] += sigma[u]
        return d, pred, sigma

    def dijkstra_simple(self, n: int, adj: Dict, source: int) -> List[float]:
        """
        Dijkstra distances (`_dijkstra_simple`).

        Returns:
            List[float]: Distances (inf if unreachable)
        """
        INF = float("inf")
        d = [INF] * n
        d[source] = 0.0
        pq = [(0.0, source)]
        visited = [False] * n
        while pq:
            _dist_u, u = heapq.heappop(pq)
            if visited[u]:
                continue
            visited[u] = True
            for v, w in adj.get(u, []):
                new_dist = d[u] + w
                if new_dist < d[v]:
                    d[v] = new_dist
                    heapq.heappush(pq, (new_dist, v))
        return d

    def brandes_betweenness(self, n: int, adj: Dict) -> Dict[int, float]:
        """
        Unnormalised betweenness (`_brandes_betweenness`).

        Returns:
            Dict[int, float]: node -> betweenness count
        """
        btw = {i: 0.0 for i in range(n)}
        for s in range(n):
            d, pred, sigma = self.dijkstra_with_paths(n, adj, s)
            delta = [0.0] * n
            INF = float("inf")
            nodes_by_dist = [(d[v], v) for v in range(n) if d[v] < INF and v != s]
            nodes_by_dist.sort(reverse=True)
            for _, w in nodes_by_dist:
                for v in pred[w]:
                    if sigma[w] > 0:
                        delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
                if w != s:
                    btw[w] += delta[w]
        return btw


graph_analyzer = GraphAnalyzer()
