"""
Unit tests for AggregationFlowFeature.

Tests cover:
- Fewer than 3 decision-makers force Average (choices ignored); the odd median ignores the median choice
- Weight count, range and sum (L2) errors in legacy order; `[0.335]*3` accepted, `[0.34, 0.34, 0.33]` rejected
- Tie choices: valid choices resolve, invalid and duplicate choices fail atomically, the preview keeps open ties
- The first unresolved tie in row-major order
"""

import unittest

import pytest

from errors.analysis_errors import (
    IncompleteMatricesError,
    InvalidTieChoiceError,
    InvalidWeightsError,
    UnresolvedTieError,
)
from features.aggregation_flow_feature import AggregationFlowFeature
from models.analysis_request_models import AnalysisRequest
from tests.parity_fixtures import parity_fixtures


def request(name: str, **aggregation) -> AnalysisRequest:
    """A fixture request with replaced aggregation settings."""
    body = parity_fixtures.parity_case(name)["request"]
    return AnalysisRequest.model_validate({**body, "aggregation": {**body["aggregation"], **aggregation}})


@pytest.mark.unit
class TestAggregationFlowFeature(unittest.TestCase):
    """Test cases for AggregationFlowFeature."""

    def setUp(self):
        """Create the feature."""
        self.flow = AggregationFlowFeature()

    def test_forced_average(self):
        """Test one decision-maker forces Average and ignores invalid weights."""
        run = self.flow.run(request("two2x1__average", method="weighted", weights=[5.0]))
        self.assertEqual((run.result.method, run.method_forced, run.weights), ("average", True, None))

    def test_forced_flag_for_requested_average(self):
        """Test `method_forced` is true below 3 decision-makers even when Average was requested (web notice)."""
        self.assertTrue(self.flow.run(request("two2x1__average", method="average")).method_forced)
        self.assertFalse(self.flow.run(request("r5x3__average", method="average")).method_forced)

    def test_odd_median_ignores_choice(self):
        """Test the choice is not recorded for an odd count."""
        data = self.flow.aggregation_data(self.flow.run(request("r5x3__median", median_choice="upper")))
        self.assertEqual((data.method_label, data.median_choice), ("Median", None))

    def test_weights(self):
        """Test the weight rules and messages."""
        cases = [
            ([0.5, 0.5], "Expected 3 weights, got 2."),
            ([1.2, -0.1, -0.1], 'Weight for "DM 1" must be between 0.0 and 1.0.'),
            ([0.34, 0.34, 0.33], "Current sum is 1.01.\nPlease adjust the weights so they sum to 1.0 (±0.01)."),
        ]
        for weights, message in cases:
            with self.subTest(weights=weights):
                with self.assertRaises(InvalidWeightsError) as raised:
                    self.flow.run(request("r5x3__weighted_a", weights=weights))
                self.assertEqual(raised.exception.public_message, message)
        self.assertEqual(self.flow.run(request("r5x3__weighted_a", weights=[0.335] * 3)).weights, [0.335] * 3)

    def test_tie_choices(self):
        """Test invalid and duplicate choices, the open-tie preview, and the first unresolved tie."""
        tie = parity_fixtures.parity_case("r5x3__majority_first")["aggregation"]["ties"][0]
        with self.assertRaises(InvalidTieChoiceError) as raised:
            self.flow.run(
                request(
                    "r5x3__majority_first", tie_choices=[{"row": tie["row"], "col": tie["col"], "rating": "Neutral"}]
                )
            )
        self.assertIn("is not one of the tied ratings for cell P1 → P2.", raised.exception.public_message)
        twice = [{"row": 0, "col": 1, "rating": "Enabling"}] * 2
        with self.assertRaises(InvalidTieChoiceError) as raised:
            self.flow.run(request("r5x3__majority_first", tie_choices=twice))
        self.assertEqual(raised.exception.public_message, "Cell P1 → P2 has more than one tie choice.")
        partial = self.flow.aggregation_data(self.flow.run(request("r5x3__majority_first", tie_choices=[]), False))
        self.assertFalse(partial.ready)
        self.assertIsNone(partial.scores[0][1])
        self.assertEqual(len(partial.ties[0].votes), 3)
        with self.assertRaises(UnresolvedTieError) as raised:
            self.flow.run(request("r5x3__majority_first", tie_choices=[]))
        self.assertEqual(raised.exception.public_message, "Please select a rating for cell P1 → P2.")

    def test_incomplete(self):
        """Test a blank cell stops every aggregation."""
        body = parity_fixtures.parity_case("r5x3__average")["request"]
        body["decision_makers"][0]["ratings"][0][1] = ""
        with self.assertRaises(IncompleteMatricesError) as raised:
            self.flow.run(AnalysisRequest.model_validate(body), False)
        self.assertEqual(raised.exception.data.title, "Incomplete Matrices")
