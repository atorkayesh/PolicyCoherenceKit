"""
XLSX export compared with the legacy `_export_to_excel` dump (current run only).

Tests cover:
- Sheet order, cell values, bold/italic, fills, font colours, number formats and column widths
- Titles mapped by L3 (`Avg` → `Average`, `Majority` → `Majority Rule`, `Median (Lower)` → `Median Lower`)
- The `dm_names` case (legacy crashes on `A/B`): L3 titles asserted directly
- Text cells are strings, never formulas (L15); the download name (L10)
"""

import unittest
from io import BytesIO
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from features.xlsx_export_feature import xlsx_export_feature
from main import app
from models.analysis_request_models import AnalysisRequest
from tests.parity_fixtures import parity_fixtures

CASES = {"r6x4__median_lower": "Median Lower", "r5x3__majority_first": "Majority Rule", "example__average": "Average"}
RESULT_TITLES = ["Aggregated ({})", "Coh Scores ({})", "Range Influence ({})", "Centrality ({})"]


def colour(value):
    """RGB string of an openpyxl colour, or None."""
    return value.rgb if value is not None and value.type == "rgb" else None


def dump(content: bytes) -> List[Dict]:
    """Same dump as `scripts/parity/xlsx_capture.py`."""
    sheets = []
    for ws in load_workbook(BytesIO(content)).worksheets:
        cells = []
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None and not cell.has_style:
                    continue
                fill = cell.fill.fgColor if cell.fill and cell.fill.fill_type == "solid" else None
                cells.append(
                    {
                        "ref": cell.coordinate,
                        "value": cell.value,
                        "bold": bool(cell.font.b),
                        "italic": bool(cell.font.i),
                        "fill": colour(fill),
                        "font_colour": colour(cell.font.color),
                        "number_format": cell.number_format,
                    }
                )
        widths = {letter: dim.width for letter, dim in sorted(ws.column_dimensions.items())}
        sheets.append({"title": ws.title, "cells": cells, "column_widths": widths})
    return sheets


@pytest.mark.integration
class TestXlsxExport(unittest.TestCase):
    """The API export against the legacy workbooks."""

    def test_matches_legacy_layout(self):
        """Test every XLSX fixture, sheet by sheet."""
        for name, label in CASES.items():
            with self.subTest(name):
                legacy = parity_fixtures.xlsx(name)["sheets"]
                sheets = dump(xlsx_export_feature.export_bytes(parity_fixtures.request(name)))
                dm_count = len(legacy) - 4
                titles = [s["title"] for s in legacy[:dm_count]] + [t.format(label) for t in RESULT_TITLES]
                self.assertEqual([s["title"] for s in sheets], titles)
                for actual, expected in zip(sheets, legacy, strict=True):
                    self.assertEqual(actual["cells"], expected["cells"], actual["title"])
                    self.assertEqual(actual["column_widths"], expected["column_widths"], actual["title"])

    def test_dm_names_titles(self):
        """Test L3 on names the legacy export crashes on, collides with or truncates."""
        fixture = parity_fixtures.xlsx("dm_names")
        self.assertIn("Invalid character / found in sheet title", fixture["error_message"])
        sheets = dump(xlsx_export_feature.export_bytes(AnalysisRequest.model_validate(fixture["request"])))
        self.assertEqual(
            [s["title"] for s in sheets],
            [
                "A_B",
                "Aggregated (Average) (2)",
                "Department of Energy Transition",
                "Department of Energy Transi (2)",
                *[t.format("Average") for t in RESULT_TITLES],
            ],
        )

    def test_text_cells_are_never_formulas(self):
        """Test a decision-maker and a policy named `=1+1` are written as strings (L15)."""
        body = parity_fixtures.parity_case("two2x1__average")["request"]
        body = {**body, "policies": ["=1+1", body["policies"][1]]}
        body["decision_makers"] = [{**body["decision_makers"][0], "name": "=1+1"}]
        wb = load_workbook(BytesIO(xlsx_export_feature.export_bytes(AnalysisRequest.model_validate(body))))
        ws = wb.worksheets[0]
        self.assertEqual(ws.title, "=1+1")
        self.assertEqual((ws["B1"].value, ws["B1"].data_type), ("P1: =1+1", "s"))
        scores = wb.worksheets[2]
        self.assertEqual((scores["B2"].value, scores["B2"].data_type), ("=1+1", "s"))

    def test_http_download(self):
        """Test the endpoint returns the workbook with the L10 file name."""
        response = TestClient(app).post(
            "/api/v1/analysis/export/xlsx", json=parity_fixtures.parity_case("example__average")["request"]
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["content-disposition"],
            'attachment; filename="WEF_Nexus_Example_coherence.xlsx"; '
            "filename*=UTF-8''WEF_Nexus_Example_coherence.xlsx",
        )
        self.assertEqual(response.content[:2], b"PK")
