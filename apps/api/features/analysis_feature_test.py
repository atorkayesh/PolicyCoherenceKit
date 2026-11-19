"""
Unit tests for AnalysisFeature (full parity is in `tests/parity_integration_test.py`).

Tests cover:
- The async entry point and the shared analysis rows; unresolved ties are rejected
"""

import unittest

import pytest

from errors.analysis_errors import UnresolvedTieError
from features.analysis_feature import AnalysisFeature
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestAnalysisFeature(unittest.IsolatedAsyncioTestCase):
    """Test cases for AnalysisFeature."""

    async def test_analyze(self):
        """Test the result shape for a fixture."""
        data = await AnalysisFeature().analyze(parity_fixtures.request("r6x4__median_upper"))
        self.assertEqual((data.project_name, data.aggregation.method_label), ("Parity r6x4", "Median (Upper)"))
        self.assertEqual(len(data.coherence_scores), 6)

    async def test_unresolved_tie(self):
        """Test analysis requires every tie resolved."""
        request = parity_fixtures.request("r5x3__majority_first")
        request.aggregation.tie_choices = []
        with self.assertRaises(UnresolvedTieError):
            await AnalysisFeature().analyze(request)
