"""
Coherence scores (`coherence_scores_tab.py:107-142`) and their colour bands (`coherence_scores_tab.py:73-100`),
ported verbatim. Unresolved ties read as 0 (`scores.get(..., 0.0) or 0.0`); the API rejects them first.
"""

from typing import Dict, List

from constants.band_constants import COUNT_BANDS, VALUE_BANDS, VALUE_THRESHOLDS
from models.aggregation_models import AggregationResult
from models.analysis_result_models import CoherenceScoreRow


class CoherenceScoresFeature:
    """Computes OI, II, WOI and WII."""

    def compute_scores(self, result: AggregationResult) -> List[Dict]:
        """
        Compute the scores of every policy, in index order.

        Args:
            result: Aggregation result

        Returns:
            List[Dict]: `{code, policy, oi, ii, woi, wii}`; WOI and WII rounded to 2 dp
        """
        n = result.n
        scores = result.scores
        rows = []
        for i in range(n):
            oi = sum(1 for j in range(n) if j != i and scores.get((i, j), 0.0) not in (None, 0.0))
            ii = sum(1 for j in range(n) if j != i and scores.get((j, i), 0.0) not in (None, 0.0))
            woi = sum(scores.get((i, j), 0.0) or 0.0 for j in range(n) if j != i)
            wii = sum(scores.get((j, i), 0.0) or 0.0 for j in range(n) if j != i)
            rows.append(
                {
                    "code": result.codes[i],
                    "policy": result.policies[i],
                    "oi": oi,
                    "ii": ii,
                    "woi": round(woi, 2),
                    "wii": round(wii, 2),
                }
            )
        return rows

    def value_band(self, value: float) -> str:
        """
        Band key of a WOI or WII value (`_value_color`).

        Args:
            value: Score

        Returns:
            str: `strong_positive` ... `strong_negative`
        """
        keys = [band["key"] for band in VALUE_BANDS]
        if value > VALUE_THRESHOLDS["STRONG"]:
            return keys[0]
        if value > VALUE_THRESHOLDS["MODERATE"]:
            return keys[1]
        if value > VALUE_THRESHOLDS["ZERO"]:
            return keys[2]
        if value == VALUE_THRESHOLDS["ZERO"]:
            return keys[3]
        if value >= -VALUE_THRESHOLDS["MODERATE"]:
            return keys[4]
        if value >= -VALUE_THRESHOLDS["STRONG"]:
            return keys[5]
        return keys[6]

    def count_band(self, value: int, n: int) -> str:
        """
        Band key of an OI or II count (`_count_color`): share of the other `n - 1` policies.

        Args:
            value: Count
            n: Number of policies

        Returns:
            str: `very_high`, `high`, `medium`, `low`, or `none` when n <= 1
        """
        if n <= 1:
            return COUNT_BANDS[-1]["key"]
        ratio = value / (n - 1)
        for band in COUNT_BANDS[:3]:
            if ratio >= band["min_ratio"]:
                return band["key"]
        return COUNT_BANDS[3]["key"]

    def rows(self, score_rows: List[Dict], n: int) -> List[CoherenceScoreRow]:
        """
        Add the band keys to the score rows.

        Args:
            score_rows: Output of `compute_scores`
            n: Number of policies

        Returns:
            List[CoherenceScoreRow]: Rows in index order
        """
        return [
            CoherenceScoreRow(
                **row,
                oi_band=self.count_band(row["oi"], n),
                ii_band=self.count_band(row["ii"], n),
                woi_band=self.value_band(row["woi"]),
                wii_band=self.value_band(row["wii"]),
            )
            for row in score_rows
        ]


coherence_scores_feature = CoherenceScoresFeature()
