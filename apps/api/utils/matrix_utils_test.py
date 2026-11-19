"""
Unit tests for MatrixConverter.

Tests cover:
- Positional policy codes
- Cell dicts to `n x n` lists (missing cells become None) and back
"""

import unittest

import pytest

from utils.matrix_utils import MatrixConverter


@pytest.mark.unit
class TestMatrixConverter(unittest.TestCase):
    """Test cases for MatrixConverter."""

    def setUp(self):
        """Create the converter."""
        self.converter = MatrixConverter()

    def test_codes(self):
        """Test codes are P1 ... Pn whatever the names."""
        self.assertEqual(self.converter.codes(["Zeta", "Alpha", "Beta"]), ["P1", "P2", "P3"])

    def test_round_trip(self):
        """Test grid conversion keeps positions and fills gaps with None."""
        grid = self.converter.to_grid({(0, 0): 0.0, (0, 1): -0.0, (1, 0): 2.0}, 2)
        self.assertEqual(grid, [[0.0, -0.0], [2.0, None]])
        self.assertEqual(self.converter.to_cells([[1, 2], [3, 4]]), {(0, 0): 1, (0, 1): 2, (1, 0): 3, (1, 1): 4})
