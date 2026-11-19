"""Unit tests for the aggregation router: the preview keeps open ties."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestAggregationRouter(unittest.TestCase):
    """Test cases for the aggregation router."""

    def test_preview(self):
        """Test a majority request without tie choices."""
        body = parity_fixtures.parity_case("r5x3__majority_first")["request"]
        body["aggregation"]["tie_choices"] = []
        data = TestClient(app).post("/api/v1/aggregation/preview", json=body).json()["data"]
        self.assertFalse(data["ready"])
        self.assertTrue(data["ties"])
