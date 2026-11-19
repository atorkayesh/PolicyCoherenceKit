"""
Unit tests for WorkbookImportFeature.

Tests cover:
- `.xls` and other extensions → `unsupported_file` (L5); uploads over 5 MB → 413 while streaming;
  a declared `Content-Length` over the limit + overhead → 413
- The `policies` reference, decision-maker clashes, empty or colliding trimmed sheet names, nothing imported
- Summary messages and the suggested project name
"""

import io
import unittest

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from errors.import_errors import (
    ExistingDecisionMakersError,
    InvalidImportError,
    NothingImportedError,
    PolicyListMismatchError,
    UploadTooLargeError,
)
from features.workbook_import_feature import WorkbookImportFeature
from main import app

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def workbook(names=("Expert A",), header=("Alpha", "Beta")) -> bytes:
    """One complete sheet per name."""
    wb = Workbook()
    wb.remove(wb.active)
    for name in names:
        ws = wb.create_sheet(name)
        ws.append([None, *header])
        for i, policy in enumerate(header):
            ws.append([policy, *["Neutral" if i == j else "Enabling" for j in range(len(header))]])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.mark.unit
class TestWorkbookImportFeature(unittest.TestCase):
    """Test cases for WorkbookImportFeature."""

    def setUp(self):
        """Create the feature and a client."""
        self.feature = WorkbookImportFeature()
        self.client = TestClient(app)

    def post(self, content: bytes, filename: str = "Plan.xlsx", **data):
        """Upload a workbook."""
        return self.client.post("/api/v1/imports/workbook", files={"file": (filename, content, XLSX)}, data=data)

    def test_extension_and_size(self):
        """Test `.xls` is unsupported and a 5 MB + 1 byte upload is 413."""
        response = self.post(workbook(), "old.xls")
        self.assertEqual(
            (response.status_code, response.json()["message"]), (422, "Only .xlsx workbooks are supported.")
        )
        response = self.post(b"x" * (5 * 1024 * 1024 + 1))
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (413, "upload_too_large"))
        self.assertEqual(response.json()["message"], "The workbook is larger than 5 MB.")

    def test_content_length(self):
        """Test the declared size check: over limit + overhead raises; missing or malformed values pass."""
        feature = WorkbookImportFeature(max_bytes=10)
        for value in (None, "abc", str(10 + 64 * 1024)):
            feature.check_content_length(value)
        with self.assertRaises(UploadTooLargeError):
            feature.check_content_length(str(10 + 64 * 1024 + 1))

    def test_success(self):
        """Test a clean import, the summary and the suggested name."""
        data = self.post(workbook(), "WEF Nexus.xlsx").json()["data"]
        self.assertEqual(
            (data["imported_count"], data["summary_message"]), (1, "1 matrix/matrices imported successfully.")
        )
        self.assertEqual(
            (data["policies"], data["codes"], data["suggested_project_name"]),
            (["Alpha", "Beta"], ["P1", "P2"], "WEF Nexus"),
        )

    def test_reference_and_clash(self):
        """Test the `policies` field is the reference and existing decision-makers clash (sorted)."""
        with self.assertRaises(PolicyListMismatchError) as raised:
            self.feature.import_bytes(workbook(), "x.xlsx", ["Beta", "Alpha"], None)
        self.assertIn("  - Expert A", raised.exception.public_message)
        with self.assertRaises(ExistingDecisionMakersError) as raised:
            self.feature.import_bytes(workbook(("Expert B", "Expert A")), "x.xlsx", None, ["Expert B", "Expert A"])
        self.assertEqual(
            raised.exception.public_message,
            "These decision-maker names already exist in the project:\n\nExpert A\nExpert B",
        )

    def test_sheet_names(self):
        """Test sheet names that collide after trimming."""
        with self.assertRaises(InvalidImportError) as raised:
            self.feature.import_bytes(workbook(("A", "A ")), "x.xlsx", None, None)
        self.assertEqual(
            raised.exception.public_message, "Sheet names must be non-empty and unique after trimming spaces."
        )

    def test_nothing_imported(self):
        """Test a workbook of skipped sheets returns the warnings with the L4 heading."""
        with self.assertRaises(NothingImportedError) as raised:
            self.feature.import_bytes(workbook(header=("Only",)), "x.xlsx", None, None)
        group = raised.exception.data.warning_groups[0]
        self.assertEqual((group.kind, group.heading), ("skipped", "The following sheets were skipped:"))
