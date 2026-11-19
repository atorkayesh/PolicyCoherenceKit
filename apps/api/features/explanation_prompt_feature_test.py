"""
Unit tests for ExplanationPromptFeature (exact parity for every fixture is in the prompt integration test).

Tests cover:
- The header names the method label; the seven section headers appear in order
"""

import unittest

import pytest

from features.analysis_feature import analysis_feature
from features.explanation_prompt_feature import SECTION_HEADERS, ExplanationPromptFeature
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestExplanationPromptFeature(unittest.TestCase):
    """Test cases for ExplanationPromptFeature."""

    def test_prompt(self):
        """Test the header and sections."""
        output = analysis_feature.compute(parity_fixtures.request("r6x4__median_lower"))
        prompt = ExplanationPromptFeature().build_prompt(
            output.run.result, output.scores, output.entropy, output.centrality
        )
        self.assertIn("for 6 policies, aggregated using the Median (Lower) method.", prompt)
        positions = [prompt.index(f"## {header}") for header in SECTION_HEADERS]
        self.assertEqual(positions, sorted(positions))
