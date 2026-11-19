import { DecisionMakersStep } from "@/components/page-specific/assessment/DecisionMakersStep";
import { ImportStep } from "@/components/page-specific/assessment/ImportStep";
import { MatrixStep } from "@/components/page-specific/assessment/MatrixStep";
import { MedianStep } from "@/components/page-specific/assessment/MedianStep";
import { MethodStep } from "@/components/page-specific/assessment/MethodStep";
import { PoliciesStep } from "@/components/page-specific/assessment/PoliciesStep";
import { ProjectStep } from "@/components/page-specific/assessment/ProjectStep";
import { ReviewStep } from "@/components/page-specific/assessment/ReviewStep";
import { TiesStep } from "@/components/page-specific/assessment/TiesStep";
import { WeightsStep } from "@/components/page-specific/assessment/WeightsStep";
import type { StepId, StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { matrixStepIndex } from "@/utils/flow.utils";

/** The question component of `step`. Only the open step is mounted. */
export function FlowStep({
  step,
  scales,
  ...nav
}: StepProps & { step: StepId; scales: ScalesData }) {
  switch (step) {
    case "project":
      return <ProjectStep scales={scales} {...nav} />;
    case "decision-makers":
      return <DecisionMakersStep scales={scales} {...nav} />;
    case "policies":
      return <PoliciesStep scales={scales} {...nav} />;
    case "import":
      return <ImportStep scales={scales} {...nav} />;
    case "review":
      return <ReviewStep {...nav} />;
    case "method":
      return <MethodStep scales={scales} {...nav} />;
    case "weights":
      return <WeightsStep scales={scales} {...nav} />;
    case "median":
      return <MedianStep scales={scales} {...nav} />;
    case "ties":
      return <TiesStep scales={scales} {...nav} />;
    default: {
      const index = matrixStepIndex(step);
      return index === null ? null : (
        <MatrixStep index={index} scales={scales} {...nav} />
      );
    }
  }
}
