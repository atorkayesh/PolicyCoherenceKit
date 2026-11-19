import { RefreshCwIcon } from "lucide-react";
import { InlineError } from "@/components/general/InlineError";
import { Button } from "@/components/ui/button";
import { RESULTS_TEXT } from "@/constants/results.constants";
import { useResultsOutdated } from "@/hooks/analysis.hook";
import { useRerun } from "@/hooks/rerun.hook";
import type { StepId } from "@/interfaces/project.interface";
import { errorMessage, errorTitle } from "@/utils/api.utils";

/** Shown when the answers changed after the run; "Re-run" analyses the current answers. */
export function OutdatedResultsBanner({
  onOpen,
}: {
  onOpen: (step: StepId) => void;
}) {
  const outdated = useResultsOutdated();
  const rerun = useRerun(onOpen);
  if (!outdated) return null;

  return (
    <output className="flex flex-col gap-2 rounded-lg border border-line-strong bg-muted px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-medium">{RESULTS_TEXT.OUTDATED}</p>
        <Button
          type="button"
          size="sm"
          onClick={() => rerun.mutate()}
          disabled={rerun.isPending}
        >
          <RefreshCwIcon
            data-icon="inline-start"
            className={rerun.isPending ? "animate-spin" : undefined}
          />
          {RESULTS_TEXT.RERUN}
        </Button>
      </div>
      <InlineError
        title={rerun.error ? errorTitle(rerun.error) : null}
        message={rerun.error ? errorMessage(rerun.error) : null}
      />
    </output>
  );
}
