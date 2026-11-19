import { ArrowLeftIcon } from "lucide-react";
import { SectionCard } from "@/components/general/SectionCard";
import { ExportBar } from "@/components/page-specific/assessment/ExportBar";
import { OutdatedResultsBanner } from "@/components/page-specific/assessment/OutdatedResultsBanner";
import { ResultTabs } from "@/components/page-specific/assessment/ResultTabs";
import { StartOverButton } from "@/components/page-specific/assessment/StartOverButton";
import { Button } from "@/components/ui/button";
import { FLOW_TEXT } from "@/constants/flow.constants";
import { RESULTS_TEXT } from "@/constants/results.constants";
import { useScales } from "@/hooks/scales.hook";
import type { StepId } from "@/interfaces/project.interface";
import { useProjectStore } from "@/store/project.store";

/** Full-width Results for the stored snapshot; "Back to inputs" opens Review, "Start over" clears everything. */
export function ResultsCard({
  onBack,
  onOpen,
}: {
  onBack: () => void;
  onOpen: (step: StepId) => void;
}) {
  const scales = useScales().data;
  const snapshot = useProjectStore((state) => state.snapshot);
  const snapshotHash = useProjectStore((state) => state.snapshotHash);
  const data = useProjectStore((state) => state.results);
  if (!snapshot || !data || !scales) return null;
  const { aggregation } = data;

  return (
    <div className="flex w-full flex-col gap-4 pt-6 pb-8 duration-200 animate-in fade-in slide-in-from-bottom-3 motion-reduce:animate-none">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          type="button"
          variant="outline"
          className="max-sm:h-11"
          onClick={onBack}
        >
          <ArrowLeftIcon data-icon="inline-start" />
          {FLOW_TEXT.BACK_TO_INPUTS}
        </Button>
        <StartOverButton />
      </div>
      <SectionCard
        title={RESULTS_TEXT.TITLE}
        subtitle={
          <span className="whitespace-pre-wrap">
            {RESULTS_TEXT.SUBTITLE(
              data.project_name,
              aggregation.method_label,
              aggregation.decision_maker_count,
            )}
          </span>
        }
      >
        <div className="flex flex-col gap-4">
          {aggregation.method_forced && (
            <p className="rounded-lg border bg-muted px-4 py-3 text-sm">
              {RESULTS_TEXT.FORCED_NOTE(
                scales.rules.method_choice_min_decision_makers,
                aggregation.method_label,
              )}
            </p>
          )}
          <OutdatedResultsBanner onOpen={onOpen} />
          <ExportBar
            key={`export-${snapshotHash}`}
            snapshot={snapshot}
            snapshotHash={snapshotHash}
            data={data}
            scales={scales}
          />
          <ResultTabs
            key={`tabs-${snapshotHash}`}
            snapshot={snapshot}
            snapshotHash={snapshotHash}
            data={data}
            scales={scales}
          />
        </div>
      </SectionCard>
    </div>
  );
}
