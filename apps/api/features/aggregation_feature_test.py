"""
Unit tests for AggregationFeature.

Tests cover:
- Average: integer sums then half-to-even rounding; Weighted: no renormalisation and `-0.0`
- Majority: unique modes, ties with score-descending labels and `None` scores
- Median: odd middle label, even lower/upper choice with both labels kept (never averaged)
- Colour bands: nearest integer of the clamped score, ties toward +∞
"""

import math
import unittest

import pytest

from features.aggregation_feature import AggregationFeature
from models.aggregation_models import RatingMatrix


def matrices(*cells):
    """One 2 x 2 matrix per (0, 1) label; (1, 0) is Neutral."""
    out = []
    for k, label in enumerate(cells):
        m = RatingMatrix(decision_maker=f"DM {k}", policies=["A", "B"], codes=["P1", "P2"])
        m.data[(0, 1)] = label
        m.data[(1, 0)] = "Neutral"
        out.append(m)
    return out


@pytest.mark.unit
class TestAggregationFeature(unittest.TestCase):
    """Test cases for AggregationFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = AggregationFeature()

    def test_average_rounding(self):
        """Test `round(1/8, 2) == 0.12` (half-to-even on the binary value)."""
        result = self.feature.average(matrices("Enabling", *["Neutral"] * 7))
        self.assertEqual(result.scores[(0, 1)], 0.12)
        self.assertEqual(result.source_scores[(0, 1)], [1.0] + [0.0] * 7)

    def test_weighted_negative_zero(self):
        """Test weights are not renormalised and a small negative sum rounds to `-0.0`."""
        result = self.feature.weighted(matrices("Constraining", "Neutral", "Neutral"), [0.004, 0.498, 0.498])
        self.assertEqual(math.copysign(1.0, result.scores[(0, 1)]), -1.0)
        self.assertEqual(self.feature.weighted(matrices("Indivisible"), [0.5]).scores[(0, 1)], 1.5)

    def test_majority(self):
        """Test a unique mode and a tie."""
        self.assertEqual(self.feature.majority(matrices("Enabling", "Enabling", "Neutral")).scores[(0, 1)], 1.0)
        tied = self.feature.majority(matrices("Constraining", "Indivisible", "Neutral"))
        self.assertIsNone(tied.scores[(0, 1)])
        self.assertEqual(tied.ties[0].tied_labels, ["Indivisible", "Neutral", "Constraining"])

    def test_median(self):
        """Test odd and even medians."""
        odd = self.feature.median(matrices("Cancelling", "Enabling", "Indivisible"), "upper")
        self.assertEqual(
            (odd.scores[(0, 1)], odd.ordinal_cells[(0, 1)], odd.median_even_choice), (1.0, ("Enabling",), None)
        )
        cells = ("Neutral", "Constraining", "Indivisible", "Cancelling")
        lower = self.feature.median(matrices(*cells), "lower")
        upper = self.feature.median(matrices(*cells), "upper")
        self.assertEqual(lower.ordinal_cells[(0, 1)], ("Constraining", "Neutral"))
        self.assertEqual((lower.scores[(0, 1)], upper.scores[(0, 1)]), (-1.0, 0.0))
        self.assertEqual((lower.median_even_choice, upper.median_even_choice), ("lower", "upper"))

    def test_score_band(self):
        """Test ties go toward +∞, clamping, and None."""
        self.assertEqual(
            [self.feature.score_band(s) for s in (0.5, -0.5, 2.5, 7.0, -3.4, None)],
            ["Enabling", "Neutral", "Indivisible", "Indivisible", "Cancelling", "Neutral"],
        )
