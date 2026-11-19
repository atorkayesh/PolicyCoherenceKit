import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ChoiceList } from "@/components/page-specific/assessment/ChoiceList";
import { runError } from "@/components/page-specific/assessment/RunError";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { METHOD_TEXT } from "@/constants/aggregation.constants";
import { FLOW_TEXT } from "@/constants/flow.constants";
import { STEP_TEXT } from "@/constants/steps.constants";
import { previewQueryKey } from "@/hooks/aggregation.hook";
import { requestNow, useRunFromStep } from "@/hooks/analysis.hook";
import { useMatrixCheck } from "@/hooks/matrix-check.hook";
import type { StepError, StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { previewAggregation } from "@/services/aggregation.service";
import { useProjectStore } from "@/store/project.store";
import { previewRequest } from "@/utils/analysis-request.utils";
import { stepError } from "@/utils/api.utils";
import { currentOptions, namesKey, stepAfterMethod } from "@/utils/flow.utils";

/**
 * How to combine the ratings: a choice with enough decision-makers, otherwise the forced method
 * with an explanation. Runs the analysis when no weights or median step follows; Majority previews
 * first and opens the ties step only when there are ties.
 */
export function MethodStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const { rules } = scales;
  const state = useProjectStore();
  const options = currentOptions(state);
  const check = useMatrixCheck();
  const queryClient = useQueryClient();
  const { run, start } = useRunFromStep(rules);
  const [error, setError] = useState<StepError | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const method = state.method ?? rules.default_method;
  const n = options?.decision_maker_count ?? state.decisionMakers.length;
  const isLast = stepAfterMethod(method, options, 0) === null;
  const forcedLabel =
    scales.methods.find((m) => m.key === rules.forced_method)?.label ??
    rules.forced_method;

  // Options computed for other decision-makers count as unknown: store the fresh check.
  useEffect(() => {
    if (options || !check.data) return;
    useProjectStore.getState().setAggregationOptions({
      ...check.data.aggregation_options,
      forNames: namesKey(useProjectStore.getState().decisionMakers),
    });
  }, [options, check.data]);

  const runNow = () => start("method", () => nav.onOpen("results"));

  const submit = async () => {
    if (!options) return;
    setError(null);
    run.reset();
    if (!state.method) state.setMethod(method);
    if (!isLast) return nav.onAdvance();
    if (options.method_choice_available && method === "majority") {
      setPreviewing(true);
      try {
        const request = previewRequest(requestNow(rules));
        const data = await queryClient.fetchQuery({
          queryKey: previewQueryKey(request),
          queryFn: () => previewAggregation(request),
        });
        useProjectStore.getState().setTieCount(data.ties.length);
        if (data.ties.length > 0) return nav.onAdvance();
      } catch (failure) {
        return setError(stepError(failure));
      } finally {
        setPreviewing(false);
      }
    }
    runNow();
  };

  const shownError =
    error ?? (run.error ? runError(run.error, nav.onOpen) : null);
  return (
    <StepFrame
      number={nav.number}
      title={STEP_TEXT.method.title}
      help={
        options
          ? options.method_choice_available
            ? METHOD_TEXT.CHOICE_HELP(n)
            : METHOD_TEXT.FORCED_HELP(n)
          : FLOW_TEXT.CHECKING
      }
      error={shownError ?? (check.error ? stepError(check.error) : null)}
      pending={(!options && check.isFetching) || previewing || run.isPending}
      nextLabel={isLast ? FLOW_TEXT.RUN : FLOW_TEXT.NEXT}
      onNext={() => void submit()}
      onBack={nav.onBack}
    >
      {options?.method_choice_available && (
        <ChoiceList
          name="method"
          label={METHOD_TEXT.GROUP_LABEL}
          options={scales.methods}
          value={method}
          onChange={state.setMethod}
        />
      )}
      {options && !options.method_choice_available && (
        <p className="rounded-lg border bg-card px-4 py-3 text-sm">
          {METHOD_TEXT.FORCED_NOTE(
            rules.method_choice_min_decision_makers,
            forcedLabel,
          )}
        </p>
      )}
    </StepFrame>
  );
}
