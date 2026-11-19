import type { AggregationData, Tie } from "@/interfaces/aggregation.interface";

const POLICIES = ["Energy", "Water", "Food"];
const CODES = ["P1", "P2", "P3"];

function tie(row: number, col: number, labels: [string, number][]): Tie {
  return {
    row,
    col,
    code_row: CODES[row],
    code_col: CODES[col],
    policy_row: POLICIES[row],
    policy_col: POLICIES[col],
    tied_options: labels.map(([label, score]) => ({ label, score })),
    votes: [
      { decision_maker: "A", rating: labels[0][0] },
      { decision_maker: "B", rating: labels[1][0] },
      { decision_maker: "C", rating: labels[0][0] },
      { decision_maker: "D", rating: labels[1][0] },
      { decision_maker: "E", rating: "Neutral" },
    ],
    chosen: null,
  };
}

/** A 5-decision-maker × 3-policy Majority preview with two ties (scores null until resolved). */
export const MAJORITY_PREVIEW: AggregationData = {
  requested_method: "majority",
  method: "majority",
  method_label: "Majority Rule",
  method_forced: false,
  decision_maker_count: 5,
  decision_makers: ["A", "B", "C", "D", "E"],
  policies: POLICIES,
  codes: CODES,
  weights: null,
  median_choice: null,
  scores: [
    [0, null, 1],
    [-1, 0, null],
    [2, 0, 0],
  ],
  bands: [
    ["Neutral", "Neutral", "Enabling"],
    ["Constraining", "Neutral", "Neutral"],
    ["Reinforcing", "Neutral", "Neutral"],
  ],
  ordinal_cells: null,
  ties: [
    tie(0, 1, [
      ["Reinforcing", 2],
      ["Enabling", 1],
    ]),
    tie(1, 2, [
      ["Neutral", 0],
      ["Constraining", -1],
    ]),
  ],
  ready: false,
};

/** The same aggregation without ties (inputs changed). */
export const PREVIEW_NO_TIES: AggregationData = {
  ...MAJORITY_PREVIEW,
  ties: [],
  ready: true,
};
