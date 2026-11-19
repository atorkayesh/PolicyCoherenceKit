"""
Unit tests for GraphAnalyzer.

Tests cover:
- Edges for positive and negative scores with distance 1/|score|; unresolved ties (None) read as 0
- Edge thickness bands
- Shortest-path counting with equal-length paths and Brandes betweenness
"""

import unittest

import pytest

from models.aggregation_models import AggregationResult
from utils.graph_utils import GraphAnalyzer


def result(scores, n) -> AggregationResult:
    """Build a result from a cell dict."""
    return AggregationResult(
        scores=scores, ties=[], n=n, codes=[f"P{i + 1}" for i in range(n)], policies=[], method="average"
    )


@pytest.mark.unit
class TestGraphAnalyzer(unittest.TestCase):
    """Test cases for GraphAnalyzer."""

    def setUp(self):
        """Create the analyzer."""
        self.graphs = GraphAnalyzer()

    def test_build_graph(self):
        """Test negative edges are kept and None is skipped."""
        graph = self.graphs.build_graph(result({(0, 1): -2.0, (1, 0): None, (1, 2): 0.5}, 3))
        self.assertEqual(graph["edges"], [(0, 1, -2.0), (1, 2, 0.5)])
        self.assertEqual(graph["dist"], {(0, 1): 0.5, (1, 2): 2.0})

    def test_thickness(self):
        """Test the three widths."""
        self.assertEqual(
            [self.graphs.thickness(s) for s in (3.0, -2.5, 2.0, -1.5, 1.0, 0.5)], [4.0, 4.0, 2.5, 2.5, 1.0, 1.0]
        )

    def test_equal_paths_and_betweenness(self):
        """Test two equal paths 0→1→3 and 0→2→3 are both counted and split the betweenness."""
        graph = self.graphs.build_graph(result({(0, 1): 1.0, (1, 3): 1.0, (0, 2): 1.0, (2, 3): 1.0}, 4))
        d, pred, sigma = self.graphs.dijkstra_with_paths(4, graph["adj"], 0)
        self.assertEqual((d[3], sorted(pred[3]), sigma[3]), (2.0, [1, 2], 2))
        self.assertEqual(self.graphs.brandes_betweenness(4, graph["adj"]), {0: 0.0, 1: 0.5, 2: 0.5, 3: 0.0})
        self.assertEqual(self.graphs.dijkstra_simple(4, graph["adj"], 3), [float("inf")] * 3 + [0.0])
