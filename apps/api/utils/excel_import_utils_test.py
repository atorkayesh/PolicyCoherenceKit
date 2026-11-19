"""
Unit tests for WorkbookReader (hardening and the new header rules; legacy parity is in
`tests/import_parity_integration_test.py`).

Tests cover:
- Non-workbook bytes, an oversized zip entry and a chartsheet → `invalid_workbook`
- More than 50 sheets and a header wider than 100 policies → `invalid_import`
- A header gap and duplicate policies; trailing blank header cells are not gaps
"""

import io
import unittest
import zipfile

import pytest
from openpyxl import Workbook

from errors.import_errors import InvalidImportError, InvalidWorkbookError
from utils.excel_import_utils import WorkbookReader


def workbook(sheets=1, header=("A", "B"), chart=False) -> bytes:
    """Build workbook bytes with square Neutral sheets."""
    wb = Workbook()
    wb.remove(wb.active)
    for k in range(sheets):
        ws = wb.create_sheet(f"S{k}")
        ws.append([None, *header])
        for name in header:
            ws.append([name, *["Neutral"] * len(header)])
    if chart:
        wb.create_chartsheet("Chart")
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.mark.unit
class TestWorkbookReader(unittest.TestCase):
    """Test cases for WorkbookReader."""

    def setUp(self):
        """Create the reader."""
        self.reader = WorkbookReader()

    def test_unreadable_and_bombs(self):
        """Test garbage, a zip entry over 50 MB uncompressed, and a chartsheet."""
        bomb = io.BytesIO()
        with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("xl/big.xml", b"\0" * (50 * 1024 * 1024 + 1))
        for content in (b"not a workbook", bomb.getvalue(), workbook(chart=True)):
            with self.assertRaises(InvalidWorkbookError) as raised:
                self.reader.read(content)
            self.assertEqual(
                raised.exception.public_message, "The file could not be read as an Excel workbook (.xlsx)."
            )

    def test_limits(self):
        """Test the sheet limit (checked before parsing) and the policy limit."""
        with self.assertRaises(InvalidImportError) as raised:
            self.reader.read(workbook(sheets=51))
        self.assertEqual(raised.exception.public_message, "The workbook has more than 50 sheets.")
        with self.assertRaises(InvalidImportError) as raised:
            self.reader.read(workbook(header=[f"P{k}" for k in range(101)]))
        self.assertEqual(raised.exception.public_message, "Please enter at most 100 policy names.")

    def test_header_rules(self):
        """Test the gap message, the duplicate message, and that trailing blanks are allowed."""
        warnings = {"skipped": [], "blank_cells": []}
        rows = [(None, "A", None, "B"), ("A", "Neutral", None, "Enabling"), ("B", "Enabling", None, "Neutral")]
        with self.assertRaises(InvalidImportError) as raised:
            self.reader.parse_sheet("S", rows, warnings)
        self.assertEqual(raised.exception.public_message, 'Sheet "S": header row has a blank policy name in column C.')
        dup = [(None, "A", "A"), ("A", "Neutral", "Enabling"), ("A", "Enabling", "Neutral")]
        with self.assertRaises(InvalidImportError) as raised:
            self.reader.parse_sheet("S", dup, warnings)
        self.assertEqual(raised.exception.public_message, 'Sheet "S": Policy names must be unique.')
        trailing = [(None, "A", "B", None), ("A", "Neutral", "Enabling", None), ("B", "Enabling", "Neutral", None)]
        self.assertEqual(
            self.reader.parse_sheet("S", trailing, warnings).ratings, [["Neutral", "Enabling"], ["Enabling", "Neutral"]]
        )
