"""
Unit tests for NetworkChartDataFeature (layout parity is in `tests/layout_parity_integration_test.py`).

Tests cover:
- The invalid focus message; layout label and canvas
"""

import unittest

import pytest

from constants.chart_constants import NetworkLayout
from errors.analysis_errors import InvalidFocusPolicyError
from features.network_chart_data_feature import NetworkChartDataFeature
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestNetworkChartDataFeature(unittest.TestCase):
    """Test cases for NetworkChartDataFeature."""

    def test_focus_and_canvas(self):
        """Test the focus range and the canvas."""
        feature = NetworkChartDataFeature()
        request = parity_fixtures.request("r5x3__average")
        with self.assertRaises(InvalidFocusPolicyError) as raised:
            feature.chart_sync(request, NetworkLayout.SHELL, -1)
        self.assertEqual(raised.exception.public_message, "The focus policy must be between 0 and 4.")
        data = feature.chart_sync(request, NetworkLayout.SHELL, None)
        self.assertEqual((data.layout_label, data.canvas.width, data.canvas.height), ("Shell", 600, 600))
