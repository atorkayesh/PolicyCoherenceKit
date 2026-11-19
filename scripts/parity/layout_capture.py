"""
Capture legacy network layouts on the square 600 x 600 logical canvas (plan Phase 2.6, Settled Decision 14).

`NetworkTab` is built with `__new__`; `_result`, `_graph`, `_centrality` and a stub `_layout_var` are set and
`_compute_layout_positions` runs unchanged. Node and edge lists follow `_redraw_network` (`network_tab.py:903-907`)
and `_redraw_ego` (`network_tab.py:1052-1064`). While positions are computed, `numpy.linalg.eigh` is wrapped to
apply the L16 sign rule (each eigenvector column flipped so its largest-magnitude entry is positive, first such
index on ties) and to record the eigenvalues and the two chosen indices.
"""

from contextlib import contextmanager
from typing import Dict, Iterator, List, Optional

import network_tab
import numpy as np

CANVAS = (600, 600)
LAYOUTS = ["Circular", "Force-Directed", "Spectral", "Shell"]
LAYOUT_KEYS = {"Circular": "circular", "Force-Directed": "force_directed", "Spectral": "spectral", "Shell": "shell"}
DEGENERATE_GAP = 1e-9


class _LayoutVar:
    """Stub for the layout `StringVar`."""

    def __init__(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value


def flip_signs(vectors: np.ndarray) -> np.ndarray:
    """L16: flip each column so that its largest-magnitude entry (first on ties) is positive."""
    fixed = vectors.copy()
    for column in range(fixed.shape[1]):
        index = int(np.argmax(np.abs(fixed[:, column])))
        if fixed[index, column] < 0:
            fixed[:, column] = -fixed[:, column]
    return fixed


@contextmanager
def _signed_eigh(store: Dict) -> Iterator[None]:
    """Wrap `numpy.linalg.eigh` with the L16 sign rule and record the spectrum."""
    original = np.linalg.eigh

    def wrapper(matrix):
        values, vectors = original(matrix)
        order = np.argsort(values)
        nontrivial = [int(idx) for idx in order if values[idx] > 1e-9]
        store["eigenvalues"] = values.tolist()
        store["chosen"] = nontrivial[:2]
        compared = [values[idx] for idx in nontrivial[:3]]
        store["spectral_degenerate"] = any(
            abs(compared[k + 1] - compared[k]) < DEGENERATE_GAP for k in range(len(compared) - 1)
        )
        return values, flip_signs(vectors)

    np.linalg.eigh = wrapper
    try:
        yield
    finally:
        np.linalg.eigh = original


def _tab(result, layout: str):
    tab = network_tab.NetworkTab.__new__(network_tab.NetworkTab)
    tab._result = result
    tab._graph = network_tab._build_graph(result)
    tab._centrality = network_tab.compute_centrality(result)
    tab._layout_var = _LayoutVar(layout)
    return tab


def capture(result, layout: str, focus: Optional[int]) -> Dict:
    """Positions, node order and edges of one layout, for the full network (`focus=None`) or one ego view."""
    tab = _tab(result, layout)
    edges = tab._graph["edges"]
    if focus is None:
        node_ids = list(range(result.n))
        used_edges = edges
    else:
        used_edges = [(i, j, s) for (i, j, s) in edges if i == focus or j == focus]
        neighbours = sorted(
            {i for (i, _, _) in used_edges if i != focus} | {j for (_, j, _) in used_edges if j != focus}
        )
        node_ids = [focus] + neighbours
    spectrum: Dict = {}
    with _signed_eigh(spectrum):
        positions = tab._compute_layout_positions(node_ids, used_edges, *CANVAS)
    return {
        "layout": LAYOUT_KEYS[layout],
        "focus": focus,
        "canvas": list(CANVAS),
        "node_order": node_ids,
        "positions": {str(node): list(positions[node]) for node in node_ids},
        "edges": used_edges,
        "eigenvalues": spectrum.get("eigenvalues"),
        "chosen_eigen_indices": spectrum.get("chosen"),
        "spectral_degenerate": bool(spectrum.get("spectral_degenerate", False)),
    }


def all_layouts(result) -> List[Dict]:
    """Every layout for the full network and for focus 0."""
    return [capture(result, layout, focus) for layout in LAYOUTS for focus in (None, 0)]
