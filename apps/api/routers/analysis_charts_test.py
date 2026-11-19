"""Unit tests for the analysis charts router: layout query parameter and an unknown layout."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestAnalysisChartsRouter(unittest.TestCase):
    """Test cases for the analysis charts router."""

    def test_layouts(self):
        """Test a valid and an unknown layout."""
        client = TestClient(app)
        body = parity_fixtures.parity_case("r5x3__average")["request"]
        data = client.post("/api/v1/analysis/charts/network?layout=spectral&focus=1", json=body).json()["data"]
        self.assertEqual((data["layout"], data["focus"], data["nodes"][0]["index"]), ("spectral", 1, 1))
        self.assertEqual(
            client.post("/api/v1/analysis/charts/network?layout=radial", json=body).json()["error"]["code"],
            "validation_error",
        )
