import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/constants/query.constants";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import { getNetworkChartData } from "@/services/charts.service";

/** Query key of the network chart data for a snapshot, layout and focus. */
export function networkChartKey(
  snapshotHash: string,
  layout: string,
  focus: number | null,
) {
  return [QUERY_KEYS.NETWORK_CHART, snapshotHash, layout, focus] as const;
}

/** Network chart data of the results snapshot; one request per layout and focus. */
export function useNetworkChartData(
  snapshot: AnalysisRequest,
  snapshotHash: string,
  layout: string,
  focus: number | null,
) {
  return useQuery({
    queryKey: networkChartKey(snapshotHash, layout, focus),
    queryFn: () => getNetworkChartData(snapshot, layout, focus),
    staleTime: Number.POSITIVE_INFINITY,
    retry: false,
  });
}
