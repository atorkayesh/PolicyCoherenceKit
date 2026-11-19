import { API_ENDPOINTS } from "@/constants/api.constants";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import {
  type AnalysisData,
  analysisResponseSchema,
} from "@/interfaces/analysis.interface";
import { apiData, jsonPost } from "@/utils/api.utils";

/** Aggregate and run every analysis for the request. */
export function runAnalysis(request: AnalysisRequest): Promise<AnalysisData> {
  return apiData(
    API_ENDPOINTS.ANALYSIS,
    jsonPost(request),
    analysisResponseSchema,
  );
}
