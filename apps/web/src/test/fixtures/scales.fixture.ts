import type { ScalesData } from "@/interfaces/scales.interface";

/** `GET /scales` as the backend contract defines it (legacy colours). */
export const SCALES: ScalesData = {
  ratings: [
    { label: "Indivisible", score: 3, fill: "#0B6E6E", text: "#ffffff" },
    { label: "Reinforcing", score: 2, fill: "#2A9D8F", text: "#ffffff" },
    { label: "Enabling", score: 1, fill: "#6BAF92", text: "#2d2d2d" },
    { label: "Neutral", score: 0, fill: "#B0B7C3", text: "#555555" },
    { label: "Constraining", score: -1, fill: "#E9C46A", text: "#2d2d2d" },
    { label: "Counteracting", score: -2, fill: "#E76F51", text: "#ffffff" },
    { label: "Cancelling", score: -3, fill: "#9B2226", text: "#ffffff" },
  ],
  diagonal_label: "Neutral",
  methods: [
    {
      key: "average",
      label: "Average",
      description:
        "Each decision-maker is weighted equally. Cell score = mean of all scores.",
    },
    {
      key: "median",
      label: "Median",
      description:
        "Uses the ordered middle rating(s) and avoids assuming equal spacing.",
    },
    {
      key: "majority",
      label: "Majority Rule",
      description:
        "The most common rating wins. Ties are flagged for manual resolution.",
    },
    {
      key: "weighted",
      label: "Weighted",
      description:
        "You assign a weight (0–1) to each DM. Weights must sum to 1.0 (±0.01).",
    },
  ],
  median_choices: [
    {
      key: "lower",
      label: "Lower Median",
      description: "Lower middle rating.",
    },
    {
      key: "upper",
      label: "Upper Median",
      description: "Upper middle rating.",
    },
  ],
  rules: {
    min_policies: 2,
    max_policies: 100,
    min_decision_makers: 1,
    max_decision_makers: 50,
    method_choice_min_decision_makers: 3,
    forced_method: "average",
    default_method: "average",
    default_median_choice: "lower",
    weight_min: 0.0,
    weight_max: 1.0,
    weight_sum_target: 1.0,
    weight_sum_tolerance: 0.01,
  },
  count_bands: [
    { key: "very_high", min_ratio: 0.75, fill: "#7799b9", text: "#ffffff" },
    { key: "high", min_ratio: 0.5, fill: "#a6bcd3", text: "#1f2937" },
    { key: "medium", min_ratio: 0.25, fill: "#d0dbe7", text: "#1f2937" },
    { key: "low", min_ratio: 0, fill: "#eae7e0", text: "#666666" },
    { key: "none", min_ratio: null, fill: "#d9d9d9", text: "#555555" },
  ],
  value_bands: [
    { key: "strong_positive", fill: "#177e40", text: "#ffffff" },
    { key: "positive", fill: "#25c263", text: "#ffffff" },
    { key: "weak_positive", fill: "#88edaf", text: "#2d2d2d" },
    { key: "zero", fill: "#d9d9d9", text: "#555555" },
    { key: "weak_negative", fill: "#f5c07a", text: "#2d2d2d" },
    { key: "negative", fill: "#e07b39", text: "#ffffff" },
    { key: "strong_negative", fill: "#ef4444", text: "#ffffff" },
  ],
  entropy_categories: [
    {
      label: "Low",
      threshold_text: "H < 25% of max",
      fill: "#a3a3a3",
      text: "#ffffff",
    },
    {
      label: "Low-to-Medium",
      threshold_text: "25% ≤ H < 50% of max",
      fill: "#a7f3d0",
      text: "#2d2d2d",
    },
    {
      label: "Medium-to-High",
      threshold_text: "50% ≤ H < 75% of max",
      fill: "#34d399",
      text: "#ffffff",
    },
    {
      label: "High",
      threshold_text: "H ≥ 75% of max",
      fill: "#059669",
      text: "#ffffff",
    },
  ],
  network: {
    layouts: [
      { key: "circular", label: "Circular" },
      { key: "force_directed", label: "Force-Directed" },
      { key: "spectral", label: "Spectral" },
      { key: "shell", label: "Shell" },
    ],
    default_layout: "force_directed",
    positive_colour: "#1a6e3c",
    negative_colour: "#b71c1c",
    isolated_colour: "#aaaaaa",
    node_colour: "#2c4a6e",
    focus_colour: "#5a7fa8",
    node_text_colour: "#ffffff",
    layout_canvas: [600, 600],
  },
  pca: { point_colour: "#2c4a6e", axis_colour: "#cccccc" },
  texts: { most_contested_value_label: "Rating agreement" },
  imports: { accept: [".xlsx"], max_bytes: 5242880 },
};

/** Wrap `data` in the API's response envelope. */
export function envelope<T>(data: T) {
  return {
    success: true,
    message: "OK",
    data,
    metadata: { timestamp: "2026-11-18T12:00:00Z" },
  };
}

/** An API error body (feature error with `data`). */
export function errorBody(code: string, message: string, data: unknown = null) {
  return { success: false, message, data, error: { code, fields: null } };
}
