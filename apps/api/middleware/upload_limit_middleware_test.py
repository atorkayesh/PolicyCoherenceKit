"""
Unit tests for UploadLimitMiddleware.

Tests cover:
- A declared `Content-Length` over the limit is a 413 envelope before the route runs
- Other paths and uploads within the limit pass through
"""

import unittest

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from errors.error_handlers import ErrorHandlers
from features.workbook_import_feature import WorkbookImportFeature
from middleware.upload_limit_middleware import UploadLimitMiddleware

PATH = "/api/v1/imports/workbook"


def _make_app(calls: list) -> FastAPI:
    """Create an app with a 100-byte limit whose routes record that they ran."""
    app = FastAPI()
    ErrorHandlers().register(app)
    app.add_middleware(UploadLimitMiddleware, feature=WorkbookImportFeature(max_bytes=100))

    @app.post(PATH)
    @app.post("/other")
    async def upload() -> dict:
        calls.append(True)
        return {}

    return app


@pytest.mark.unit
class TestUploadLimitMiddleware(unittest.TestCase):
    """Test cases for UploadLimitMiddleware."""

    def setUp(self):
        """Create the client."""
        self.calls = []
        self.client = TestClient(_make_app(self.calls))

    def test_declared_oversize_is_413(self):
        """Test the limit plus the multipart overhead is exceeded by one byte."""
        response = self.client.post(PATH, content=b"x" * (100 + 64 * 1024 + 1))

        self.assertEqual((response.status_code, response.json()["error"]["code"]), (413, "upload_too_large"))
        self.assertEqual(response.json()["message"], "The workbook is larger than 5 MB.")
        self.assertEqual(self.calls, [])

    def test_within_limit_and_other_paths_pass(self):
        """Test a body within the margin and another path reach the route."""
        self.assertEqual(self.client.post(PATH, content=b"x" * (100 + 64 * 1024)).status_code, 200)
        self.assertEqual(self.client.post("/other", content=b"x" * 200_000).status_code, 200)
        self.assertEqual(len(self.calls), 2)
