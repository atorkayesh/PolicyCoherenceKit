"""
Exact-text parity of the Results Insights texts with the legacy app, for every parity fixture.

The raw legacy text gets only the literal label-fix replacements below (plan Phase 9.2), nothing else:
- L11: `" -> "` becomes `" → "` (the Most Contested `↔` is unchanged; tags already use `→`)
- L12: Most Contested value `Agreement: ` becomes `Rating agreement: `
- L13: `reinforcing relationship` / `constraining relationship` become `positive link` / `negative link`;
  ` Reinforcing)` / ` Constraining)` become `, positive)` / `, negative)`; card value ` Reinforcing` becomes
  ` positive link`
- L14: no ported text states a decision-maker count, so nothing is replaced
"""

import unittest
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from features.analysis_feature import analysis_feature
from main import app
from models.analysis_request_models import AnalysisRequest
from tests.parity_fixtures import parity_fixtures

STORY_FIXES = [
    (" -> ", " → "),
    ("through the reinforcing relationship ", "through the positive link "),
    ("through the constraining relationship ", "through the negative link "),
    (" Reinforcing)", ", positive)"),
    (" Constraining)", ", negative)"),
]


def fixed(text: str, replacements=STORY_FIXES) -> str:
    """Apply literal before → after replacements."""
    for before, after in replacements:
        text = text.replace(before, after)
    return text


def expected_texts(legacy: Dict) -> Dict:
    """The API texts expected from the raw legacy texts."""
    cards = legacy["cards"]
    link = cards["strongest_link"]
    contested = cards["most_contested"]
    conflict = cards["conflict_ratio"]
    prefix, _, detail = legacy["interpretation"].partition(" ")
    return {
        "story": fixed(legacy["story"]),
        "interpretation_label": prefix,
        "interpretation_text": detail,
        "overview_agreement_text": legacy["overview"]["agreement"],
        "tag_top_driver": legacy["tags"]["top_driver"],
        "tag_strongest_link": legacy["tags"]["strongest_link"],
        "tag_contested": legacy["tags"]["contested"],
        "top_driver": {k: cards["top_driver"][k] for k in ("hero", "value_text")},
        "top_dependent": {k: cards["top_dependent"][k] for k in ("hero", "value_text")},
        "strongest_link": {
            "main": fixed(link["main"], [(" -> ", " → ")]),
            "value_text": fixed(link["value_text"], [(" Reinforcing", " positive link")]),
            "caption": link["caption"],
        },
        "most_contested": {
            "main": contested["main"],
            "value_text": fixed(contested["value_text"], [("Agreement: ", "Rating agreement: ")]),
            "caption": contested["caption"],
        },
        "conflict": (conflict["main"], conflict["value_text"], conflict["caption"]),
    }


@pytest.mark.integration
class TestInsightsTextParity(unittest.TestCase):
    """Story, interpretation, tags and card texts."""

    def compare(self, texts: Dict, legacy: Dict) -> None:
        """Compare the API texts with the fixed legacy texts."""
        expected = expected_texts(legacy)
        conflict = texts.pop("conflict_ratio")
        self.assertEqual((conflict["main_text"], conflict["value_text"], conflict["caption"]), expected.pop("conflict"))
        self.assertEqual(texts, expected)

    def test_feature_level(self):
        """Test the texts built by `AnalysisFeature`."""
        for name, fixture in parity_fixtures.parity():
            with self.subTest(name):
                data = analysis_feature.analyze_sync(AnalysisRequest.model_validate(fixture["request"]))
                self.compare(data.insights.texts.model_dump(mode="json"), fixture["texts"])

    def test_http(self):
        """Test the texts returned by `POST /analysis`."""
        client = TestClient(app)
        for name, fixture in parity_fixtures.parity():
            with self.subTest(name):
                data = client.post("/api/v1/analysis", json=fixture["request"]).json()["data"]
                self.compare(data["insights"]["texts"], fixture["texts"])

    def test_strongest_link_suffix_and_sign_wording(self):
        """Test L13 is exercised by the fixtures: a negative-link story and a `, positive)` suffix exist."""
        stories = [fixed(f["texts"]["story"]) for _, f in parity_fixtures.parity()]
        self.assertTrue(any("through the negative link " in story for story in stories))
        self.assertTrue(any(", positive)" in story for story in stories))
        self.assertFalse(any("->" in story or "Reinforcing" in story for story in stories))
