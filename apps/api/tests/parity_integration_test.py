"""
Numerical parity with the legacy Tk app, for every parity fixture, at feature level and through `POST /analysis`.

Tests cover:
- Aggregation (scores, ties, median labels and choice, method label, forced Average) and colour bands
- Coherence scores with band keys, entropy (with `-0.0`), centrality and its ranking, the network info bar
- PCA: `explained` exactly, coordinates and bounds per component up to a sign flip (degenerate cases: explained only)
- Insights rows, graph statistics, agreement, contested relations and system health
- Error fixtures: the public message follows the fixture's `api_message_rule`
"""

import unittest
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from features.analysis_feature import analysis_feature
from features.pca_feature import pca_feature
from main import app
from models.analysis_request_models import AnalysisRequest
from tests.parity_fixtures import parity_assertions as check
from tests.parity_fixtures import parity_fixtures

L2 = ("so they sum to exactly 1.0.", "so they sum to 1.0 (±0.01).")


def l11(text: str) -> str:
    """Apply the L11 arrow fix to a legacy message (`A -> B` and `P1->P2`)."""
    return text.replace(" -> ", " → ").replace("->", " → ")


@pytest.mark.integration
class TestAnalysisParity(unittest.TestCase):
    """Every analysis fixture, at feature level and over HTTP."""

    @classmethod
    def setUpClass(cls):
        """Create one client for the HTTP comparisons."""
        cls.client = TestClient(app)

    def test_feature_level(self):
        """Test `AnalysisFeature` reproduces every fixture."""
        for name, fixture in parity_fixtures.parity():
            with self.subTest(name):
                request = AnalysisRequest.model_validate(fixture["request"])
                self.compare(analysis_feature.analyze_sync(request).model_dump(mode="json"), fixture)

    def test_http(self):
        """Test `POST /analysis` reproduces every fixture."""
        for name, fixture in parity_fixtures.parity():
            with self.subTest(name):
                response = self.client.post("/api/v1/analysis", json=fixture["request"])
                self.assertEqual(response.status_code, 200, response.text)
                self.compare(response.json()["data"], fixture)

    def compare(self, data: Dict, fixture: Dict) -> None:
        """Compare one `AnalysisData` with one fixture."""
        self._aggregation(data["aggregation"], fixture)
        self._tables(data, fixture)
        result = analysis_feature.compute(AnalysisRequest.model_validate(fixture["request"])).run.result
        self._pca(data["pca"], fixture["pca"], pca_feature.unrounded_explained(result))
        self._network(data["network"], fixture)
        self._insights(data["insights"], fixture)

    def _aggregation(self, agg: Dict, fixture: Dict) -> None:
        legacy = fixture["aggregation"]
        self.assertEqual(agg["method"], legacy["method"])
        self.assertEqual(agg["method_label"], legacy["label"])
        self.assertEqual(agg["requested_method"], legacy["requested_method"])
        self.assertEqual(agg["method_forced"], legacy["decision_makers"] < 3)
        self.assertEqual(agg["median_choice"], legacy["median_even_choice"])
        self.assertEqual(agg["decision_makers"], legacy["decision_maker_names"])
        self.assertEqual(agg["decision_maker_count"], legacy["decision_makers"])
        self.assertEqual((agg["policies"], agg["codes"]), (legacy["policies"], legacy["codes"]))
        check.floats(agg["scores"], legacy["scores"], where="scores")
        self.assertEqual(agg["ordinal_cells"], legacy["ordinal_cells"])
        ties = [(t["row"], t["col"], [o["label"] for o in t["tied_options"]], t["chosen"]) for t in agg["ties"]]
        expected = [(t["row"], t["col"], t["tied_labels"], t["chosen"]) for t in legacy["ties"]]
        self.assertEqual(ties, expected)
        self.assertTrue(agg["ready"])
        self.assertEqual(agg["bands"], fixture["bands"])
        if legacy["method"] == "weighted":
            self.assertEqual(agg["weights"], fixture["request"]["aggregation"]["weights"])

    def _tables(self, data: Dict, fixture: Dict) -> None:
        n = fixture["aggregation"]["n"]
        for row, legacy in zip(data["coherence_scores"], fixture["scores"], strict=True):
            self.assertEqual(
                [row[k] for k in ("code", "policy", "oi", "ii")], [legacy[k] for k in ("code", "policy", "oi", "ii")]
            )
            check.floats([row["woi"], row["wii"]], [legacy["woi"], legacy["wii"]], where="woi/wii")
            self.assertEqual(row["oi_band"], check.count_band(legacy["oi_colour"], n))
            self.assertEqual(row["ii_band"], check.count_band(legacy["ii_colour"], n))
            self.assertEqual(row["woi_band"], check.value_band(legacy["woi_colour"]))
            self.assertEqual(row["wii_band"], check.value_band(legacy["wii_colour"]))
        entropy = data["range_of_influence"]
        self.assertEqual(entropy["hmax"], fixture["entropy"][0]["hmax"])
        check.floats([r["entropy"] for r in entropy["rows"]], [r["entropy"] for r in fixture["entropy"]], where="H")
        self.assertEqual([r["category"] for r in entropy["rows"]], [r["category"] for r in fixture["entropy"]])

    def _pca(self, pca: Dict, legacy: Dict, unrounded) -> None:
        self.assertEqual(pca["valid"], legacy["valid"])
        check.explained(pca["explained"], unrounded, legacy)
        if not legacy["valid"]:
            self.assertEqual((pca["points"], pca["bounds"]), ([], None))
            self.assertEqual(pca["message"], "PCA requires at least 3 policies.")
            return
        p1, p2 = pca["explained"]
        self.assertEqual(pca["total_explained"], round(p1 + p2, 1))
        self.assertEqual((pca["x_axis_label"], pca["y_axis_label"]), (f"PC1 ({p1}%)", f"PC2 ({p2}%)"))
        self.assertEqual(pca["stats_text"], f"PC1: {p1}%   PC2: {p2}%   Total explained: {round(p1 + p2, 1)}%")
        if parity_fixtures.is_degenerate(legacy["singular_values"]):
            return
        coords = [[p["x"], p["y"]] for p in pca["points"]]
        expected = check.aligned_pca(coords, legacy["coords"])
        check.floats(coords, expected, where="pca")
        xs, ys = [c[0] for c in expected], [c[1] for c in expected]
        bounds = [min(xs), max(xs) if max(xs) - min(xs) else min(xs) + 1.0]
        bounds += [min(ys), max(ys) if max(ys) - min(ys) else min(ys) + 1.0]
        b = pca["bounds"]
        check.floats([b["x_min"], b["x_max"], b["y_min"], b["y_max"]], bounds, where="pca bounds")

    def _network(self, network: Dict, fixture: Dict) -> None:
        edges = [[e["source"], e["target"], e["score"]] for e in network["edges"]]
        check.floats(edges, fixture["graph_edges"], where="edges")
        legacy = fixture["centrality"]
        check.floats(
            [[r["betweenness"], r["closeness"]] for r in network["centrality"]],
            [[r["betweenness"], r["closeness"]] for r in legacy],
            where="centrality",
        )
        self.assertEqual(network["centrality_ranking"], fixture["centrality_ranking"])
        info = fixture["network_info"]
        self.assertEqual(
            (network["edge_count"], network["isolated_count"], network["density"], network["stats_text"]),
            (info["edge_count"], info["isolated"], info["density"], info["stats_text"]),
        )

    def _insights(self, insights: Dict, fixture: Dict) -> None:
        legacy = fixture["insights"]
        keys = ["net", "prominence", "entropy", "betweenness", "closeness", "woi", "wii"]
        check.floats([[r[k] for k in keys] for r in insights["rows"]], [[r[k] for k in keys] for r in legacy["rows"]])
        self.assertEqual(
            [r["entropy_category"] for r in insights["rows"]], [r["entropy_category"] for r in legacy["rows"]]
        )
        roles = [
            "driver" if r["net"] > 0.05 else "dependent" if r["net"] < -0.05 else "balanced" for r in legacy["rows"]
        ]
        self.assertEqual([r["role"] for r in insights["rows"]], roles)
        graph = dict(legacy["graph"])
        self.assertEqual(insights["graph"], graph)
        agreement = legacy["agreement"]
        check.floats(
            [insights["agreement"]["average_agreement"], insights["agreement"]["average_correlation"]],
            [agreement["average_agreement"], agreement["average_correlation"]],
            where="agreement",
        )
        fields = ["i", "j", "score", "agreement_ratio", "spread"]
        actual = insights["agreement"]["contested"]
        self.assertEqual(
            [[c[k] for k in fields] for c in actual], [[c[k] for k in fields] for c in agreement["contested"]]
        )
        self.assertEqual([c["pair"] for c in actual], [l11(c["pair"]) for c in agreement["contested"]])
        self.assertEqual(insights["health"], fixture["texts"]["health"])


