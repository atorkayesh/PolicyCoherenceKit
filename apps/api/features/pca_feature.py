"""
PCA of the outgoing influence profiles (`pca_tab.py:65-121`), ported verbatim, and the scatter data
(`pca_tab.py:185-196, 416-470`).

Known Tkinter Behaviour Kept 1 and 2: each row drops its own diagonal, so column `j` means a different target per
row; coordinates are `X_std @ Vt[:2].T` with no sign convention; standardisation uses the population std with a
zero std mapped to 1; an all-Neutral matrix gives all-zero coordinates with `valid = true`; n < 3 is invalid.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from constants.chart_constants import NETWORK_TEXT, PCA_MIN_POLICIES, PCA_TEXT
from models.aggregation_models import AggregationResult
from models.analysis_result_models import PcaBounds, PcaData, PcaPoint


class PcaFeature:
    """Computes the PCA coordinates and the scatter's bounds and texts."""

    def compute_pca(self, result: AggregationResult) -> Tuple[List[Tuple[float, float]], Tuple[float, float], bool]:
        """
        Run the PCA.

        Args:
            result: Aggregation result

        Returns:
            Tuple: (coordinates per policy, (PC1 %, PC2 %) rounded to 1 dp, valid)
        """
        n = result.n
        scores = result.scores
        if n < PCA_MIN_POLICIES:
            return [], (0.0, 0.0), False
        X = np.array(
            [[scores.get((i, j), 0.0) or 0.0 for j in range(n) if j != i] for i in range(n)],
            dtype=float,
        )
        means = X.mean(axis=0)
        stds = X.std(axis=0)
        stds[stds == 0] = 1.0
        X_std = (X - means) / stds
        U, S, Vt = np.linalg.svd(X_std, full_matrices=False)
        pct = self.percentages(S)
        if pct is None:
            explained = (0.0, 0.0)
        else:
            explained = (
                round(pct[0], 1) if len(pct) > 0 else 0.0,
                round(pct[1], 1) if len(pct) > 1 else 0.0,
            )
        coords_2d = (X_std @ Vt[:2].T).tolist()
        coords = [(row[0], row[1]) for row in coords_2d]
        return coords, explained, True

    def percentages(self, singular_values: np.ndarray) -> Optional[List[float]]:
        """
        Unrounded explained variance per component, `S**2 / sum(S**2) * 100` (`pca_tab.py:105-113`).

        Args:
            singular_values: Singular values of the standardised matrix

        Returns:
            Optional[List[float]]: Percentages, or None when the total variance is 0
        """
        var = singular_values**2
        total_var = var.sum()
        if total_var == 0:
            return None
        return (var / total_var * 100).tolist()

    def unrounded_explained(self, result: AggregationResult) -> Optional[List[float]]:
        """
        PC1 and PC2 percentages before `round(pct, 1)`; used by the rounding-boundary parity rule.

        Args:
            result: Aggregation result

        Returns:
            Optional[List[float]]: Two percentages, or None when invalid or without variance
        """
        n = result.n
        if n < PCA_MIN_POLICIES:
            return None
        X = np.array([[result.scores.get((i, j), 0.0) or 0.0 for j in range(n) if j != i] for i in range(n)])
        stds = X.std(axis=0)
        stds[stds == 0] = 1.0
        pct = self.percentages(np.linalg.svd((X - X.mean(axis=0)) / stds, full_matrices=False)[1])
        return pct[:2] if pct else None

    def data(self, result: AggregationResult, entropy_rows: List[Dict]) -> PcaData:
        """
        Build the scatter data.

        Args:
            result: Aggregation result
            entropy_rows: Entropy rows (for the category colouring)

        Returns:
            PcaData: Points, bounds, axis labels and the stats line, or the n < 3 message
        """
        coords, explained, valid = self.compute_pca(result)
        pc1, pc2 = explained
        total = round(pc1 + pc2, 1)
        if not valid:
            return PcaData(
                valid=False,
                explained=[pc1, pc2],
                total_explained=total,
                points=[],
                bounds=None,
                x_axis_label=None,
                y_axis_label=None,
                stats_text=None,
                message=PCA_TEXT["TOO_FEW_POLICIES"],
            )
        points = [
            PcaPoint(
                index=i,
                code=result.codes[i],
                policy=result.policies[i],
                label=NETWORK_TEXT["HOVER_LABEL"].format(code=result.codes[i], policy=result.policies[i]),
                x=x,
                y=y,
                entropy_category=entropy_rows[i]["category"],
            )
            for i, (x, y) in enumerate(coords)
        ]
        return PcaData(
            valid=True,
            explained=[pc1, pc2],
            total_explained=total,
            points=points,
            bounds=self._bounds(coords),
            x_axis_label=PCA_TEXT["X_AXIS"].format(pct=pc1),
            y_axis_label=PCA_TEXT["Y_AXIS"].format(pct=pc2),
            stats_text=PCA_TEXT["STATS"].format(pc1=pc1, pc2=pc2, total=total),
            message=None,
        )

    def _bounds(self, coords: List[Tuple[float, float]]) -> PcaBounds:
        """`_redraw` scale (`pca_tab.py:436-442`): min/max, with a zero range drawn as `min + 1.0`."""
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        return PcaBounds(
            x_min=x_min,
            x_max=x_max if x_max - x_min else x_min + 1.0,
            y_min=y_min,
            y_max=y_max if y_max - y_min else y_min + 1.0,
        )


pca_feature = PcaFeature()
