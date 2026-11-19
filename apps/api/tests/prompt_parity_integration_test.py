"""
Exact parity of the AI prompt with `llm_tab.build_prompt` for every parity fixture (no label fixes apply).
"""

import unittest

import pytest

from features.analysis_feature import analysis_feature
from features.explanation_prompt_feature import explanation_prompt_feature
from models.analysis_request_models import AnalysisRequest
from tests.parity_fixtures import parity_fixtures


@pytest.mark.integration
class TestPromptParity(unittest.TestCase):
    """The prompt text."""

    def test_prompt_matches_legacy(self):
        """Test the prompt equals the legacy prompt exactly."""
        for name, fixture in parity_fixtures.parity():
            with self.subTest(name):
                output = analysis_feature.compute(AnalysisRequest.model_validate(fixture["request"]))
                prompt = explanation_prompt_feature.build_prompt(
                    output.run.result, output.scores, output.entropy, output.centrality
                )
                self.assertEqual(prompt, fixture["prompt"])
