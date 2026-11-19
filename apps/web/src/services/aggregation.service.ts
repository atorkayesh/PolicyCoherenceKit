import { API_ENDPOINTS } from "@/constants/api.constants";
import {
  type AggregationData,
  type AnalysisRequest,
  aggregationResponseSchema,
} from "@/interfaces/aggregation.interface";
import { apiData, jsonPost } from "@/utils/api.utils";

/** Aggregate without analysing: lists the majority ties (scores are null until resolved). */
export function previewAggregation(
  request: AnalysisRequest,
): Promise<AggregationData> {
  return apiData(
    API_ENDPOINTS.AGGREGATION_PREVIEW,
    jsonPost(request),
    aggregationResponseSchema,
  );
}
