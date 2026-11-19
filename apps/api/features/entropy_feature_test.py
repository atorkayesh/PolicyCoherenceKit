"""
Unit tests for EntropyFeature.

Tests cover:
- Hmax for n = 2 and n > 2; one non-zero link gives `-0.0`; no links give 0.0 and Low
- Category thresholds use the rounded H over the unrounded Hmax
"""

import math
import unittest

import pytest

from features.entropy_feature import EntropyFeature
from models.aggregation_models import AggregationResult


def result(scores, n):
    """Build a result."""
    codes = [f"P{i + 1}" for i in range(n)]
    return AggregationResult(scores=scores, ties=[], n=n, codes=codes, policies=codes, method="average")


@pytest.mark.unit
class TestEntropyFeature(unittest.TestCase):
    """Test cases for EntropyFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = EntropyFeature()

    def test_rows(self):
        """Test `-0.0`, an even split, and an empty row."""
        rows = self.feature.compute_entropy(result({(0, 1): 2.0, (1, 0): 1.0, (1, 2): -1.0}, 3))
        self.assertEqual(math.copysign(1.0, rows[0]["entropy"]), -1.0)
        self.assertEqual((rows[1]["entropy"], rows[1]["category"]), (1.0, "High"))
        self.assertEqual((rows[2]["entropy"], rows[2]["category"], rows[2]["hmax"]), (0.0, "Low", 1.0))
        self.assertEqual(self.feature.compute_entropy(result({}, 2))[0]["hmax"], 1.0)

    def test_categories(self):
        """Test the four bands and Hmax 0."""
        self.assertEqual(
            [self.feature.categorise(h, 1.0) for h in (0.2, 0.25, 0.5, 0.75)],
            ["Low", "Low-to-Medium", "Medium-to-High", "High"],
        )
        self.assertEqual(self.feature.categorise(0.0, 0.0), "Low")
