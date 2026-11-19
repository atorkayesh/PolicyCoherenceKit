"""
Unit tests for NetworkLayouter (parity with legacy layouts is in `tests/layout_parity_integration_test.py`).

Tests cover:
- Circular layout from -π/2 on the 600 x 600 canvas; one node at the centre
- L16: eigenvector columns flipped so the largest-magnitude entry is positive
- Spectral and force-directed fall back to circular for tiny or edgeless graphs; results stay within the canvas
"""

import unittest

import numpy as np
import pytest

from constants.chart_constants import NetworkLayout
from utils.network_layout_utils import NetworkLayouter


@pytest.mark.unit
class TestNetworkLayouter(unittest.TestCase):
    """Test cases for NetworkLayouter."""

    def setUp(self):
        """Create the layouter."""
        self.layouter = NetworkLayouter()

    def test_circular(self):
        """Test the first node is at the top and a single node at the centre."""
        positions = self.layouter.circular([0, 1, 2, 3], 600, 600)
        self.assertAlmostEqual(positions[0][0], 300.0)
        self.assertAlmostEqual(positions[0][1], 80.0)
        self.assertEqual(self.layouter.circular([5], 600, 600), {5: (300.0, 300.0)})

    def test_flip_signs(self):
        """Test the largest-magnitude entry of each column becomes positive (first on ties)."""
        fixed = self.layouter.flip_signs(np.array([[0.1, -0.5], [-0.9, 0.5]]))
        np.testing.assert_array_equal(fixed, [[-0.1, 0.5], [0.9, -0.5]])

    def test_fallbacks_and_bounds(self):
        """Test fallbacks to circular and that every layout stays on the canvas."""
        edges = [(0, 1, 2.0), (1, 2, -1.0), (2, 3, 3.0), (3, 0, 1.0)]
        circular = self.layouter.circular([0, 1], 600, 600)
        self.assertEqual(self.layouter.spectral([0, 1], edges, 600, 600), circular)
        self.assertEqual(self.layouter.spectral([0, 1, 2], [], 600, 600), self.layouter.circular([0, 1, 2], 600, 600))
        centrality = [{"code": f"P{i + 1}", "betweenness": 0.1 * i} for i in range(4)]
        for layout in NetworkLayout:
            positions = self.layouter.positions(
                layout, [0, 1, 2, 3], edges, (600, 600), centrality, ["P1", "P2", "P3", "P4"]
            )
            self.assertTrue(all(0 <= x <= 600 and 0 <= y <= 600 for x, y in positions.values()), layout)
