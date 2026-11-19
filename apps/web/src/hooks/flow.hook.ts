import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { useProjectStore } from "@/store/project.store";
import { answeredSteps, questionSteps } from "@/utils/flow.utils";

/** Ordered question steps for the current answers, and which are answered. */
export function useFlowSteps() {
  const flow = useProjectStore(
    useShallow((state) => ({
      decisionMakers: state.decisionMakers,
      method: state.method,
      aggregationOptions: state.aggregationOptions,
      tieCount: state.tieCount,
      answeredList: state.answered,
      answeredMatrices: state.answeredMatrices,
      hasResults: state.results !== null,
    })),
  );
  const { decisionMakers, method, aggregationOptions, tieCount } = flow;
  const steps = useMemo(
    () =>
      questionSteps({ decisionMakers, method, aggregationOptions, tieCount }),
    [decisionMakers, method, aggregationOptions, tieCount],
  );
  const answered = useMemo(
    () =>
      answeredSteps(
        flow.answeredList,
        flow.decisionMakers,
        flow.answeredMatrices,
      ),
    [flow.answeredList, flow.decisionMakers, flow.answeredMatrices],
  );
  return { steps, answered, hasResults: flow.hasResults };
}
