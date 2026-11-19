"""
Unit tests for WeightCheckFeature.

Tests cover:
- The live sum text, `Sum: —` when an input does not parse, and the unrounded ±0.01 colour rule
- Missing → invalid → out-of-range per decision-maker; the sum error only when every weight is valid (L2)
"""

import unittest

import pytest

from features.weight_check_feature import WeightCheckFeature
from models.check_models import WeightCheckRequest

DMS = ["A", "B", "C"]


@pytest.mark.unit
class TestWeightCheckFeature(unittest.TestCase):
    """Test cases for WeightCheckFeature."""

    def check(self, weights):
        """Check raw inputs."""
        return WeightCheckFeature().check(WeightCheckRequest(decision_makers=DMS, weights=weights))

    def test_sum(self):
        """Test the sum text, tolerance and sum error."""
        data = self.check(["0.3", "0.3", "0.3"])
        self.assertEqual((data.sum_text, data.within_tolerance, data.valid), ("Sum: 0.9", False, False))
        self.assertEqual(
            data.first_error.message, "Current sum is 0.9.\nPlease adjust the weights so they sum to 1.0 (±0.01)."
        )
        accepted = self.check(["0.335", "0.335", "0.335"])
        self.assertTrue(accepted.valid and accepted.within_tolerance)

    def test_per_weight_errors(self):
        """Test the per-decision-maker messages and that the sum is not checked then."""
        data = self.check(["", "abc", "1.5"])
        self.assertEqual([e.title for e in data.errors], ["Missing Weight", "Invalid Value", "Out of Range"])
        self.assertEqual(data.sum_text, "Sum: —")
        self.assertIsNone(data.total)
        self.assertEqual(data.weights, [None, None, 1.5])
        nan = self.check(["nan", "0.5", "0.5"])
        self.assertEqual((nan.first_error.title, nan.weights[0]), ("Out of Range", None))
