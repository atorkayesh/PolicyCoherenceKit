"""
Unit tests for InsightsTextFeature (exact parity is in `tests/insights_text_parity_integration_test.py`).

Tests cover:
- L11 arrow, L12 `Rating agreement`, L13 sign wording; `N/A` texts without a top driver
"""

import unittest

import pytest

from features.analysis_feature import analysis_feature
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestInsightsTextFeature(unittest.TestCase):
    """Test cases for InsightsTextFeature."""

    def test_label_fixes(self):
        """Test the fixed labels on a negative case."""
        texts = analysis_feature.analyze_sync(parity_fixtures.request("negative6x3__average")).insights.texts
        self.assertIn("through the negative link ", texts.story)
        self.assertIn(", negative)", texts.story)
        self.assertNotIn("->", texts.story)
        self.assertTrue(texts.most_contested.value_text.startswith("Rating agreement: "))
        self.assertIn(" ↔ ", texts.most_contested.main)
        self.assertEqual(texts.strongest_link.value_text, "No strong link")
        self.assertEqual(texts.tag_strongest_link, "Strongest Link: No non-zero relation")
        self.assertEqual(texts.interpretation_label, "Interpretation:")
