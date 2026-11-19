"""
Unit tests for PcaFeature.

Tests cover:
- n < 3 is invalid with the legacy message and no points
- An all-zero matrix is valid with zero coordinates and a zero range drawn as min + 1.0
- Labels, stats text and the unrounded percentages
"""

import unittest

import pytest

from features.analysis_feature import analysis_feature
from features.pca_feature import PcaFeature
from models.aggregation_models import AggregationResult
from tests.parity_fixtures import parity_fixtures


def result(scores, n):
    """Build a result."""
    codes = [f"P{i + 1}" for i in range(n)]
    return AggregationResult(scores=scores, ties=[], n=n, codes=codes, policies=codes, method="average")


@pytest.mark.unit
class TestPcaFeature(unittest.TestCase):
    """Test cases for PcaFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = PcaFeature()

    def test_invalid(self):
        """Test fewer than 3 policies."""
        data = self.feature.data(result({}, 2), [])
        self.assertEqual(
            (data.valid, data.points, data.bounds, data.message), (False, [], None, "PCA requires at least 3 policies.")
        )

    def test_zero_variance(self):
        """Test all-Neutral input."""
        rows = [{"category": "Low"}] * 3
        data = self.feature.data(result({}, 3), rows)
        self.assertTrue(data.valid)
        self.assertEqual([(p.x, p.y) for p in data.points], [(0.0, 0.0)] * 3)
        self.assertEqual((data.bounds.x_min, data.bounds.x_max), (0.0, 1.0))
        self.assertEqual(data.stats_text, "PC1: 0.0%   PC2: 0.0%   Total explained: 0.0%")
        self.assertIsNone(self.feature.unrounded_explained(result({}, 3)))

    def test_labels(self):
        """Test axis labels and the unrounded percentages behind them."""
        output = analysis_feature.compute(parity_fixtures.request("r5x3__average"))
        data = self.feature.data(output.run.result, output.entropy)
        pct = self.feature.unrounded_explained(output.run.result)
        self.assertEqual(data.explained, [round(pct[0], 1), round(pct[1], 1)])
        self.assertEqual(data.x_axis_label, f"PC1 ({data.explained[0]}%)")
        self.assertEqual(data.points[0].label, "P1:  Urban Mobility Plan")
