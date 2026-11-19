export const QUERY_KEYS = {
  SCALES: ["scales"],
  EXPLANATION_PROVIDERS: ["explanations", "providers"],
  MATRIX_CHECK: "matrix-check",
  WEIGHT_CHECK: "weight-check",
  AGGREGATION_PREVIEW: "aggregation-preview",
  NETWORK_CHART: "network-chart",
} as const;

export const MUTATION_KEYS = {
  VALIDATE_SETUP: ["setup", "validate"],
  RUN_ANALYSIS: ["analysis", "run"],
  IMPORT_WORKBOOK: ["imports", "workbook"],
  EXPORT_FILE: ["export"],
  EXPLANATION: ["explanation"],
} as const;

/** Debounce of the live weight sum (ms). */
export const WEIGHT_CHECK_DEBOUNCE_MS = 250;
