"""
Unit tests for AggregationLabeler (L1, L3).

Tests cover:
- Labels of results (Median (Lower)/(Upper) for even medians, Median for odd) and of method keys
- Unknown methods are title-cased; sheet labels drop the parentheses
"""

import unittest

import pytest

from constants.aggregation_constants import AggregationMethod
from models.aggregation_models import AggregationResult
from utils.aggregation_label_utils import AggregationLabeler


def result(method: str, choice=None) -> AggregationResult:
    """Build an empty result."""
    return AggregationResult(scores={}, ties=[], n=0, codes=[], policies=[], method=method, median_even_choice=choice)


@pytest.mark.unit
class TestAggregationLabeler(unittest.TestCase):
    """Test cases for AggregationLabeler."""

    def setUp(self):
        """Create the labeler."""
        self.labeler = AggregationLabeler()

    def test_result_labels(self):
        """Test every result label."""
        cases = [
            (result("average"), "Average"),
            (result("majority"), "Majority Rule"),
            (result("weighted"), "Weighted"),
            (result("median"), "Median"),
            (result("median", "lower"), "Median (Lower)"),
            (result("median", "upper"), "Median (Upper)"),
            (result("borda"), "Borda"),
        ]
        for value, label in cases:
            with self.subTest(label=label):
                self.assertEqual(self.labeler.method_label(value), label)

    def test_method_keys(self):
        """Test string and enum method keys."""
        self.assertEqual(self.labeler.method_label("median"), "Median")
        self.assertEqual(self.labeler.method_label(AggregationMethod.MAJORITY), "Majority Rule")

    def test_sheet_label(self):
        """Test the L3 sheet label."""
        self.assertEqual(self.labeler.sheet_label("Median (Lower)"), "Median Lower")
        self.assertEqual(self.labeler.sheet_label("Majority Rule"), "Majority Rule")
