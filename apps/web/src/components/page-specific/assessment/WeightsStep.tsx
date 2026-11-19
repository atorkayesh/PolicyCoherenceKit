import { useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { runError } from "@/components/page-specific/assessment/RunError";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { Input } from "@/components/ui/input";
import { WEIGHTS_TEXT } from "@/constants/aggregation.constants";
import { FLOW_TEXT } from "@/constants/flow.constants";
import { QUERY_KEYS } from "@/constants/query.constants";
import { STEP_TEXT } from "@/constants/steps.constants";
import { useRunFromStep } from "@/hooks/analysis.hook";
import { useWeightCheck } from "@/hooks/weights.hook";
import type { StepError, StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import type { WeightCheckRequest } from "@/interfaces/weights.interface";
import { cn } from "@/lib/utils";
import { checkWeights } from "@/services/weights.service";
import { useProjectStore } from "@/store/project.store";
import { stepError } from "@/utils/api.utils";
import { pyFloatStr } from "@/utils/format.utils";

/** Weighted method: one raw text per decision-maker, the API's live sum, validated on OK. */
export function WeightsStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const { rules } = scales;
  const decisionMakers = useProjectStore((state) => state.decisionMakers);
  const weightTexts = useProjectStore((state) => state.weightTexts);
  const setWeightText = useProjectStore((state) => state.setWeightText);
  const setWeights = useProjectStore((state) => state.setWeights);
  const queryClient = useQueryClient();
  const { run, start } = useRunFromStep(rules);
  const inputs = useRef<(HTMLInputElement | null)[]>([]);
  const [error, setError] = useState<StepError | null>(null);
  const [checking, setChecking] = useState(false);
  const body: WeightCheckRequest = {
    decision_makers: decisionMakers.map((dm) => dm.name),
    weights: decisionMakers.map((dm) => weightTexts[dm.id] || null),
  };
  const live = useWeightCheck(body);

  const submit = async () => {
    setError(null);
    run.reset();
    setChecking(true);
    try {
      const data = await queryClient.fetchQuery({
        queryKey: [QUERY_KEYS.WEIGHT_CHECK, JSON.stringify(body)],
        queryFn: () => checkWeights(body),
      });
      if (!data.valid) {
        const first = data.first_error;
        setError({ title: first?.title, message: first?.message ?? "" });
        if (first?.index != null) inputs.current[first.index]?.focus();
        return;
      }
      setWeights(
        Object.fromEntries(
          decisionMakers.map((dm, i) => [dm.id, data.weights[i] ?? 0]),
        ),
      );
      start("weights", () => nav.onOpen("results"));
    } catch (failure) {
      setError(stepError(failure));
    } finally {
      setChecking(false);
    }
  };

  return (
    <StepFrame
      number={nav.number}
      title={STEP_TEXT.weights.title}
      help={WEIGHTS_TEXT.HELP(
        pyFloatStr(rules.weight_min),
        pyFloatStr(rules.weight_max),
        pyFloatStr(rules.weight_sum_target),
        pyFloatStr(rules.weight_sum_tolerance),
      )}
      error={error ?? (run.error ? runError(run.error, nav.onOpen) : null)}
      pending={checking || run.isPending}
      nextLabel={FLOW_TEXT.RUN}
      onNext={() => void submit()}
      onBack={nav.onBack}
    >
      <div className="flex flex-col gap-3">
        {decisionMakers.map((dm, i) => (
          <label
            key={dm.id}
            className="flex items-center justify-between gap-3 text-sm"
          >
            <span className="min-w-0 truncate font-medium">{dm.name}</span>
            <Input
              ref={(element) => {
                inputs.current[i] = element;
              }}
              inputMode="decimal"
              value={weightTexts[dm.id] ?? ""}
              onChange={(event) => setWeightText(dm.id, event.target.value)}
              className="h-10 w-32 text-right text-base sm:text-sm"
            />
          </label>
        ))}
        <p
          aria-live="polite"
          className={cn(
            "text-right text-sm font-medium",
            live.data && !live.data.within_tolerance && "text-destructive",
          )}
        >
          {live.data?.sum_text ?? ""}
        </p>
      </div>
    </StepFrame>
  );
}
