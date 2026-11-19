"""
Unit tests for MatrixCheckFeature.

Tests cover:
- `blank_count` and the 10-item `blank_cells` cap; the legacy message with `(+k more)` and the L11 arrow
- Aggregation options by decision-maker count
"""

import unittest

import pytest

from features.matrix_check_feature import MatrixCheckFeature
from models.project_models import ProjectInput


@pytest.mark.unit
class TestMatrixCheckFeature(unittest.TestCase):
    """Test cases for MatrixCheckFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = MatrixCheckFeature()

    def test_blank_cells(self):
        """Test a 4 x 4 matrix with 12 blanks."""
        project = ProjectInput(
            project_name="P", policies=["A", "B", "C", "D"], decision_makers=[{"name": "X", "ratings": [[""] * 4] * 4}]
        )
        data = self.feature.check(project)
        row = data.decision_makers[0]
        self.assertEqual((row.blank_count, len(row.blank_cells), row.filled, row.total), (12, 10, 0, 12))
        self.assertTrue(
            data.incomplete_message.endswith(
                "  X: P1 → P2, P1 → P3, P1 → P4, P2 → P1, P2 → P3, P2 → P4, "
                "P3 → P1, P3 → P2, P3 → P4, P4 → P1 (+2 more)"
            )
        )
        self.assertFalse(data.complete)

    def test_options(self):
        """Test forced Average below 3 and the median choice for even counts."""
        self.assertEqual(self.feature.aggregation_options(2).forced_method, "average")
        self.assertFalse(self.feature.aggregation_options(3).median_choice_applies)
        self.assertTrue(self.feature.aggregation_options(4).median_choice_applies)
