"""
Network layout and chart-data parity with the legacy canvas code, on the square 600 x 600 canvas.

Tests cover:
- Node positions per layout, full and ego view, at `atol=1e-6` px; node and edge order as `_redraw_network` and
  `_redraw_ego` build them; spectral fixtures marked `spectral_degenerate` are skipped (listed in AGENTS.md)
- Edge sign, colour, width and two-way flag; ego title, edge labels and the empty message (L8); the stats text
- 422 `invalid_focus_policy`; the `$5bn and $3bn` policy name verbatim in labels
"""

import unittest

import pytest
from fastapi.testclient import TestClient

from constants.chart_constants import NetworkLayout
from features.network_chart_data_feature import network_chart_data_feature
from main import app
from models.analysis_request_models import AnalysisRequest
from tests.parity_fixtures import LAYOUT_ATOL, parity_fixtures
from tests.parity_fixtures import parity_assertions as check


@pytest.mark.integration
class TestLayoutParity(unittest.TestCase):
    """Every layout fixture."""

    def test_positions_and_order(self):
        """Test positions, node order and edges against the legacy layouts."""
        compared = 0
        for name, fixture in parity_fixtures.layouts():
            with self.subTest(name):
                request = AnalysisRequest.model_validate(fixture["request"])
                data = network_chart_data_feature.chart_sync(
                    request, NetworkLayout(fixture["layout"]), fixture["focus"]
                )
                self.assertEqual([node.index for node in data.nodes], fixture["node_order"])
                check.floats([[e.source, e.target, e.score] for e in data.edges], fixture["edges"])
                if fixture["spectral_degenerate"]:
                    continue
                expected = [fixture["positions"][str(idx)] for idx in fixture["node_order"]]
                check.floats([[node.x, node.y] for node in data.nodes], expected, atol=LAYOUT_ATOL)
                compared += 1
        self.assertGreaterEqual(compared, 39)

    def test_full_network_fields(self):
        """Test colours, widths, two-way flags, fills and the stats line of the full network."""
        fixture = parity_fixtures.parity_case("r5x3__average")
        data = network_chart_data_feature.chart_sync(
            AnalysisRequest.model_validate(fixture["request"]), NetworkLayout.CIRCULAR, None
        )
        pairs = {(e.source, e.target) for e in data.edges}
        for edge in data.edges:
            self.assertEqual(edge.colour, "#1a6e3c" if edge.score > 0 else "#b71c1c")
            self.assertEqual(edge.width, 4.0 if abs(edge.score) >= 2.5 else 2.5 if abs(edge.score) >= 1.5 else 1.0)
            self.assertEqual(edge.two_way, (edge.target, edge.source) in pairs)
            self.assertIsNone(edge.label)
        self.assertEqual(data.stats.text, fixture["network_info"]["stats_text"])
        self.assertTrue(all(node.radius == 18 and node.fill in ("#2c4a6e", "#aaaaaa") for node in data.nodes))
        self.assertIn("Green bonds worth $5bn and $3bn", [node.label.split(":  ")[1] for node in data.nodes])
        self.assertIsNone(data.title)

    def test_ego_view(self):
        """Test the ego node, title and edge labels."""
        request = parity_fixtures.request("r6x4__average")
        data = network_chart_data_feature.chart_sync(request, NetworkLayout.FORCE_DIRECTED, 0)
        ego = data.nodes[0]
        self.assertEqual((ego.index, ego.is_focus, ego.radius, ego.fill), (0, True, 22, "#5a7fa8"))
        self.assertEqual(data.title, f"Ego Network:  P1  ({request.policies[0]})")
        self.assertTrue(all(edge.label == f"{edge.score:+.2f}" for edge in data.edges))
        self.assertIsNone(data.empty_message)

    def test_ego_without_connections(self):
        """Test L8: the empty message is returned and the ego is drawn alone at the centre."""
        request = parity_fixtures.request("onelink3x1__average")
        data = network_chart_data_feature.chart_sync(request, NetworkLayout.SPECTRAL, 2)
        self.assertEqual(data.empty_message, "P3 has no direct connections.")
        self.assertEqual([(n.x, n.y, n.radius, n.fill) for n in data.nodes], [(300.0, 300.0, 18, "#aaaaaa")])
        self.assertEqual(data.edges, [])

    def test_invalid_focus(self):
        """Test an out-of-range focus over HTTP."""
        body = parity_fixtures.parity_case("r5x3__average")["request"]
        response = TestClient(app).post("/api/v1/analysis/charts/network?layout=shell&focus=5", json=body)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "invalid_focus_policy")
        ok = TestClient(app).post("/api/v1/analysis/charts/network", json=body)
        self.assertEqual(ok.json()["data"]["layout"], "force_directed")
