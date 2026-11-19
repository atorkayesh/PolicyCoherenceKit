"""Unit tests for the analysis router: success, and the 422 for incomplete matrices with its title."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestAnalysisRouter(unittest.TestCase):
    """Test cases for the analysis router."""

    def test_analysis(self):
        """Test success and a blank cell."""
        client = TestClient(app)
        body = parity_fixtures.parity_case("r5x3__average")["request"]
        self.assertEqual(client.post("/api/v1/analysis", json=body).status_code, 200)
        body["decision_makers"][1]["ratings"][2][0] = ""
        response = client.post("/api/v1/analysis", json=body)
        self.assertEqual((response.status_code, response.json()["data"]["title"]), (422, "Incomplete Matrices"))
        self.assertNotIn("Traceback", response.text)

    def test_method_forced_below_three(self):
        """Test `/analysis` reports `method_forced` for one decision-maker with a requested Average."""
        body = parity_fixtures.parity_case("example__average")["request"]
        data = TestClient(app).post("/api/v1/analysis", json=body).json()["data"]["aggregation"]
        self.assertEqual(
            (data["requested_method"], data["method"], data["method_forced"]), ("average", "average", True)
        )