@pytest.mark.integration
class TestErrorParity(unittest.TestCase):
    """Each error fixture's input gives the public message its `api_message_rule` defines."""

    @classmethod
    def setUpClass(cls):
        """Create one client."""
        cls.client = TestClient(app)

    def expected(self, fixture: Dict) -> str:
        """The API message for a legacy message under the fixture's rule."""
        message = fixture["error_message"]
        if fixture["api_message_rule"] == "identical_except_L2":
            return message.replace(*L2)
        if fixture["api_message_rule"] == "identical_after_L11":
            return l11(message)
        return message

    def test_error_fixtures(self):
        """Test every replayable error fixture over HTTP."""
        replayed = 0
        for name, fixture in parity_fixtures.errors():
            if fixture["api_message_rule"] == "documentation":
                continue
            with self.subTest(name):
                body = self.replay(fixture)
                self.assertEqual(body["message"], self.expected(fixture))
                self.assertEqual((body["data"] or {}).get("title"), fixture["title"])
                replayed += 1
        self.assertGreaterEqual(replayed, 16)

    def replay(self, fixture: Dict) -> Dict:
        """Send the fixture input to the endpoint the user path maps to; return the first error."""
        if "setup" in fixture:
            response = self.client.post("/api/v1/setup/validate", json=fixture["setup"])
            self.assertEqual(response.status_code, 422, response.text)
            return response.json()
        if "request" in fixture:
            response = self.client.post("/api/v1/analysis", json=fixture["request"])
            self.assertEqual(response.status_code, 422, response.text)
            return response.json()
        body = {"decision_makers": fixture["decision_makers"], "weights": fixture["raw_weights"]}
        error = self.client.post("/api/v1/weights/check", json=body).json()["data"]["first_error"]
        return {"message": error["message"], "data": {"title": error["title"]}}
