"""
Unit tests for CentralityFeature.

Tests cover:
- Betweenness normalisation and closeness above 1 (outgoing distances)
- The info-bar text with isolated nodes; the stable ranking; edge sign and two-way flags
"""

import unittest

import pytest

from features.centrality_feature import CentralityFeature
from models.aggregation_models import AggregationResult
from utils.graph_utils import graph_analyzer


def result(scores, n):
    """Build a result."""
    codes = [f"P{i + 1}" for i in range(n)]
    return AggregationResult(scores=scores, ties=[], n=n, codes=codes, policies=codes, method="average")


@pytest.mark.unit
class TestCentralityFeature(unittest.TestCase):
    """Test cases for CentralityFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = CentralityFeature()

    def test_closeness_above_one(self):
        """Test n = 2 with |s| = 3 gives closeness 3.0."""
        r = result({(0, 1): 3.0}, 2)
        rows = self.feature.compute_centrality(r, graph_analyzer.build_graph(r))
        self.assertEqual([(x["betweenness"], x["closeness"]) for x in rows], [(0.0, 3.0), (0.0, 0.0)])

    def test_stats_ranking_edges(self):
        """Test the stats line, ranking ties in index order, and edges."""
        r = result({(0, 1): 1.0, (1, 0): -2.0, (1, 2): 1.0}, 4)
        graph = graph_analyzer.build_graph(r)
        stats = self.feature.stats(r, graph)
        self.assertEqual(stats["text"], "4 nodes  |  3 directed edges  |  density: 0.25  |  1 isolated")
        rows = self.feature.compute_centrality(r, graph)
        self.assertEqual(self.feature.ranking(rows), ["P2", "P1", "P3", "P4"])
        edges = self.feature.edges(graph)
        self.assertEqual(
            [(e.sign, e.two_way, e.width) for e in edges],
            [("positive", True, 1.0), ("negative", True, 2.5), ("positive", False, 1.0)],
        )
