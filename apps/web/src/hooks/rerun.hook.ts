import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MUTATION_KEYS } from "@/constants/query.constants";
import { previewQueryKey } from "@/hooks/aggregation.hook";
import { requestNow, useRunAnalysis } from "@/hooks/analysis.hook";
import { useScales } from "@/hooks/scales.hook";
import type { StepId } from "@/interfaces/project.interface";
import { previewAggregation } from "@/services/aggregation.service";
import { checkMatrices } from "@/services/matrices.service";
import { useProjectStore } from "@/store/project.store";
import { previewRequest, tieKey } from "@/utils/analysis-request.utils";
import { namesKey } from "@/utils/flow.utils";

/** What Re-run did: ran, or opened a step that needs an answer first. */
export type RerunOutcome = { kind: "ran" } | { kind: "open"; step: StepId };

/**
 * Re-run from Results: `/matrices/check` (incomplete → Review), missing weights → Weights,
 * Majority with unresolved ties → Ties, otherwise `/analysis` with a new snapshot.
 */
export function useRerun(onOpen: (step: StepId) => void) {
  const rules = useScales().data?.rules;
  const run = useRunAnalysis();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationKey: [...MUTATION_KEYS.RUN_ANALYSIS, "rerun"],
    mutationFn: async (): Promise<RerunOutcome> => {
      if (!rules) throw new Error("The assessment options are not loaded.");
      const store = useProjectStore.getState();
      const request = requestNow(rules);
      const { aggregation: _, ...project } = request;
      const check = await checkMatrices(project);
      const options = check.aggregation_options;
      store.setAggregationOptions({
        ...options,
        forNames: namesKey(store.decisionMakers),
      });
      if (!check.complete) return { kind: "open", step: "review" };
      const method = request.aggregation.method;
      const choice = options.method_choice_available;
      if (choice && method === "weighted" && !request.aggregation.weights) {
        return { kind: "open", step: "weights" };
      }
      if (choice && method === "majority") {
        const preview = previewRequest(request);
        const data = await queryClient.fetchQuery({
          queryKey: previewQueryKey(preview),
          queryFn: () => previewAggregation(preview),
        });
        store.setTieCount(data.ties.length);
        const ids = store.policies.map((policy) => policy.id);
        const unresolved = data.ties.some((tie) => {
          const chosen = store.tieChoices[tieKey(ids[tie.row], ids[tie.col])];
          return !tie.tied_options.some((option) => option.label === chosen);
        });
        if (unresolved) return { kind: "open", step: "ties" };
      }
      await run.mutateAsync(request);
      return { kind: "ran" };
    },
    onSuccess: (outcome) => {
      if (outcome.kind === "open") onOpen(outcome.step);
    },
  });
  return mutation;
}
