export const API_V1_PREFIX = "/api/v1";

export const API_ENDPOINTS = {
  HEALTH: "/health",
  SCALES: "/scales",
  SETUP_VALIDATE: "/setup/validate",
  MATRICES_CHECK: "/matrices/check",
  WEIGHTS_CHECK: "/weights/check",
  AGGREGATION_PREVIEW: "/aggregation/preview",
  ANALYSIS: "/analysis",
  EXPORT_XLSX: "/analysis/export/xlsx",
  CHART_NETWORK: "/analysis/charts/network",
  IMPORT_WORKBOOK: "/imports/workbook",
  EXPLANATIONS: "/explanations",
  EXPLANATION_PROVIDERS: "/explanations/providers",
  EXPLANATION_PDF: "/explanations/export/pdf",
} as const;
