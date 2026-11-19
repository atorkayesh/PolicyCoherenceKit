"""
Unit tests for InsightsFeature.

Tests cover:
- Average ranks for ties; Pearson 1.0 at zero variance; one decision-maker gives agreement 1.0
- Graph statistics (first strongest pair in row-major order), roles, and integer system health
"""

import unittest

import pytest

from features.insights_feature import InsightsFeature
from models.aggregation_models import AggregationResult


@pytest.mark.unit
class TestInsightsFeature(unittest.TestCase):
    """Test cases for InsightsFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = InsightsFeature()

    def test_ranks_and_correlation(self):
        """Test tied ranks and the zero-variance rule."""
        self.assertEqual(self.feature.rank_values([3.0, 1.0, 3.0]), [2.5, 1.0, 2.5])
        self.assertEqual(self.feature.pearson_corr([1.0, 1.0], [0.0, 2.0]), 1.0)
        self.assertAlmostEqual(self.feature.pearson_corr([1.0, 2.0], [2.0, 1.0]), -1.0, places=12)

    def test_graph_roles_health(self):
        """Test graph stats, roles and health on a 2 x 2 result."""
        r = AggregationResult(
            scores={(0, 1): 3.0, (1, 0): 3.0},
            ties=[],
            n=2,
            codes=["P1", "P2"],
            policies=["A", "B"],
            method="average",
            decision_makers=1,
            decision_maker_names=["X"],
        )
        graph = self.feature.graph_stats(r)
        self.assertEqual((graph["positive_edges"], graph["strongest_pos_pair"], graph["polarity"]), (2, (0, 1), 1.0))
        self.assertEqual(self.feature.spearman_agreement(r), (1.0, 1.0))
        self.assertEqual([self.feature.role(v) for v in (0.06, -0.06, 0.05)], ["driver", "dependent", "balanced"])
        self.assertEqual(
            self.feature.system_health(r), {"score": 100, "synergy": 100, "conflict": 0, "neutral_uncertain": 0}
        )
