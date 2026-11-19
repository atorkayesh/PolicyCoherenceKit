import { useMutation } from "@tanstack/react-query";
import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { MUTATION_KEYS } from "@/constants/query.constants";
import { useScales } from "@/hooks/scales.hook";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import type { FixedStepId } from "@/interfaces/project.interface";
import { runAnalysis } from "@/services/analysis.service";
import { useProjectStore } from "@/store/project.store";
import {
  buildAnalysisRequest,
  requestKey,
} from "@/utils/analysis-request.utils";

/** Run the analysis and store the results with the request they were computed from. */
export function useRunAnalysis() {
  const setResults = useProjectStore((state) => state.setResults);
  return useMutation({
    mutationKey: MUTATION_KEYS.RUN_ANALYSIS,
    mutationFn: runAnalysis,
    onSuccess: (data, request: AnalysisRequest) => setResults(request, data),
  });
}

/** The request for the current answers (null until the scales are loaded). */
export function useCurrentRequest(): AnalysisRequest | null {
  const rules = useScales().data?.rules;
  const inputs = useProjectStore(
    useShallow((state) => ({
      projectName: state.projectName,
      decisionMakers: state.decisionMakers,
      policies: state.policies,
      matrices: state.matrices,
      method: state.method,
      weights: state.weights,
      medianChoice: state.medianChoice,
      tieChoices: state.tieChoices,
    })),
  );
  return useMemo(
    () => (rules ? buildAnalysisRequest(inputs, rules) : null),
    [inputs, rules],
  );
}

/** Whether the answers changed since the results were computed. */
export function useResultsOutdated(): boolean {
  const current = useCurrentRequest();
  const snapshot = useProjectStore((state) => state.snapshot);
  return useMemo(
    () =>
      snapshot !== null &&
      current !== null &&
      requestKey(current) !== requestKey(snapshot),
    [current, snapshot],
  );
}

/** The request for the answers in the store right now (after writes made in the same event). */
export function requestNow(
  rules: Parameters<typeof buildAnalysisRequest>[1],
): AnalysisRequest {
  return buildAnalysisRequest(useProjectStore.getState(), rules);
}

/**
 * Run the analysis from the last question step: on success the step is marked answered and
 * `onDone` opens Results. Errors stay on the step (see `RunError`).
 */
export function useRunFromStep(
  rules: Parameters<typeof buildAnalysisRequest>[1],
) {
  const run = useRunAnalysis();
  const markAnswered = useProjectStore((state) => state.markAnswered);
  const start = (step: FixedStepId, onDone: () => void) => {
    run.mutate(requestNow(rules), {
      onSuccess: () => {
        markAnswered(step);
        onDone();
      },
    });
  };
  return { run, start };
}
