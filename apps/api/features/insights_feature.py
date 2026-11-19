"""
Results Insights numbers, ported verbatim from `results_insights_tab.py:294-455, 503-509, 562-590, 607-664`.

Only what the tab displays is returned; the dead legacy fields (`narrative`, quadrants, `top_broker`,
`top_prominent`, the driver/dependent/balanced lists, `strong_consensus`, `top_*_rows`) are not computed. Known
Tkinter Behaviour Kept 6, 9 and 10: the top driver/dependent are `max` by `(woi, prominence, net)` and
`(wii, prominence, -net)` (first on ties, may be negative); stable sorts keep index order; zero variance gives a
correlation of 1.0.
"""

import math
from collections import Counter
from typing import Dict, List, Tuple

from constants.insights_constants import INSIGHTS_ARROWS, INSIGHTS_THRESHOLDS
from models.aggregation_models import AggregationResult


class InsightsFeature:
    """Computes the Results Insights statistics."""

    def compute(
        self, result: AggregationResult, scores: List[Dict], entropy: List[Dict], centrality: List[Dict]
    ) -> Dict:
        """
        `compute_insights` (displayed parts) plus system health.

        Args:
            result: Aggregation result
            scores: `compute_scores` rows
            entropy: `compute_entropy` rows
            centrality: `compute_centrality` rows

        Returns:
            Dict: `rows`, `graph`, `agreement`, `top_driver`, `top_dependent`, `health`
        """
        entropy_by_code = {row["code"]: row for row in entropy}
        centrality_by_code = {row["code"]: row for row in centrality}
        enriched = []
        for idx, row in enumerate(scores):
            net = round(row["woi"] - row["wii"], 2)
            prominence = round(
                sum(abs(result.scores.get((idx, j), 0.0) or 0.0) for j in range(result.n) if j != idx)
                + sum(abs(result.scores.get((j, idx), 0.0) or 0.0) for j in range(result.n) if j != idx),
                2,
            )
            enriched.append(
                {
                    **row,
                    "index": idx,
                    "net": net,
                    "prominence": prominence,
                    "entropy": entropy_by_code[row["code"]]["entropy"],
                    "entropy_category": entropy_by_code[row["code"]]["category"],
                    "betweenness": centrality_by_code[row["code"]]["betweenness"],
                    "closeness": centrality_by_code[row["code"]]["closeness"],
                    "role": self.role(net),
                }
            )
        return {
            "rows": enriched,
            "graph": self.graph_stats(result),
            "agreement": self.agreement_stats(result),
            "top_driver": max(enriched, key=lambda r: (r["woi"], r["prominence"], r["net"]), default=None),
            "top_dependent": max(enriched, key=lambda r: (r["wii"], r["prominence"], -r["net"]), default=None),
            "health": self.system_health(result),
        }

    def role(self, net: float) -> str:
        """`_role_for_row`: driver above +0.05, dependent below -0.05, else balanced."""
        if net > INSIGHTS_THRESHOLDS["NET_CUTOFF"]:
            return "driver"
        if net < -INSIGHTS_THRESHOLDS["NET_CUTOFF"]:
            return "dependent"
        return "balanced"

    def policy_label(self, code: str, policy: str) -> str:
        """`_policy_label`: `{policy} ({code})`."""
        return f"{policy} ({code})"

    def pair_label(self, result: AggregationResult, i: int, j: int, arrow: str = INSIGHTS_ARROWS["DIRECTED"]) -> str:
        """`_pair_label` with the single arrow `→` (L11)."""
        first = self.policy_label(result.codes[i], result.policies[i])
        return f"{first} {arrow} {self.policy_label(result.codes[j], result.policies[j])}"

    def graph_stats(self, result: AggregationResult) -> Dict:
        """`_build_graph_stats`: counts, density, polarity and the strongest links (first in row-major on ties)."""
        n = result.n
        pos = neg = zero = 0
        strongest_pos = strongest_neg = strongest_pos_pair = strongest_neg_pair = None
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                score = result.scores.get((i, j), 0.0) or 0.0
                if score > 0:
                    pos += 1
                    if strongest_pos is None or score > strongest_pos:
                        strongest_pos, strongest_pos_pair = score, (i, j)
                elif score < 0:
                    neg += 1
                    if strongest_neg is None or score < strongest_neg:
                        strongest_neg, strongest_neg_pair = score, (i, j)
                else:
                    zero += 1
        max_edges = n * (n - 1) if n > 1 else 1
        return {
            "positive_edges": pos,
            "negative_edges": neg,
            "zero_edges": zero,
            "density": round((pos + neg) / max_edges, 3),
            "polarity": round(pos / (pos + neg), 3) if (pos + neg) else 0.5,
            "strongest_pos": strongest_pos if strongest_pos is not None else 0.0,
            "strongest_neg": strongest_neg if strongest_neg is not None else 0.0,
            "strongest_pos_pair": strongest_pos_pair,
            "strongest_neg_pair": strongest_neg_pair,
        }

    def rank_values(self, values: List[float]) -> List[float]:
        """`_rank_values`: 1-based ranks, ties get the average rank."""
        indexed = sorted(enumerate(values), key=lambda item: item[1])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(indexed):
            j = i + 1
            while j < len(indexed) and indexed[j][1] == indexed[i][1]:
                j += 1
            avg_rank = (i + 1 + j) / 2.0
            for k in range(i, j):
                ranks[indexed[k][0]] = avg_rank
            i = j
        return ranks

    def pearson_corr(self, xs: List[float], ys: List[float]) -> float:
        """`_pearson_corr`: 1.0 when either vector has zero variance; clamped to [-1, 1]."""
        n = len(xs)
        if n == 0 or n != len(ys):
            return 0.0
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
        den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
        den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
        if den_x == 0 or den_y == 0:
            return 1.0
        return max(-1.0, min(1.0, num / (den_x * den_y)))

    def spearman_agreement(self, result: AggregationResult) -> Tuple[float, float]:
        """`_average_dm_spearman_agreement`: (average correlation, (avg + 1) / 2), both rounded to 3 dp."""
        dm_count = max(result.decision_makers, len(result.decision_maker_names))
        if dm_count <= 1:
            return 1.0, 1.0
        dm_vectors: List[List[float]] = [[] for _ in range(dm_count)]
        for i in range(result.n):
            for j in range(result.n):
                if i == j:
                    continue
                values = [float(v) for v in result.source_scores.get((i, j), [])]
                if len(values) != dm_count:
                    continue
                for dm_idx, value in enumerate(values):
                    dm_vectors[dm_idx].append(value)
        if not dm_vectors or not dm_vectors[0]:
            return 1.0, 1.0
        ranked = [self.rank_values(vector) for vector in dm_vectors]
        pairwise = [self.pearson_corr(ranked[i], ranked[j]) for i in range(dm_count) for j in range(i + 1, dm_count)]
        if not pairwise:
            return 1.0, 1.0
        avg_corr = sum(pairwise) / len(pairwise)
        return round(avg_corr, 3), round((avg_corr + 1.0) / 2.0, 3)

    def agreement_stats(self, result: AggregationResult) -> Dict:
        """`_agreement_stats`: the five most contested relations (stable sort) and the rank agreement."""
        rows = []
        dm_count = max(1, result.decision_makers or len(result.decision_maker_names) or 1)
        for i in range(result.n):
            for j in range(result.n):
                if i == j:
                    continue
                values = [float(v) for v in result.source_scores.get((i, j), [])]
                if not values:
                    continue
                counts = Counter(values)
                rows.append(
                    {
                        "i": i,
                        "j": j,
                        "pair": self.pair_label(result, i, j),
                        "score": result.scores.get((i, j), 0.0) or 0.0,
                        "agreement_ratio": round(max(counts.values()) / dm_count, 3),
                        "spread": round(max(values) - min(values), 2),
                    }
                )
        contested = sorted(rows, key=lambda row: (row["agreement_ratio"], -row["spread"], -abs(row["score"])))
        average_corr, average_agreement = self.spearman_agreement(result)
        return {
            "contested": contested[: INSIGHTS_THRESHOLDS["CONTESTED_SHOWN"]],
            "average_agreement": average_agreement,
            "average_correlation": average_corr,
        }

    def system_health(self, result: AggregationResult) -> Dict[str, int]:
        """`_build_system_health`: synergy, conflict and neutral shares (int `round`, half-to-even) and the score."""
        max_edges = max(1, result.n * (result.n - 1))
        max_strength = max_edges * INSIGHTS_THRESHOLDS["MAX_SCORE"]
        positive_strength = negative_strength = 0.0
        neutral_count = 0
        for i in range(result.n):
            for j in range(result.n):
                if i == j:
                    continue
                score = result.scores.get((i, j), 0.0) or 0.0
                if score > 0:
                    positive_strength += score
                elif score < 0:
                    negative_strength += abs(score)
                else:
                    neutral_count += 1
        synergy = round((positive_strength / max_strength) * 100)
        conflict = round((negative_strength / max_strength) * 100)
        neutral_uncertain = round((neutral_count / max_edges) * 100)
        base = INSIGHTS_THRESHOLDS["HEALTH_BASE"]
        penalty = round(neutral_uncertain * INSIGHTS_THRESHOLDS["HEALTH_NEUTRAL_PENALTY"])
        score = max(0, min(100, base + synergy - conflict - penalty))
        return {"score": score, "synergy": synergy, "conflict": conflict, "neutral_uncertain": neutral_uncertain}


insights_feature = InsightsFeature()
