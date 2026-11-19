"""
Unit tests for ErrorEnvelopeMiddleware.

Tests cover:
- An unexpected exception becomes the standard 500 envelope with CORS headers for an allowed origin
- The app's CORS settings do not allow credentials
"""

import unittest

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from errors.error_handlers import ErrorHandlers
from main import app as main_app
from middleware.error_envelope_middleware import ErrorEnvelopeMiddleware

ORIGIN = "http://localhost:3001"


def _make_app() -> FastAPI:
    """Create an app ordered like `main.py` with a route that crashes."""
    app = FastAPI()
    ErrorHandlers().register(app)
    app.add_middleware(ErrorEnvelopeMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=[ORIGIN], allow_methods=["*"], allow_headers=["*"])

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("password=hunter2")

    return app


@pytest.mark.unit
class TestErrorEnvelopeMiddleware(unittest.TestCase):
    """Test cases for ErrorEnvelopeMiddleware."""

    def test_500_has_envelope_and_cors_headers(self):
        """Test an unexpected exception returns the 500 envelope with `Access-Control-Allow-Origin`."""
        client = TestClient(_make_app(), raise_server_exceptions=False)
        response = client.get("/crash", headers={"Origin": ORIGIN})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["access-control-allow-origin"], ORIGIN)
        self.assertEqual(response.json()["error"]["code"], "internal_error")
        self.assertNotIn("hunter2", response.text)

    def test_main_app_cors_without_credentials(self):
        """Test the API never allows credentialed CORS requests (it uses no cookies or auth)."""
        response = TestClient(main_app).get("/api/v1/health", headers={"Origin": ORIGIN})

        self.assertEqual(response.headers["access-control-allow-origin"], ORIGIN)
        self.assertNotIn("access-control-allow-credentials", response.headers)
