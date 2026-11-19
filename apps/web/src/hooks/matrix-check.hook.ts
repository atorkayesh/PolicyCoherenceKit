import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { QUERY_KEYS } from "@/constants/query.constants";
import { useCurrentRequest } from "@/hooks/analysis.hook";
import type { ProjectInput } from "@/interfaces/aggregation.interface";
import { checkMatrices } from "@/services/matrices.service";
import { hashString, requestKey } from "@/utils/analysis-request.utils";

/** The project part of the current request (no aggregation settings). */
export function useCurrentProjectInput(): ProjectInput | null {
  const request = useCurrentRequest();
  return useMemo(() => {
    if (!request) return null;
    const { aggregation: _, ...project } = request;
    return project;
  }, [request]);
}

/** `/matrices/check` for the current answers, keyed by the project hash (sent once per change). */
export function useMatrixCheck() {
  const project = useCurrentProjectInput();
  const hash = hashString(requestKey(project));
  return useQuery({
    queryKey: [QUERY_KEYS.MATRIX_CHECK, hash],
    queryFn: () => checkMatrices(project as ProjectInput),
    enabled: project !== null,
    retry: false,
  });
}
