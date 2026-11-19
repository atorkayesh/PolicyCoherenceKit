import { ChoiceList } from "@/components/page-specific/assessment/ChoiceList";
import { runError } from "@/components/page-specific/assessment/RunError";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { MEDIAN_TEXT } from "@/constants/aggregation.constants";
import { FLOW_TEXT } from "@/constants/flow.constants";
import { STEP_TEXT } from "@/constants/steps.constants";
import { useRunFromStep } from "@/hooks/analysis.hook";
import type { StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";

/** Median with an even count: lower or upper median, then run. */
export function MedianStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const stored = useProjectStore((state) => state.medianChoice);
  const setMedianChoice = useProjectStore((state) => state.setMedianChoice);
  const count = useProjectStore((state) => state.decisionMakers.length);
  const { run, start } = useRunFromStep(scales.rules);
  const value = stored ?? scales.rules.default_median_choice;

  const submit = () => {
    run.reset();
    if (!stored) setMedianChoice(value);
    start("median", () => nav.onOpen("results"));
  };

  return (
    <StepFrame
      number={nav.number}
      title={STEP_TEXT.median.title}
      help={MEDIAN_TEXT.HELP(count)}
      error={run.error ? runError(run.error, nav.onOpen) : null}
      pending={run.isPending}
      nextLabel={FLOW_TEXT.RUN}
      onNext={submit}
      onBack={nav.onBack}
    >
      <ChoiceList
        name="median"
        label={MEDIAN_TEXT.GROUP_LABEL}
        options={scales.median_choices}
        value={value}
        onChange={setMedianChoice}
      />
    </StepFrame>
  );
}
