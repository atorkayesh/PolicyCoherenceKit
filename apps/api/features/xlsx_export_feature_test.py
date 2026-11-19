"""
Unit tests for XlsxExportFeature (layout parity is in `tests/xlsx_integration_test.py`).

Tests cover:
- The L10 download name and the sheet order for one run
"""

import unittest
from io import BytesIO

import pytest
from openpyxl import load_workbook

from features.xlsx_export_feature import XlsxExportFeature
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestXlsxExportFeature(unittest.IsolatedAsyncioTestCase):
    """Test cases for XlsxExportFeature."""

    async def test_export(self):
        """Test the name and sheets."""
        request = parity_fixtures.request("two2x3__weighted")
        request.project_name = "A/B plan"
        content, name = await XlsxExportFeature().export(request)
        self.assertEqual(name, "A_B_plan_coherence.xlsx")
        titles = load_workbook(BytesIO(content)).sheetnames
        self.assertEqual(
            titles[3:],
            ["Aggregated (Weighted)", "Coh Scores (Weighted)", "Range Influence (Weighted)", "Centrality (Weighted)"],
        )
