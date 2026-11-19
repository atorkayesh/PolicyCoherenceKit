"""
Unit tests for SetupValidationFeature.

Tests cover:
- `/setup/validate`: trimming, dropped empty entries, partial forms, codes
- The legacy order and messages, existing decision-makers, limits and control characters
- Request matrices: shape and label errors
"""

import unittest

import pytest

from errors.setup_errors import InvalidRatingsError, InvalidSetupError
from features.setup_validation_feature import SetupValidationFeature
from models.setup_models import SetupValidateRequest


@pytest.mark.unit
class TestSetupValidationFeature(unittest.TestCase):
    """Test cases for SetupValidationFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = SetupValidationFeature()

    def fail(self, **form) -> str:
        """Return the setup error message."""
        with self.assertRaises(InvalidSetupError) as raised:
            self.feature.validate_setup(SetupValidateRequest(**form))
        return raised.exception.public_message

    def test_clean_form(self):
        """Test trimming, dropped empties and codes."""
        data = self.feature.validate_setup(
            SetupValidateRequest(project_name=" P ", decision_makers=[" A ", ""], policies=["X", " ", "Y"])
        )
        self.assertEqual(
            (data.project_name, data.decision_makers, data.policies, data.codes), ("P", ["A"], ["X", "Y"], ["P1", "P2"])
        )
        self.assertIsNone(self.feature.validate_setup(SetupValidateRequest(project_name="P")).codes)

    def test_order_and_limits(self):
        """Test the first failing rule wins, then limits and control characters."""
        self.assertEqual(self.fail(project_name=" ", decision_makers=[]), "Please enter a project name.")
        self.assertEqual(self.fail(decision_makers=["A", "A"], policies=["X"]), "Decision-maker names must be unique.")
        self.assertEqual(
            self.fail(decision_makers=[f"D{k}" for k in range(51)]), "Please enter at most 50 decision-makers."
        )
        self.assertEqual(self.fail(policies=[f"P{k}" for k in range(101)]), "Please enter at most 100 policy names.")
        self.assertEqual(self.fail(policies=["X", "Y\x07"]), "Names must not contain control characters.")
        message = self.fail(decision_makers=["Zed", "Al"], existing_decision_makers=["Al", "Zed"])
        self.assertEqual(message, "These decision-maker names already exist in the project:\n\nAl\nZed")

    def test_ratings(self):
        """Test shape before labels."""
        with self.assertRaises(InvalidRatingsError) as raised:
            self.feature.check_ratings(["A"], [[["Neutral"]]], ["P1", "P2"])
        self.assertEqual(raised.exception.public_message, 'Ratings for "A" must be 2 x 2.')
        with self.assertRaises(InvalidRatingsError) as raised:
            self.feature.check_ratings(["A"], [[["x", "enabling"], ["", "Neutral"]]], ["P1", "P2"])
        self.assertEqual(raised.exception.public_message, 'Unrecognised rating "enabling" for "A" at P1 → P2.')
