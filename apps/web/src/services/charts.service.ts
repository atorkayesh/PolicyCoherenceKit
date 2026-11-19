import { API_ENDPOINTS } from "@/constants/api.constants";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import {
  type NetworkChartData,
  networkChartResponseSchema,
} from "@/interfaces/chart.interface";
import { apiData, jsonPost } from "@/utils/api.utils";

/** Network chart data for a layout and an optional focus policy (0-based; null = full network). */
export function getNetworkChartData(
  request: AnalysisRequest,
  layout: string,
  focus: number | null,
): Promise<NetworkChartData> {
  const query = new URLSearchParams({ layout });
  if (focus !== null) query.set("focus", String(focus));
  return apiData(
    `${API_ENDPOINTS.CHART_NETWORK}?${query}`,
    jsonPost(request),
    networkChartResponseSchema,
  );
}
