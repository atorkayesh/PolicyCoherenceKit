"""Unit tests for the analysis export router: the XLSX media type."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.parity_fixtures import parity_fixtures


@pytest.mark.unit
class TestAnalysisExportRouter(unittest.TestCase):
    """Test cases for the analysis export router."""

    def test_export(self):
        """Test the response type."""
        response = TestClient(app).post(
            "/api/v1/analysis/export/xlsx", json=parity_fixtures.parity_case("two2x1__average")["request"]
        )
        self.assertEqual(
            response.headers["content-type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
