"""
The AI interpretation prompt, verbatim from `llm_tab.py:86-196` (`SECTION_HEADERS`, `build_prompt`).

The prompt is out of scope for label fixes: it is compared exactly with the legacy output for every fixture. It
never includes PCA or insights.
"""

from typing import Dict, List

from models.aggregation_models import AggregationResult
from utils.aggregation_label_utils import aggregation_labeler

SECTION_HEADERS = [
    "1. Overall Coherence Assessment",
    "2. Key Synergies",
    "3. Key Conflicts",
    "4. Influential Policies",
    "5. Range of Influence",
    "6. Network Structure",
    "7. Strategic Recommendations",
]


class ExplanationPromptFeature:
    """Builds the user prompt from an aggregation result and its legacy analysis rows."""

    def build_prompt(
        self, result: AggregationResult, scores: List[Dict], entropy: List[Dict], centrality: List[Dict]
    ) -> str:
        """
        Build the prompt.

        Args:
            result: Aggregation result (every tie resolved)
            scores: `compute_scores` rows
            entropy: `compute_entropy` rows
            centrality: `compute_centrality` rows (index order; sorted here by betweenness, descending)

        Returns:
            str: The legacy prompt text
        """
        n = result.n
        codes = result.codes
        lines = []
        lines.append(
            f"You are given the results of a policy coherence analysis for "
            f"{n} policies, aggregated using the {aggregation_labeler.method_label(result)} method.\n"
        )
        lines.append("POLICY LIST:")
        for code, name in zip(codes, result.policies, strict=False):
            lines.append(f"  {code}: {name}")
        lines.append("")
        lines.append(
            "AGGREGATED SCORE MATRIX "
            "(rows = influencing policy, columns = influenced policy, "
            "scale: -3=Cancelling to +3=Indivisible, 0=diagonal):"
        )
        lines.append("         " + "  ".join(f"{c:>6}" for c in codes))
        for i in range(n):
            row_vals = [f"{(result.scores.get((i, j), 0.0) or 0.0):>6.2f}" for j in range(n)]
            lines.append(f"  {codes[i]:>5}  " + "  ".join(row_vals))
        lines.append("")
        lines.append(
            "COHERENCE SCORES "
            "(OI=Outgoing Influence count, II=Incoming Influence count, "
            "WOI=Weighted Outgoing, WII=Weighted Incoming):"
        )
        lines.append(f"  {'Code':<6} {'OI':>4} {'II':>4} {'WOI':>7} {'WII':>7}  Policy")
        for row in scores:
            lines.append(
                f"  {row['code']:<6} {row['oi']:>4} {row['ii']:>4} "
                f"{row['woi']:>7.2f} {row['wii']:>7.2f}  {row['policy']}"
            )
        lines.append("")
        lines.append(
            "RANGE OF INFLUENCE — SHANNON ENTROPY "
            "(0=concentrated on one policy, higher=distributed; "
            "categories based on fraction of max entropy):"
        )
        lines.append(f"  {'Code':<6} {'Entropy':>8}  {'Category':<14}  Policy")
        for row in entropy:
            lines.append(f"  {row['code']:<6} {row['entropy']:>8.4f}  {row['category']:<14}  {row['policy']}")
        lines.append("")
        lines.append("NETWORK CENTRALITY (Betweenness: broker role 0-1; Closeness: reachability, higher=more central):")
        lines.append(f"  {'Code':<6} {'Betweenness':>12} {'Closeness':>10}  Policy")
        for row in sorted(centrality, key=lambda r: r["betweenness"], reverse=True):
            lines.append(f"  {row['code']:<6} {row['betweenness']:>12.4f} {row['closeness']:>10.4f}  {row['policy']}")
        lines.append("")
        lines.append(
            "Provide a structured, in-depth interpretation with the "
            "following sections. Each section should be multiple paragraphs "
            "with specific references to the data above:\n"
        )
        for header in SECTION_HEADERS:
            lines.append(f"## {header}")
        lines.append(
            "\nEnsure your interpretation is analytical, references specific "
            "policies by name and code, and provides actionable insights for "
            "policy professionals."
        )
        return "\n".join(lines)


explanation_prompt_feature = ExplanationPromptFeature()
