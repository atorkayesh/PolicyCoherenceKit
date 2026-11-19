"""Unit tests for the matrices router: completeness with blanks, and the validation order of requests."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.unit
class TestMatricesRouter(unittest.TestCase):
    """Test cases for the matrices router."""

    def test_check(self):
        """Test blanks are allowed and setup errors come before rating errors."""
        client = TestClient(app)
        body = {
            "project_name": "P",
            "policies": ["A", "B"],
            "decision_makers": [{"name": "X", "ratings": [["", ""], ["Enabling", ""]]}],
        }
        data = client.post("/api/v1/matrices/check", json=body).json()["data"]
        self.assertEqual((data["complete"], data["decision_makers"][0]["blank_count"]), (False, 1))
        bad = {**body, "policies": ["A", "A"], "decision_makers": [{"name": "X", "ratings": [["bad"]]}]}
        self.assertEqual(
            client.post("/api/v1/matrices/check", json=bad).json()["message"], "Policy names must be unique."
        )
        shape = {**body, "decision_makers": [{"name": "X", "ratings": [["Neutral"]]}]}
        response = client.post("/api/v1/matrices/check", json=shape)
        self.assertEqual(
            (response.json()["error"]["code"], response.json()["message"]),
            ("invalid_ratings", 'Ratings for "X" must be 2 x 2.'),
        )
