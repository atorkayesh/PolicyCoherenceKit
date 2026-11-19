"""
Unit tests for CoherenceScoresFeature.

Tests cover:
- OI/II counts, WOI/WII sums rounded to 2 dp; None reads as 0
- Value and count band thresholds
"""

import unittest

import pytest

from features.coherence_scores_feature import CoherenceScoresFeature
from models.aggregation_models import AggregationResult


@pytest.mark.unit
class TestCoherenceScoresFeature(unittest.TestCase):
    """Test cases for CoherenceScoresFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = CoherenceScoresFeature()

    def test_scores(self):
        """Test a 3 x 3 result."""
        scores = {(0, 1): 2.0, (0, 2): -0.5, (1, 0): None, (1, 2): 0.0, (2, 0): 1.25, (2, 1): 0.0}
        result = AggregationResult(
            scores=scores, ties=[], n=3, codes=["P1", "P2", "P3"], policies=["A", "B", "C"], method="average"
        )
        rows = self.feature.compute_scores(result)
        self.assertEqual(
            [(r["oi"], r["ii"], r["woi"], r["wii"]) for r in rows],
            [(2, 1, 1.5, 1.25), (0, 1, 0.0, 2.0), (1, 1, 1.25, -0.5)],
        )

    def test_bands(self):
        """Test every value band and the count bands."""
        values = [1.6, 1.5, 0.6, 0.5, 0.1, 0.0, -0.5, -0.6, -1.5, -1.6]
        self.assertEqual(
            [self.feature.value_band(v) for v in values],
            [
                "strong_positive",
                "positive",
                "positive",
                "weak_positive",
                "weak_positive",
                "zero",
                "weak_negative",
                "negative",
                "negative",
                "strong_negative",
            ],
        )
        self.assertEqual([self.feature.count_band(c, 5) for c in (4, 2, 1, 0)], ["very_high", "high", "medium", "low"])
        self.assertEqual(self.feature.count_band(0, 1), "none")
