"""
Unit tests for ExcelStyler.

Tests cover:
- Text cells are strings even when they look like formulas (L15); numbers stay numbers
- The header style and `auto_width` (longest truthy value + 4, at least 14)
"""

import unittest

import pytest
from openpyxl import Workbook

from utils.excel_style_utils import ExcelStyler


@pytest.mark.unit
class TestExcelStyler(unittest.TestCase):
    """Test cases for ExcelStyler."""

    def setUp(self):
        """Create a worksheet."""
        self.styler = ExcelStyler()
        self.ws = Workbook().active

    def test_text_is_never_a_formula(self):
        """Test `=1+1` is stored as text and numbers keep their type."""
        self.assertEqual(self.styler.cell(self.ws, 1, 1, "=1+1").data_type, "s")
        self.assertEqual(self.styler.cell(self.ws, 1, 2, -0.0).data_type, "n")

    def test_header(self):
        """Test white bold text on navy, centred."""
        cell = self.styler.header(self.ws, 1, 1, "Code")
        self.assertTrue(cell.font.b)
        self.assertEqual((cell.fill.fgColor.rgb, cell.font.color.rgb), ("002C4A6E", "00FFFFFF"))
        self.assertEqual(cell.alignment.horizontal, "center")

    def test_auto_width(self):
        """Test widths: minimum 14, otherwise the longest truthy value plus 4 (zero values skipped)."""
        self.styler.cell(self.ws, 1, 1, "x" * 20)
        self.styler.cell(self.ws, 1, 2, 0.0)
        self.styler.auto_width(self.ws)
        self.assertEqual((self.ws.column_dimensions["A"].width, self.ws.column_dimensions["B"].width), (24, 14))
