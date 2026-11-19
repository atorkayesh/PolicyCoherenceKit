import { useMemo } from "react";
import { MatrixGrid } from "@/components/page-specific/assessment/MatrixGrid";
import { RatingLegend } from "@/components/page-specific/assessment/RatingLegend";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { MATRIX_TEXT } from "@/constants/steps.constants";
import type { StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";
import { countFilled } from "@/utils/matrix.utils";

/** Filled-cell progress of one matrix (counted in the browser; completeness comes from the API). */
function MatrixProgress({ dmId }: { dmId: string }) {
  const matrix = useProjectStore((state) => state.matrices[dmId]);
  const { filled, total } = useMemo(() => countFilled(matrix ?? []), [matrix]);
  return (
    <p className="text-sm text-muted-foreground" aria-live="polite">
      {MATRIX_TEXT.PROGRESS(filled, total)}
    </p>
  );
}

/** One decision-maker's ratings. OK marks the matrix answered (completeness is checked on Review). */
export function MatrixStep({
  index,
  scales,
  ...nav
}: StepProps & { index: number; scales: ScalesData }) {
  const decisionMakers = useProjectStore((state) => state.decisionMakers);
  const dm = decisionMakers[index];
  const ratings = useMemo(
    () => scales.ratings.map((rating) => rating.label),
    [scales.ratings],
  );
  if (!dm) return null;

  return (
    <StepFrame
      number={nav.number}
      wide
      title={MATRIX_TEXT.TITLE(index, decisionMakers.length, dm.name)}
      help={MATRIX_TEXT.HELP(scales.diagonal_label)}
      onNext={nav.onAdvance}
      onBack={nav.onBack}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <RatingLegend label={MATRIX_TEXT.LEGEND} ratings={scales.ratings} />
          <MatrixProgress dmId={dm.id} />
        </div>
        <MatrixGrid
          dmId={dm.id}
          ratings={ratings}
          diagonalLabel={scales.diagonal_label}
        />
      </div>
    </StepFrame>
  );
}
