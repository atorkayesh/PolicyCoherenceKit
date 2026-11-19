"""
Results Insights texts, ported from `results_insights_tab.py:294-310, 512-604, 815-835, 879, 953-1084`.

Label fixes applied: L11 (one arrow `→`; the Most Contested card keeps `↔`), L12 (`Rating agreement: `), and L13
(sign wording: `positive link` / `negative link`). Known Tkinter Behaviour Kept 3, 4 and 17: the Strongest Link card
and tag use the strongest positive pair only; Most Contested always names a pair; the story tone follows the sign.
"""

from typing import Dict, Optional, Tuple

from constants.insights_constants import INSIGHTS_ARROWS, INSIGHTS_TEXT, INSIGHTS_THRESHOLDS, INTERPRETATIONS
from features.insights_feature import InsightsFeature, insights_feature
from models.aggregation_models import AggregationResult
from models.insights_models import (
    ConflictRatioText,
    InsightsTexts,
    MostContestedText,
    PolicyCardText,
    StrongestLinkText,
)


class InsightsTextFeature:
    """Builds the story, the interpretation, the banner tags and the card texts."""

    def __init__(self, insights: Optional[InsightsFeature] = None):
        """
        Create the feature.

        Args:
            insights: Label helpers; defaults to the shared instance
        """
        self._insights = insights or insights_feature

    def texts(self, result: AggregationResult, insights: Dict) -> InsightsTexts:
        """
        Build every displayed text.

        Args:
            result: Aggregation result
            insights: Output of `InsightsFeature.compute`

        Returns:
            InsightsTexts: Story, interpretation, tags and cards
        """
        contested = insights["agreement"]["contested"]
        driver = insights["top_driver"]
        graph = insights["graph"]
        prefix = INSIGHTS_TEXT["INTERPRETATION_LABEL"]
        interpretation = self.supporting_interpretation(insights)
        return InsightsTexts(
            story=self.story(result, insights),
            interpretation_label=prefix,
            interpretation_text=interpretation[len(prefix) :].lstrip(),
            overview_agreement_text=f"{insights['agreement']['average_agreement']:.2f}",
            tag_top_driver=INSIGHTS_TEXT["TAG_TOP_DRIVER"].format(value=self.policy_from_row(driver)),
            tag_strongest_link=INSIGHTS_TEXT["TAG_STRONGEST_LINK"].format(
                value=self.format_pair(result, graph["strongest_pos_pair"])
            ),
            tag_contested=INSIGHTS_TEXT["TAG_CONTESTED"].format(
                value=contested[0]["pair"] if contested else INSIGHTS_TEXT["NO_CONTESTED_TAG"]
            ),
            top_driver=self._policy_card(driver, "woi", "WOI"),
            top_dependent=self._policy_card(insights["top_dependent"], "wii", "WII"),
            strongest_link=self._strongest_link_card(result, graph),
            most_contested=self._most_contested_card(result, contested[0] if contested else None),
            conflict_ratio=self._conflict_ratio_card(graph),
        )

    def policy_from_row(self, row: Optional[Dict]) -> str:
        """`_policy_label_from_row`: `{policy} ({code})` or `N/A`."""
        if not row:
            return INSIGHTS_TEXT["NOT_AVAILABLE"]
        return self._insights.policy_label(row["code"], row["policy"])

    def format_pair(self, result: AggregationResult, pair) -> str:
        """`_format_pair`: the pair label, or `No non-zero relation`."""
        if not pair:
            return INSIGHTS_TEXT["NO_RELATION"]
        i, j = pair
        return self._insights.pair_label(result, i, j)

    def strongest_link(self, result: AggregationResult, row_index: int) -> Tuple[str, float]:
        """`_strongest_link`: the largest |score| in the row (strict `>`, so the lower index wins ties); L13 suffix."""
        best_pair = None
        best_score = 0.0
        for j in range(result.n):
            if j == row_index:
                continue
            score = result.scores.get((row_index, j), 0.0) or 0.0
            if abs(score) > abs(best_score):
                best_score = score
                best_pair = (row_index, j)
        if best_pair is None:
            return INSIGHTS_TEXT["NO_STRONG_OUTGOING_LINK"], 0.0
        _, j = best_pair
        tone = "positive" if best_score > 0 else "negative"
        return f"{self._insights.pair_label(result, row_index, j)} ({best_score:+.2f}, {tone})", best_score

    def story(self, result: AggregationResult, insights: Dict) -> str:
        """`_build_story_banner` with the L11 arrow and the L13 sign wording."""
        top_driver = insights["top_driver"]
        contested = insights["agreement"]["contested"][0] if insights["agreement"]["contested"] else None
        if not top_driver:
            return "The current result set is too sparse to describe a clear system story."
        link_text, score = self.strongest_link(result, top_driver["index"])
        average_agreement = insights["agreement"]["average_agreement"]
        stable_phrase = (
            "stable" if average_agreement >= INSIGHTS_THRESHOLDS["STABLE_AGREEMENT"] else "not yet fully stable"
        )
        driver = self.policy_from_row(top_driver)
        sign = "positive" if score > 0 else "negative"
        if contested:
            return (
                f"{driver} emerges as the top driving policy in the system, with the highest weighted outgoing "
                f"coherence score of {top_driver['woi']:+.2f} and its strongest influence "
                f"through the {sign} link {link_text}, which indicates a "
                f"{stable_phrase} and structurally significant interaction. In contrast, the linkage "
                f"{contested['pair']} remains contested across decision-makers, reflecting a lack of consensus and "
                f"highlighting an area of uncertainty within the system."
            )
        if abs(score) > 0:
            return (
                f"{driver} emerges as the top driving policy in the system, with the highest weighted outgoing "
                f"coherence score of {top_driver['woi']:+.2f} and its strongest influence "
                f"through the {sign} link {link_text}, which indicates a "
                f"{stable_phrase} and structurally significant interaction. At the same time, the broader pattern "
                f"shows an average agreement level of {average_agreement:.2f}, suggesting that the "
                f"dominant structure is interpretable with reasonable confidence."
            )
        return (
            f"{driver} emerges as the top driving policy in the system based on its weighted outgoing coherence "
            f"score of {top_driver['woi']:+.2f}, but no single outgoing relationship "
            f"yet dominates strongly enough to define the structure on its own. This suggests the system remains "
            f"diffuse, with influence spread across multiple pathways that should be interpreted with care."
        )

    def supporting_interpretation(self, insights: Dict) -> str:
        """`_build_supporting_interpretation`: one of five sentences, with the `Interpretation:` prefix."""
        contested = insights["agreement"]["contested"][0] if insights["agreement"]["contested"] else None
        agreement = insights["agreement"]["average_agreement"]
        if contested and agreement >= INSIGHTS_THRESHOLDS["STABLE_AGREEMENT"]:
            key = "STABLE_CONTESTED"
        elif contested and agreement >= INSIGHTS_THRESHOLDS["WORKABLE_AGREEMENT"]:
            key = "WORKABLE_CONTESTED"
        elif contested:
            key = "CONTESTED"
        elif agreement >= INSIGHTS_THRESHOLDS["STABLE_AGREEMENT"]:
            key = "STABLE"
        else:
            key = "MODERATE"
        return f"{INSIGHTS_TEXT['INTERPRETATION_LABEL']} {INTERPRETATIONS[key]}"

    def _policy_card(self, row: Optional[Dict], key: str, unit: str) -> PolicyCardText:
        """`_top_driver_card` / `_top_dependent_card`."""
        value = f"{row[key]:+.2f} {unit}" if row else INSIGHTS_TEXT["NOT_AVAILABLE"]
        return PolicyCardText(hero=self.policy_from_row(row), value_text=value)

    def _strongest_link_card(self, result: AggregationResult, graph: Dict) -> StrongestLinkText:
        """`_strongest_link_card` with the L13 value text."""
        value = (
            f"{graph['strongest_pos']:+.2f} positive link"
            if graph["strongest_pos_pair"]
            else INSIGHTS_TEXT["NO_STRONG_LINK"]
        )
        return StrongestLinkText(
            main=self.format_pair(result, graph["strongest_pos_pair"]),
            value_text=value,
            caption=INSIGHTS_TEXT["STRONGEST_RELATION"],
        )

    def _most_contested_card(self, result: AggregationResult, contested: Optional[Dict]) -> MostContestedText:
        """`_most_contested_card`: the only `↔` in the API, and `Rating agreement` (L12)."""
        if not contested:
            return MostContestedText(
                main=INSIGHTS_TEXT["NO_CONTESTED_LINK"],
                value_text=INSIGHTS_TEXT["STABLE"],
                caption=INSIGHTS_TEXT["MODERATE_DISAGREEMENT"],
            )
        ratio = contested["agreement_ratio"]
        high = ratio < INSIGHTS_THRESHOLDS["HIGH_DISAGREEMENT_RATIO"]
        return MostContestedText(
            main=self._insights.pair_label(result, contested["i"], contested["j"], INSIGHTS_ARROWS["UNDIRECTED"]),
            value_text=f"{INSIGHTS_TEXT['MOST_CONTESTED_VALUE_LABEL']}: {ratio:.2f}",
            caption=INSIGHTS_TEXT["HIGH_DISAGREEMENT" if high else "MODERATE_DISAGREEMENT"],
        )

    def _conflict_ratio_card(self, graph: Dict) -> ConflictRatioText:
        """`_conflict_ratio_card`: negative share of the active links."""
        active = graph["positive_edges"] + graph["negative_edges"]
        ratio = (graph["negative_edges"] / active) if active else 0.0
        if ratio <= INSIGHTS_THRESHOLDS["LOW_CONFLICT_RATIO"]:
            caption = INSIGHTS_TEXT["LOW_CONFLICT"]
        elif ratio <= INSIGHTS_THRESHOLDS["MODERATE_CONFLICT_RATIO"]:
            caption = INSIGHTS_TEXT["MODERATE_CONFLICT"]
        else:
            caption = INSIGHTS_TEXT["HIGH_CONFLICT"]
        return ConflictRatioText(
            ratio=ratio,
            main_text=f"{ratio * 100:.0f}%",
            value_text=f"{graph['negative_edges']} of {active} active links",
            caption=caption,
        )


insights_text_feature = InsightsTextFeature()
