import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";
import { runError } from "@/components/page-specific/assessment/RunError";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { TieCard } from "@/components/page-specific/assessment/TieCard";
import { TIES_TEXT } from "@/constants/aggregation.constants";
import { FLOW_TEXT } from "@/constants/flow.constants";
import { MATRIX_GRID, STEP_TEXT } from "@/constants/steps.constants";
import { useAggregationPreview } from "@/hooks/aggregation.hook";
import { useRunFromStep } from "@/hooks/analysis.hook";
import type { Tie } from "@/interfaces/aggregation.interface";
import type { StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";
import { tieKey } from "@/utils/analysis-request.utils";
import { stepError } from "@/utils/api.utils";

/** Many ties: a virtualised list, so hundreds of cards stay responsive. */
function VirtualTieList({ ties, keys }: { ties: Tie[]; keys: string[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const list = useVirtualizer({
    count: ties.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => TIES_TEXT.CARD_HEIGHT,
    overscan: 4,
    initialRect: MATRIX_GRID.INITIAL_RECT,
  });
  return (
    <div ref={scrollRef} className="max-h-[60vh] overflow-auto">
      <div className="relative w-full" style={{ height: list.getTotalSize() }}>
        {list.getVirtualItems().map((item) => (
          <div
            key={item.key}
            ref={list.measureElement}
            data-index={item.index}
            className="absolute left-0 w-full pb-3"
            style={{ top: item.start }}
          >
            <TieCard tie={ties[item.index]} choiceKey={keys[item.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Majority ties: choose a rating for every tied cell, then run. */
export function TiesStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const preview = useAggregationPreview();
  const policies = useProjectStore((state) => state.policies);
  const { run, start } = useRunFromStep(scales.rules);
  const ties = preview.data?.ties ?? [];
  const keys = ties.map((tie) =>
    tieKey(policies[tie.row]?.id, policies[tie.col]?.id),
  );

  const submit = () => {
    run.reset();
    start("ties", () => nav.onOpen("results"));
  };

  return (
    <StepFrame
      number={nav.number}
      wide
      title={STEP_TEXT.ties.title}
      help={preview.data ? TIES_TEXT.HELP(ties.length) : FLOW_TEXT.CHECKING}
      error={
        run.error
          ? runError(run.error, nav.onOpen)
          : preview.error
            ? stepError(preview.error)
            : null
      }
      pending={preview.isPending || run.isPending}
      nextLabel={FLOW_TEXT.RUN}
      onNext={submit}
      onBack={nav.onBack}
    >
      {preview.data && ties.length === 0 && (
        <p className="text-muted-foreground">{TIES_TEXT.NONE}</p>
      )}
      {ties.length > TIES_TEXT.VIRTUALISE_ABOVE ? (
        <VirtualTieList ties={ties} keys={keys} />
      ) : (
        <div className="flex flex-col gap-3">
          {ties.map((tie, i) => (
            <TieCard key={keys[i]} tie={tie} choiceKey={keys[i]} />
          ))}
        </div>
      )}
    </StepFrame>
  );
}
