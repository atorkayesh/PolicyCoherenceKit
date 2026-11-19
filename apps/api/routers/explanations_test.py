"""
Unit tests for the explanations router.

Tests cover:
- Success through a mocked feature; the provider catalogue
- 422s (missing key, unknown provider, an invalid analysis) never contain the API key in the body or the logs
- The PDF export: download name, empty text, and a header that would inject markup (L6)
"""

import unittest
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from models.explanation_models import ExplanationData
from tests.parity_fixtures import parity_fixtures

KEY = "sk-very-secret-key"


@pytest.mark.unit
class TestExplanationsRouter(unittest.TestCase):
    """Test cases for the explanations router."""

    def setUp(self):
        """Create the client and a request."""
        self.client = TestClient(app)
        self.body = {"analysis": parity_fixtures.parity_case("r5x3__average")["request"], "provider": "Groq"}

    @patch("routers.explanations.explanation_feature.explain", new_callable=AsyncMock)
    def test_success(self, explain):
        """Test the response data."""
        explain.return_value = ExplanationData(text="Text", provider="Groq", model="m")
        response = self.client.post("/api/v1/explanations", json={**self.body, "api_key": KEY})
        self.assertEqual(response.json()["data"], {"text": "Text", "provider": "Groq", "model": "m"})

    def test_missing_key(self):
        """Test the legacy message for a blank key (L9)."""
        response = self.client.post("/api/v1/explanations", json={**self.body, "api_key": " "})
        self.assertEqual(
            (response.status_code, response.json()["message"]), (422, "Please enter your API key before generating.")
        )

    def test_validation_error_hides_key(self):
        """Test an invalid request never echoes or logs the key."""
        with self.assertLogs(level="INFO") as logs:
            response = self.client.post(
                "/api/v1/explanations", json={**self.body, "provider": "Claude", "api_key": KEY, "model": [KEY]}
            )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(KEY, response.text)
        self.assertNotIn(KEY, "\n".join(logs.output))

    def test_providers(self):
        """Test the catalogue lists Anthropic with its cheap default and Azure as free text."""
        response = self.client.get("/api/v1/explanations/providers")
        providers = {p["id"]: p for p in response.json()["data"]["providers"]}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(providers["Anthropic"]["default_model"], "claude-haiku-5-5")
        self.assertTrue(providers["Azure OpenAI"]["free_text_model"])
        self.assertFalse(providers["Groq"]["free_text_model"])

    def test_unlisted_model(self):
        """Test a model outside the provider's list is a 422 with a stable code."""
        response = self.client.post("/api/v1/explanations", json={**self.body, "api_key": KEY, "model": "gpt-x"})
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (422, "unsupported_model"))

    def test_invalid_azure_deployment(self):
        """Test an Azure deployment name outside the URL-safe pattern is a 422 with a clear message."""
        azure = {
            **self.body,
            "provider": "Azure OpenAI",
            "api_key": KEY,
            "azure_endpoint": "https://r.openai.azure.com",
        }
        for model in ("../x", "a b", "a" * 65):
            response = self.client.post("/api/v1/explanations", json={**azure, "model": model})
            self.assertEqual(
                (response.status_code, response.json()["error"]["code"]), (422, "invalid_azure_deployment")
            )
            self.assertIn("letters, digits", response.json()["message"])

    def test_other_providers_skip_the_deployment_pattern(self):
        """Test the pattern only applies to Azure (OpenRouter models contain '/')."""
        response = self.client.post("/api/v1/explanations", json={**self.body, "api_key": KEY, "model": "a/b"})
        self.assertEqual(response.json()["error"]["code"], "unsupported_model")

    def test_analysis_error_hides_key(self):
        """Test a 422 from the analysis (blank project name) never echoes or logs the key."""
        body = {**self.body, "analysis": {**self.body["analysis"], "project_name": " "}, "api_key": KEY}
        with self.assertLogs(level="INFO") as logs:
            response = self.client.post("/api/v1/explanations", json=body)
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (422, "invalid_setup"))
        self.assertNotIn(KEY, response.text)
        self.assertNotIn(KEY, "\n".join(logs.output))

    def test_pdf_export(self):
        """Test the PDF download, its name, and that a markup header renders as text (reportlab fetches nothing)."""
        text = '## <img src="http://127.0.0.1/"> & Co\n\n1. Overall\nBody <b> & text'
        response = self.client.post("/api/v1/explanations/export/pdf", json={"text": text})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn('filename="policy_interpretation.pdf"', response.headers["content-disposition"])

    def test_pdf_export_empty(self):
        """Test empty text is rejected with the legacy message."""
        response = self.client.post("/api/v1/explanations/export/pdf", json={"text": ""})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["message"], "Generate an interpretation first.")
        self.assertEqual(response.json()["error"]["code"], "empty_interpretation")
