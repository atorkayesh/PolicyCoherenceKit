import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { NetworkChartData } from "@/interfaces/chart.interface";

const CODES = ["P1", "P2", "P3"];
const POLICIES = ["Energy", "Water", "Food"];

/** A 2-decision-maker run where Average was forced (3 policies, valid PCA). */
export const ANALYSIS: AnalysisData = {
  project_name: "Nexus",
  aggregation: {
    requested_method: "average",
    method: "average",
    method_label: "Average",
    method_forced: true,
    decision_maker_count: 2,
    decision_makers: ["Alice", "Bob"],
    policies: POLICIES,
    codes: CODES,
    weights: null,
    median_choice: null,
    scores: [
      [0, 1.5, -0],
      [-2.25, 0, 0.5],
      [0, 3, 0],
    ],
    bands: [
      ["Neutral", "Reinforcing", "Neutral"],
      ["Counteracting", "Neutral", "Enabling"],
      ["Neutral", "Indivisible", "Neutral"],
    ],
    ordinal_cells: null,
    ties: [],
    ready: true,
  },
  coherence_scores: [
    {
      code: "P1",
      policy: "Energy",
      oi: 1,
      ii: 1,
      woi: 1.5,
      wii: -2.25,
      oi_band: "medium",
      ii_band: "medium",
      woi_band: "positive",
      wii_band: "strong_negative",
    },
    {
      code: "P2",
      policy: "Water",
      oi: 2,
      ii: 2,
      woi: -1.75,
      wii: 4.5,
      oi_band: "very_high",
      ii_band: "very_high",
      woi_band: "negative",
      wii_band: "strong_positive",
    },
    {
      code: "P3",
      policy: "Food",
      oi: 1,
      ii: 0,
      woi: 0,
      wii: -0,
      oi_band: "medium",
      ii_band: "low",
      woi_band: "zero",
      wii_band: "zero",
    },
  ],
  range_of_influence: {
    hmax: 1,
    rows: [
      { code: "P1", policy: "Energy", entropy: 0, category: "Low" },
      { code: "P2", policy: "Water", entropy: 0.9183, category: "High" },
      { code: "P3", policy: "Food", entropy: 0, category: "Low" },
    ],
  },
  pca: {
    valid: true,
    explained: [62.5, 30.1],
    total_explained: 92.6,
    points: CODES.map((code, index) => ({
      index,
      code,
      policy: POLICIES[index],
      label: `${code}:  ${POLICIES[index]}`,
      x: [-1.2, 0.4, 0.8][index],
      y: [0.3, -0.9, 0.6][index],
      entropy_category: ["Low", "High", "Low"][index],
    })),
    bounds: { x_min: -1.68, x_max: 1.28, y_min: -1.2, y_max: 0.9 },
    x_axis_label: "PC1 (62.5%)",
    y_axis_label: "PC2 (30.1%)",
    stats_text: "PC1: 62.5%   PC2: 30.1%   Total explained: 92.6%",
    message: null,
  },
  network: {
    node_count: 3,
    edge_count: 4,
    density: 0.6667,
    isolated_count: 0,
    stats_text: "3 nodes  |  4 directed edges  |  density: 0.6667",
    centrality: [
      { code: "P1", policy: "Energy", betweenness: 0, closeness: 0.5 },
      { code: "P2", policy: "Water", betweenness: 0.5, closeness: 0.6667 },
      { code: "P3", policy: "Food", betweenness: 0, closeness: 0.4 },
    ],
    centrality_ranking: ["P2", "P1", "P3"],
  },
  insights: {
    rows: [
      { code: "P1", policy: "Energy", role: "driver" },
      { code: "P2", policy: "Water", role: "dependent" },
      { code: "P3", policy: "Food", role: "balanced" },
    ],
    health: { score: 50, synergy: 50, conflict: 25, neutral_uncertain: 0 },
    texts: {
      story:
        "Energy (P1) drives Water (P2) through the positive link Energy (P1) → Water (P2), while Food (P3) stays balanced.",
      interpretation_label: "Interpretation:",
      interpretation_text: "The system is moderately coherent.",
      overview_agreement_text: "0.75",
      tag_top_driver: "Top Driving Policy: Energy (P1)",
      tag_strongest_link: "Strongest Link: Food (P3) → Water (P2)",
      tag_contested: "Contested: Water (P2) → Energy (P1)",
      top_driver: { hero: "Energy (P1)", value_text: "+1.50 WOI" },
      top_dependent: { hero: "Water (P2)", value_text: "+4.50 WII" },
      strongest_link: {
        main: "Food (P3) → Water (P2)",
        value_text: "+3.00 positive link",
        caption: "Strongest relation",
      },
      most_contested: {
        main: "Water (P2) ↔ Energy (P1)",
        value_text: "Rating agreement: 0.50",
        caption: "Moderate disagreement",
      },
      conflict_ratio: {
        ratio: 0.25,
        main_text: "25%",
        value_text: "1 of 4 active links",
        caption: "Low systemic conflict",
      },
    },
  },
};

/** Two policies: PCA cannot run. */
export const ANALYSIS_PCA_INVALID: AnalysisData = {
  ...ANALYSIS,
  pca: {
    valid: false,
    explained: [],
    total_explained: null,
    points: [],
    bounds: null,
    x_axis_label: null,
    y_axis_label: null,
    stats_text: null,
    message: "PCA requires at least 3 policies.",
  },
};

const node = (
  index: number,
  x: number,
  y: number,
  extra: Partial<NetworkChartData["nodes"][number]> = {},
) => ({
  index,
  code: CODES[index],
  policy: POLICIES[index],
  label: `${CODES[index]}:  ${POLICIES[index]}`,
  x,
  y,
  isolated: false,
  is_focus: false,
  radius: 18,
  fill: "#2c4a6e",
  ...extra,
});

/** Full network: a two-way pair P1 ⇄ P2, a negative edge and an isolated node P3. */
export const NETWORK_FULL: NetworkChartData = {
  layout: "force_directed",
  layout_label: "Force-Directed",
  focus: null,
  canvas: { width: 600, height: 600 },
  title: null,
  empty_message: null,
  nodes: [
    node(0, 100, 300),
    node(1, 500, 300),
    node(2, 300, 80, { isolated: true, fill: "#aaaaaa" }),
  ],
  edges: [
    {
      source: 0,
      target: 1,
      score: 1.5,
      sign: "positive",
      colour: "#1a6e3c",
      width: 2.5,
      two_way: true,
      label: null,
    },
    {
      source: 1,
      target: 0,
      score: -2.25,
      sign: "negative",
      colour: "#b71c1c",
      width: 4,
      two_way: true,
      label: null,
    },
  ],
  stats: {
    node_count: 3,
    edge_count: 2,
    density: 0.3333,
    isolated_count: 1,
    text: "3 nodes  |  2 directed edges  |  density: 0.3333  |  1 isolated",
  },
};

/** Ego view of the isolated P3: title and the empty message. */
export const NETWORK_EGO_EMPTY: NetworkChartData = {
  ...NETWORK_FULL,
  focus: 2,
  title: "Ego Network:  P3  (Food)",
  empty_message: "P3 has no direct connections.",
  nodes: [node(2, 300, 300, { is_focus: true, radius: 22, fill: "#5a7fa8" })],
  edges: [],
};
