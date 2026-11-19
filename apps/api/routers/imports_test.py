"""Unit tests for the imports router: the bundled example workbook imports."""

import unittest
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

EXAMPLE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "imports" / "wef_nexus_example.xlsx"


@pytest.mark.unit
class TestImportsRouter(unittest.TestCase):
    """Test cases for the imports router."""

    def test_example(self):
        """Test the example with a matching `policies` field."""
        policies = [f"P{k}" for k in range(1, 15)]
        response = TestClient(app).post(
            "/api/v1/imports/workbook",
            files={"file": ("WEF Nexus Example.xlsx", EXAMPLE.read_bytes())},
            data={"policies": policies},
        )
        data = response.json()["data"]
        self.assertEqual((data["imported_count"], data["matrices"][0]["decision_maker"]), (1, "Research Team"))
