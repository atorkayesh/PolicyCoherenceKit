"""Unit tests for the setup router: valid forms, and 422 `invalid_setup` with title and field."""

import unittest

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.unit
class TestSetupRouter(unittest.TestCase):
    """Test cases for the setup router."""

    def test_validate(self):
        """Test success and the legacy error."""
        client = TestClient(app)
        ok = client.post("/api/v1/setup/validate", json={"policies": ["A", "B"]}).json()["data"]
        self.assertEqual(ok["codes"], ["P1", "P2"])
        response = client.post("/api/v1/setup/validate", json={"policies": ["A"]})
        body = response.json()
        self.assertEqual((response.status_code, body["error"]["code"]), (422, "invalid_setup"))
        self.assertEqual(body["data"], {"title": "Too Few Policies", "field": "policies"})
