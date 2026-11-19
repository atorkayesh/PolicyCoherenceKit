"""
Network layouts, ported verbatim from `network_tab.py:92-124, 690-886` as functions of
`(node_ids, edges, width, height, centrality, codes)`; callers pass the square 600 x 600 `NETWORK_LAYOUT_CANVAS`.

The only change is label fix L16: after `np.linalg.eigh`, each eigenvector column is flipped so that its
largest-magnitude entry is positive (first such index on ties), so spectral pictures do not mirror between
platforms. `_normalize_positions` keeps its per-axis stretch (parity). No randomness anywhere.
"""

import math
from typing import Dict, List, Tuple

import numpy as np

from constants.chart_constants import NETWORK_LAYOUT_MARGIN, NetworkLayout

Edge = Tuple[int, int, float]
Positions = Dict[int, Tuple[float, float]]
_MARGIN = NETWORK_LAYOUT_MARGIN


class NetworkLayouter:
    """Computes node positions on a logical canvas (y grows downwards)."""

    def positions(
        self, layout: NetworkLayout, node_ids: List[int], edges: List[Edge], size: Tuple[int, int], centrality, codes
    ) -> Positions:
        """
        `_compute_layout_positions`.

        Args:
            layout: Layout key
            node_ids: Nodes in legacy order
            edges: `(i, j, score)` edges among the nodes
            size: Canvas `(width, height)`
            centrality: Full-network centrality rows (shell layout)
            codes: Policy codes (shell layout tie order)

        Returns:
            Positions: node -> (x, y)
        """
        width, height = size
        nodes = list(node_ids)
        if layout == NetworkLayout.FORCE_DIRECTED:
            return self.force_directed(nodes, edges, width, height)
        if layout == NetworkLayout.SPECTRAL:
            return self.spectral(nodes, edges, width, height)
        if layout == NetworkLayout.SHELL:
            return self.shell(nodes, width, height, centrality, codes)
        return self.circular(nodes, width, height)

    def normalize(self, raw: Positions, width: int, height: int, margin: int) -> Positions:
        """`_normalize_positions`: stretch each axis to the canvas minus the margin."""
        if not raw:
            return {}
        xs = [pt[0] for pt in raw.values()]
        ys = [pt[1] for pt in raw.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if math.isclose(min_x, max_x):
            min_x -= 1.0
            max_x += 1.0
        if math.isclose(min_y, max_y):
            min_y -= 1.0
            max_y += 1.0
        span_x = max_x - min_x
        span_y = max_y - min_y
        usable_w = max(1.0, width - 2 * margin)
        usable_h = max(1.0, height - 2 * margin)
        return {
            node: (margin + ((x - min_x) / span_x) * usable_w, margin + ((y - min_y) / span_y) * usable_h)
            for node, (x, y) in raw.items()
        }

    def circular(self, node_ids: List[int], width: int, height: int) -> Positions:
        """`_circular_layout_positions`: from -π/2, radius `max(40, min(w, h) / 2 - 80)`."""
        if not node_ids:
            return {}
        cx, cy = width / 2, height / 2
        if len(node_ids) == 1:
            return {node_ids[0]: (cx, cy)}
        radius = max(40, min(width, height) / 2 - _MARGIN)
        count = len(node_ids)
        positions = {}
        for idx, node in enumerate(node_ids):
            angle = 2 * math.pi * idx / count - math.pi / 2
            positions[node] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        return positions

    def undirected_strengths(self, node_ids: List[int], edges: List[Edge]):
        """`_undirected_strengths`: summed |score| per unordered pair, and the adjacency."""
        node_set = set(node_ids)
        pair_strengths: Dict[Tuple[int, int], float] = {}
        adjacency: Dict[int, List[Tuple[int, float]]] = {node: [] for node in node_ids}
        for i, j, score in edges:
            if i not in node_set or j not in node_set or i == j:
                continue
            key = (min(i, j), max(i, j))
            pair_strengths[key] = pair_strengths.get(key, 0.0) + abs(score)
        for (i, j), strength in pair_strengths.items():
            adjacency[i].append((j, strength))
            adjacency[j].append((i, strength))
        return pair_strengths, adjacency

    def force_directed(self, node_ids: List[int], edges: List[Edge], width: int, height: int) -> Positions:
        """`_force_directed_layout_positions`: 90 iterations from the circular layout."""
        count = len(node_ids)
        if count <= 1:
            return self.circular(node_ids, width, height)
        circular = self.circular(node_ids, width, height)
        cx, cy = width / 2, height / 2
        raw = {
            node: ((pos[0] - cx) / max(1.0, width / 2 - _MARGIN), (pos[1] - cy) / max(1.0, height / 2 - _MARGIN))
            for node, pos in circular.items()
        }
        pair_strengths, _ = self.undirected_strengths(node_ids, edges)
        k = math.sqrt(4.0 / count)
        iterations = 90
        for step in range(iterations):
            disp = {node: [0.0, 0.0] for node in node_ids}
            for idx, node_a in enumerate(node_ids):
                x1, y1 = raw[node_a]
                for node_b in node_ids[idx + 1 :]:
                    x2, y2 = raw[node_b]
                    dx = x1 - x2
                    dy = y1 - y2
                    dist = math.hypot(dx, dy) or 0.001
                    force = (k * k) / dist
                    rx = dx / dist * force
                    ry = dy / dist * force
                    disp[node_a][0] += rx
                    disp[node_a][1] += ry
                    disp[node_b][0] -= rx
                    disp[node_b][1] -= ry
            for (a, b), strength in pair_strengths.items():
                x1, y1 = raw[a]
                x2, y2 = raw[b]
                dx = x2 - x1
                dy = y2 - y1
                dist = math.hypot(dx, dy) or 0.001
                force = (dist * dist / k) * (0.55 + min(strength, 6.0) / 6.0)
                ax = dx / dist * force
                ay = dy / dist * force
                disp[a][0] += ax
                disp[a][1] += ay
                disp[b][0] -= ax
                disp[b][1] -= ay
            temperature = 0.12 * (1 - step / iterations) + 0.01
            for node in node_ids:
                dx, dy = disp[node]
                length = math.hypot(dx, dy)
                if length > 0:
                    scale = min(temperature, length) / length
                    dx *= scale
                    dy *= scale
                raw[node] = (max(-1.2, min(1.2, raw[node][0] + dx)), max(-1.2, min(1.2, raw[node][1] + dy)))
        return self.normalize(raw, width, height, _MARGIN)

    def spectral(self, node_ids: List[int], edges: List[Edge], width: int, height: int) -> Positions:
        """`_spectral_layout_positions` with the L16 eigenvector sign rule."""
        if len(node_ids) <= 2:
            return self.circular(node_ids, width, height)
        pair_strengths, adjacency = self.undirected_strengths(node_ids, edges)
        if not pair_strengths:
            return self.circular(node_ids, width, height)
        index = {node: idx for idx, node in enumerate(node_ids)}
        size = len(node_ids)
        adj = np.zeros((size, size), dtype=float)
        for (a, b), strength in pair_strengths.items():
            adj[index[a], index[b]] = strength
            adj[index[b], index[a]] = strength
        lap = np.diag(adj.sum(axis=1)) - adj
        eigvals, eigvecs = np.linalg.eigh(lap)
        eigvecs = self.flip_signs(eigvecs)
        order = np.argsort(eigvals)
        nontrivial = [idx for idx in order if eigvals[idx] > 1e-9]
        if not nontrivial:
            return self.circular(node_ids, width, height)
        x_vec = eigvecs[:, nontrivial[0]]
        y_vec = eigvecs[:, nontrivial[1]] if len(nontrivial) > 1 else np.zeros(size)
        raw = {}
        for node in node_ids:
            idx = index[node]
            degree_bias = len(adjacency[node]) * 0.02
            raw[node] = (float(x_vec[idx]), float(y_vec[idx] + degree_bias))
        return self.normalize(raw, width, height, _MARGIN)

    def flip_signs(self, vectors: np.ndarray) -> np.ndarray:
        """L16: flip each column so that its largest-magnitude entry (first on ties) is positive."""
        fixed = vectors.copy()
        for column in range(fixed.shape[1]):
            index = int(np.argmax(np.abs(fixed[:, column])))
            if fixed[index, column] < 0:
                fixed[:, column] = -fixed[:, column]
        return fixed

    def shell(self, node_ids: List[int], width: int, height: int, centrality, codes: List[str]) -> Positions:
        """`_shell_layout_positions`: rings of 20 %, 30 % and the rest by betweenness (code breaks ties, reversed)."""
        if not node_ids:
            return {}
        by_code = {row["code"]: row["betweenness"] for row in centrality}
        ranked = sorted(node_ids, key=lambda idx: (by_code.get(codes[idx], 0.0), codes[idx]), reverse=True)
        count = len(ranked)
        if count <= 3:
            shells = [ranked]
        else:
            inner_n = max(1, round(count * 0.2))
            middle_n = max(1, round(count * 0.3))
            outer_start = min(count, inner_n + middle_n)
            shells = [s for s in (ranked[:inner_n], ranked[inner_n:outer_start], ranked[outer_start:]) if s]
        cx, cy = width / 2, height / 2
        max_radius = max(40, min(width, height) / 2 - _MARGIN)
        shell_radii = [0.28, 0.58, 0.88]
        positions: Positions = {}
        for shell_idx, shell_nodes in enumerate(shells):
            radius = max_radius * shell_radii[min(shell_idx, len(shell_radii) - 1)]
            if len(shell_nodes) == 1:
                positions[shell_nodes[0]] = (cx, cy) if shell_idx == 0 else (cx, cy - radius)
                continue
            angle_offset = shell_idx * (math.pi / max(3, len(shell_nodes) * 2))
            for idx, node in enumerate(shell_nodes):
                angle = 2 * math.pi * idx / len(shell_nodes) - math.pi / 2 + angle_offset
                positions[node] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        return positions


network_layouter = NetworkLayouter()
