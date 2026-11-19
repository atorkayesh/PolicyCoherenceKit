"""
Range of influence: Shannon entropy of outgoing influence (`range_of_influence_tab.py:82-141`), verbatim.

Known Tkinter Behaviour Kept 5 and 12: Hmax is 1.0 for 2 policies; the category divides the rounded H by the
unrounded Hmax; `Low` means both "no outgoing influence" and "concentrated"; one non-zero link gives `-0.0`.
"""

import math
from typing import Dict, List

from constants.entropy_constants import ENTROPY_CATEGORIES, ENTROPY_RATIO_CUTOFFS
from models.aggregation_models import AggregationResult
from models.analysis_result_models import EntropyRow, RangeOfInfluenceData


class EntropyFeature:
    """Computes entropy rows and categories."""

    def compute_entropy(self, result: AggregationResult) -> List[Dict]:
        """
        Compute the entropy of every policy.

        Args:
            result: Aggregation result

        Returns:
            List[Dict]: `{code, policy, entropy, category, hmax}` in index order
        """
        n = result.n
        scores = result.scores
        hmax = math.log2(n - 1) if n > 2 else (1.0 if n == 2 else 0.0)
        rows = []
        for i in range(n):
            abs_vals = [
                abs(scores.get((i, j), 0.0) or 0.0)
                for j in range(n)
                if j != i and (scores.get((i, j), 0.0) or 0.0) != 0.0
            ]
            if not abs_vals or sum(abs_vals) == 0.0:
                entropy = 0.0
                category = ENTROPY_CATEGORIES[0]["label"]
            else:
                total = sum(abs_vals)
                probs = [v / total for v in abs_vals]
                entropy = -sum(p * math.log2(p) for p in probs if p > 0)
                entropy = round(entropy, 4)
                category = self.categorise(entropy, hmax)
            rows.append(
                {
                    "code": result.codes[i],
                    "policy": result.policies[i],
                    "entropy": entropy,
                    "category": category,
                    "hmax": round(hmax, 4),
                }
            )
        return rows

    def categorise(self, h: float, hmax: float) -> str:
        """
        Map an entropy to its category by the share of Hmax.

        Args:
            h: Rounded entropy
            hmax: Unrounded maximum entropy

        Returns:
            str: `Low`, `Low-to-Medium`, `Medium-to-High` or `High`
        """
        labels = [category["label"] for category in ENTROPY_CATEGORIES]
        if hmax == 0.0:
            return labels[0]
        ratio = h / hmax
        for label, cutoff in zip(labels, ENTROPY_RATIO_CUTOFFS, strict=False):
            if ratio < cutoff:
                return label
        return labels[-1]

    def data(self, rows: List[Dict]) -> RangeOfInfluenceData:
        """
        Package the rows.

        Args:
            rows: Output of `compute_entropy`

        Returns:
            RangeOfInfluenceData: Hmax (as the rows carry it) and the rows
        """
        return RangeOfInfluenceData(
            hmax=rows[0]["hmax"] if rows else 0.0,
            rows=[EntropyRow(**{key: row[key] for key in ("code", "policy", "entropy", "category")}) for row in rows],
        )


entropy_feature = EntropyFeature()
