"""
Import parity with the legacy importer and app flow, for every import fixture.

Tests cover:
- Matrices (blank cells `""`, Neutral diagonal) and warnings grouped by kind (L4), with the L11 arrow
- Legacy errors (header mismatch, unrecognised values) and the app's policy-list mismatch, verbatim after L11
- Gap-column and duplicate-policy workbooks give the new `api_expected_error`
- The summary message is the first line of the legacy success or warning box
"""

import unittest
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from errors.app_error import AppError
from features.workbook_import_feature import workbook_import_feature
from main import app
from tests.parity_fixtures import parity_fixtures

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def l11(text: str) -> str:
    """The L11 arrow in importer messages (`P1->P2`)."""
    return text.replace("->", " → ")


@pytest.mark.integration
class TestImportParity(unittest.TestCase):
    """Every import fixture through the feature and over HTTP."""

    def expected_error(self, fixture: Dict):
        """The API error message the fixture expects, or None for a successful import."""
        if "api_expected_error" in fixture:
            return fixture["api_expected_error"]
        if "error_message" in fixture["legacy"]:
            return l11(fixture["legacy"]["error_message"])
        title, message = fixture["app_messages"][0]
        return message if title == "Policy List Mismatch" else None

    def check_success(self, data: Dict, fixture: Dict) -> None:
        """Compare an import with the legacy result."""
        legacy = fixture["legacy"]
        self.assertEqual(
            [m["decision_maker"] for m in data["matrices"]], [m["decision_maker"] for m in legacy["matrices"]]
        )
        self.assertEqual([m["ratings"] for m in data["matrices"]], [m["ratings"] for m in legacy["matrices"]])
        self.assertEqual(data["policies"], legacy["matrices"][0]["policies"])
        warnings = [l11(w) for w in legacy["warnings"]]
        groups = {g["kind"]: g["messages"] for g in data["warning_groups"]}
        self.assertEqual(groups.get("skipped", []), [w for w in warnings if w.endswith("skipped.")])
        self.assertEqual(groups.get("blank_cells", []), [w for w in warnings if not w.endswith("skipped.")])
        self.assertEqual(data["summary_message"], fixture["app_messages"][0][1].split("\n")[0])

    def test_feature(self):
        """Test `import_bytes` for every fixture."""
        for name, fixture, content in parity_fixtures.imports():
            with self.subTest(name):
                expected = self.expected_error(fixture)
                if expected is None:
                    data = workbook_import_feature.import_bytes(content, f"{name}.xlsx", None, None)
                    self.check_success(data.model_dump(mode="json"), fixture)
                    self.assertEqual(data.suggested_project_name, name)
                else:
                    with self.assertRaises(AppError) as raised:
                        workbook_import_feature.import_bytes(content, f"{name}.xlsx", None, None)
                    self.assertEqual(raised.exception.public_message, expected)

    def test_http(self):
        """Test `POST /imports/workbook` for every fixture."""
        client = TestClient(app)
        for name, fixture, content in parity_fixtures.imports():
            with self.subTest(name):
                response = client.post("/api/v1/imports/workbook", files={"file": (f"{name}.xlsx", content, XLSX)})
                expected = self.expected_error(fixture)
                if expected is None:
                    self.assertEqual(response.status_code, 200, response.text)
                    self.check_success(response.json()["data"], fixture)
                else:
                    self.assertEqual(response.status_code, 422, response.text)
                    self.assertEqual(response.json()["message"], expected)
