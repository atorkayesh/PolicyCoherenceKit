"""
Unit tests for ScalesFeature.

Tests cover:
- Rating order, L1 method labels and the L2 description, layouts in legacy order, limits
"""

import unittest

import pytest

from features.scales_feature import ScalesFeature


@pytest.mark.unit
class TestScalesFeature(unittest.TestCase):
    """Test cases for ScalesFeature."""

    def test_scales(self):
        """Test the main values."""
        data = ScalesFeature().get_scales()
        self.assertEqual([r.label for r in data.ratings][0], "Indivisible")
        self.assertEqual([m.label for m in data.methods], ["Average", "Median", "Majority Rule", "Weighted"])
        self.assertTrue(data.methods[3].description.endswith("Weights must sum to 1.0 (±0.01)."))
        self.assertEqual(
            [layout.label for layout in data.network.layouts], ["Circular", "Force-Directed", "Spectral", "Shell"]
        )
        self.assertEqual(
            (data.rules.max_policies, data.network.layout_canvas, data.imports.max_bytes), (100, [600, 600], 5242880)
        )
        self.assertEqual(data.texts.most_contested_value_label, "Rating agreement")
