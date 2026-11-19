/** Results Insights card titles and labels (results_insights_tab.py:752-1072). */
export const INSIGHTS_TEXT = {
  KEY_INSIGHTS: "Key Insights",
  OVERVIEW: "Analysis Overview",
  POLICIES: "Policies",
  DECISION_MAKERS: "Decision-makers",
  METHOD: "Aggregation method",
  AGREEMENT: "Decision-maker agreement",
  AGREEMENT_HELP: "Average rank agreement between decision-makers (0 to 1).",
  HEALTH: "System Health",
  SYNERGY: "Synergy",
  CONFLICT: "Conflict",
  NEUTRAL: "Neutral/Uncertain",
  TOP_DRIVER: "Top Driving Policy",
  TOP_DEPENDENT: "Top Influenced Policy",
  STRONGEST_LINK: "Strongest Link",
  MOST_CONTESTED: "Most Contested",
  CONTESTED_HELP:
    "Rating agreement is the share of decision-makers giving the most common rating.",
  CONFLICT_RATIO: "Conflict Ratio",
  /** Health bars are at least this wide (percent) so a zero share stays visible. */
  MIN_BAR_PERCENT: 3,
} as const;
