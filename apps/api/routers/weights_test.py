"""Unit tests for the weights router: always 200 with the dialog messages."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.unit
class TestWeightsRouter(unittest.TestCase):
    """Test cases for the weights router."""

    def test_check(self):
        """Test an invalid input still answers 200."""
        response = TestClient(app).post("/api/v1/weights/check", json={"decision_makers": ["A"], "weights": [None]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["first_error"]["title"], "Missing Weight")
