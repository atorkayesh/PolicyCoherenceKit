import { decisionMakerWord } from "@/utils/format.utils";

export const RESULTS_TEXT = {
  TITLE: "Results",
  /** app.py:2605-2610 */
  SUBTITLE: (project: string, method: string, n: number) =>
    `Analysis complete for "${project}"  |  method: ${method}  |  ${n} ${decisionMakerWord(n)}`,
  FORCED_NOTE: (min: number, method: string) =>
    `Fewer than ${min} decision-makers: the ratings were combined with ${method}.`,
  OUTDATED: "Your inputs changed since this analysis. Run again to update.",
  RERUN: "Re-run",
} as const;

export const TAB_IDS = {
  INSIGHTS: "insights",
  AGGREGATED: "aggregated",
  SCORES: "scores",
  RANGE: "range",
  PCA: "pca",
  NETWORK: "network",
  AI: "ai",
} as const;

export const TAB_LABELS: Record<keyof typeof TAB_IDS, string> = {
  INSIGHTS: "Results Insights",
  AGGREGATED: "Aggregated",
  SCORES: "Coherence Scores",
  RANGE: "Range of Influence",
  PCA: "PCA",
  NETWORK: "Network Analysis",
  AI: "AI Interpretation",
};

/** Aggregated tab (aggregation_tab.py:319, 443-449). */
export const AGGREGATED_TEXT = {
  LEGEND: "Aggregated score scale:",
  CELL_TITLE: (codeRow: string, codeCol: string, score: string, band: string) =>
    `${codeRow} → ${codeCol}\nScore: ${score}\nColour band: ${band}`,
  DIAGONAL_TITLE: (code: string) => `${code} → ${code}\nScore: 0.00 (diagonal)`,
} as const;

/** Shared table column headers (item 27: `Code` / `Policy` like the XLSX). */
export const TABLE_TEXT = {
  CODE: "Code",
  POLICY: "Policy",
  CODE_TITLE: "Policy code",
} as const;

/** Coherence Scores tab (coherence_scores_tab.py:65-69, 197-200, 320-324). */
export const SCORES_TEXT = {
  LEGEND: [
    {
      abbr: "OI:",
      text: "Outgoing Influence — number of policies this policy affects (non-zero row cells)",
    },
    {
      abbr: "II:",
      text: "Incoming Influence — number of policies that affect this policy (non-zero col cells)",
    },
    {
      abbr: "WOI:",
      text: "Weighted Outgoing — sum of scores in the row (strength of influence exerted)",
    },
    {
      abbr: "WII:",
      text: "Weighted Incoming — sum of scores in the column (strength of influence received)",
    },
  ],
  COLUMNS: [
    {
      key: "oi",
      label: "OI",
      title: "Outgoing Influence\n(non-zero row count)",
    },
    {
      key: "ii",
      label: "II",
      title: "Incoming Influence\n(non-zero col count)",
    },
    { key: "woi", label: "WOI", title: "Weighted Outgoing\n(row sum)" },
    { key: "wii", label: "WII", title: "Weighted Incoming\n(col sum)" },
  ],
} as const;

/** Range of Influence tab (range_of_influence_tab.py:190-225, 375-377). */
export const RANGE_TEXT = {
  SUBTITLE: (hmax: string) => `max entropy = ${hmax}`,
  EXPLANATION:
    "Entropy measures how evenly a policy distributes its outgoing influence. High = spread across many policies. Low = concentrated on few.",
  LOW_NOTE: "Low also covers policies with no outgoing influence.",
  CATEGORIES: "Categories:",
  ENTROPY: "Entropy",
  ENTROPY_TITLE:
    "Shannon entropy H (base 2)\n0 = fully concentrated\nlog2(n-1) = perfectly distributed\n(max = 1 with 2 policies)",
  CATEGORY: "Category",
  CATEGORY_TITLE:
    "Influence distribution category\nbased on fraction of max entropy",
} as const;

/** PCA tab (pca_tab.py:289-389). */
export const PCA_TEXT = {
  TITLE: "PCA",
  COLOUR_BY_ENTROPY: "Colour by entropy category",
  HINT: "Hover over or tap a point to see the full policy name.",
  ENTROPY_LEGEND: "Entropy categories:",
} as const;

/** Network tab (network_tab.py:64-1262). */
export const NETWORK_TEXT = {
  TITLE: "Network Analysis",
  LAYOUT: "Layout",
  FOCUS: "Focus policy",
  FULL_NETWORK: "Full Network",
  FOCUS_OPTION: (code: string, policy: string) => `${code}: ${policy}`,
  POSITIVE: "Positive",
  NEGATIVE: "Negative",
  ISOLATED: "Isolated",
  LOADING: "Loading the network…",
  CENTRALITY: "Centrality Measures",
  CENTRALITY_HELP: "Betweenness: broker role  |  Closeness: reachability",
  BETWEENNESS: "Betweenness",
  CLOSENESS: "Closeness",
} as const;

/** Export bar labels and file names (legacy names). */
export const EXPORT_TEXT = {
  XLSX: "Export Excel",
  NETWORK_PNG: "Save Network plot as PNG",
  NETWORK_SVG: "Save Network plot as SVG",
  PCA_PNG: "Save PCA plot as PNG",
  PCA_SVG: "Save PCA plot as SVG",
  TXT: "Download as TXT",
  PDF: "Download as PDF",
  NOTHING_TO_SAVE_TITLE: "Nothing to Save",
  NOTHING_TO_SAVE: "Generate an interpretation first.",
} as const;

export const EXPORT_FILES = {
  XLSX_FALLBACK: "coherence.xlsx",
  NETWORK: "network_plot",
  PCA: "pca_plot",
} as const;
