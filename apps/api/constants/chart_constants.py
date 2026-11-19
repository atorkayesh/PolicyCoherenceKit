"""
Chart data constants: network layouts, colours and text templates (`network_tab.py:56-64, 381-393, 1066-1090`)
and the PCA scatter (`pca_tab.py:40-44, 158, 192-196, 462-470`). Charts are drawn in the browser; the API
returns data only, so there are no dpi, canvas-border or PNG settings here.
"""

from enum import Enum
from typing import Dict, Tuple


class NetworkLayout(str, Enum):
    """Network layouts, in legacy order (`network_tab.py:64`)."""

    CIRCULAR = "circular"
    FORCE_DIRECTED = "force_directed"
    SPECTRAL = "spectral"
    SHELL = "shell"


NETWORK_LAYOUT_LABELS: Dict[NetworkLayout, str] = {
    NetworkLayout.CIRCULAR: "Circular",
    NetworkLayout.FORCE_DIRECTED: "Force-Directed",
    NetworkLayout.SPECTRAL: "Spectral",
    NetworkLayout.SHELL: "Shell",
}

DEFAULT_NETWORK_LAYOUT = NetworkLayout.FORCE_DIRECTED

# Square logical canvas the layouts are computed on (Settled Decision 14), and the legacy margin.
NETWORK_LAYOUT_CANVAS: Tuple[int, int] = (600, 600)
NETWORK_LAYOUT_MARGIN = 80

NETWORK_STYLE = {
    "NODE_RADIUS": 18,
    "FOCUS_RADIUS": 22,
    "POSITIVE_COLOUR": "#1a6e3c",
    "NEGATIVE_COLOUR": "#b71c1c",
    "ISOLATED_COLOUR": "#aaaaaa",
    "NODE_COLOUR": "#2c4a6e",
    "FOCUS_COLOUR": "#5a7fa8",
    "NODE_TEXT_COLOUR": "#ffffff",
}

NETWORK_TEXT = {
    "HOVER_LABEL": "{code}:  {policy}",
    "EGO_TITLE": "Ego Network:  {code}  ({policy})",
    "EGO_EMPTY": "{code} has no direct connections.",
    "EDGE_LABEL": "{score:+.2f}",
    "STATS": "{nodes} nodes  |  {edges} directed edges  |  density: {density}",
    "STATS_ISOLATED": "  |  {isolated} isolated",
}

PCA_STYLE = {"POINT_COLOUR": "#2c4a6e", "AXIS_COLOUR": "#cccccc"}

PCA_TEXT = {
    "X_AXIS": "PC1 ({pct}%)",
    "Y_AXIS": "PC2 ({pct}%)",
    "STATS": "PC1: {pc1}%   PC2: {pc2}%   Total explained: {total}%",
    "TOO_FEW_POLICIES": "PCA requires at least 3 policies.",
}

PCA_MIN_POLICIES = 3
