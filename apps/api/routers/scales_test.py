"""Unit tests for the scales router: `GET /scales` returns the constants."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.unit
class TestScalesRouter(unittest.TestCase):
    """Test cases for the scales router."""

    def test_scales(self):
        """Test the response shape."""
        response = TestClient(app).get("/api/v1/scales")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["diagonal_label"], "Neutral")
