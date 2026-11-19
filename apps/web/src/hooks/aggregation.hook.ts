import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { QUERY_KEYS } from "@/constants/query.constants";
import { useCurrentRequest } from "@/hooks/analysis.hook";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import { previewAggregation } from "@/services/aggregation.service";
import {
  hashString,
  previewRequest,
  requestKey,
} from "@/utils/analysis-request.utils";

/** The ties preview request for the current answers (tie choices left out). */
export function useCurrentPreviewRequest(): AnalysisRequest | null {
  const request = useCurrentRequest();
  return useMemo(() => (request ? previewRequest(request) : null), [request]);
}

/** Query key of the ties preview for a request. */
export function previewQueryKey(request: AnalysisRequest) {
  return [QUERY_KEYS.AGGREGATION_PREVIEW, hashString(requestKey(request))];
}

/** `/aggregation/preview` for the current answers: the majority ties. */
export function useAggregationPreview() {
  const request = useCurrentPreviewRequest();
  return useQuery({
    queryKey: request
      ? previewQueryKey(request)
      : [QUERY_KEYS.AGGREGATION_PREVIEW],
    queryFn: () => previewAggregation(request as AnalysisRequest),
    enabled: request !== null,
    retry: false,
  });
}
