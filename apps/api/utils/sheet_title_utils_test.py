"""
Unit tests for SheetTitleBuilder (L3).

Tests cover:
- Result titles stay within 31 characters for every method
- Forbidden characters, quotes, empty names, truncation and case-insensitive de-duplication
"""

import unittest

import pytest

from utils.sheet_title_utils import SheetTitleBuilder


@pytest.mark.unit
class TestSheetTitleBuilder(unittest.TestCase):
    """Test cases for SheetTitleBuilder."""

    def setUp(self):
        """Create the builder."""
        self.builder = SheetTitleBuilder()

    def test_result_titles_fit(self):
        """Test the longest title is `Range Influence (Majority Rule)` at 31 characters."""
        for label in ("Average", "Median", "Median Lower", "Median Upper", "Majority Rule", "Weighted"):
            self.assertTrue(all(len(t) <= 31 for t in self.builder.result_titles(label)))
        self.assertEqual(len("Range Influence (Majority Rule)"), 31)
        self.assertIn("Range Influence (Majority Rule)", self.builder.result_titles("Majority Rule"))

    def test_clean(self):
        """Test character replacement, quote stripping, the empty fallback and truncation."""
        self.assertEqual(self.builder.clean("a\\b/c?d*e[f]g:h"), "a_b_c_d_e_f_g_h")
        self.assertEqual(self.builder.clean("'quoted'"), "quoted")
        self.assertEqual(self.builder.clean("''"), "Sheet")
        self.assertEqual(len(self.builder.clean("x" * 40)), 31)

    def test_deduplication(self):
        """Test reserved titles win and duplicates get ` (2)`, ` (3)` within 31 characters."""
        titles = self.builder.decision_maker_titles(
            ["coh scores (average)", "Dup", "dup", "DUP", "y" * 40, "y" * 35], ["Coh Scores (Average)"]
        )
        self.assertEqual(titles[:4], ["coh scores (average) (2)", "Dup", "dup (2)", "DUP (3)"])
        self.assertEqual(titles[4], "y" * 31)
        self.assertEqual(titles[5], "y" * 27 + " (2)")
