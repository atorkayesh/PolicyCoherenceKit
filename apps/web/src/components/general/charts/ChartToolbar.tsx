import { RotateCcwIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { CHART_TEXT } from "@/constants/chart.constants";

/** Controls above a chart (selects, checkboxes) and the Reset view button at the far end. */
export function ChartToolbar({
  children,
  onResetView,
}: {
  children?: ReactNode;
  onResetView: () => void;
}) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      {children}
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="ml-auto max-sm:h-10"
        onClick={onResetView}
      >
        <RotateCcwIcon data-icon="inline-start" />
        {CHART_TEXT.RESET_VIEW}
      </Button>
    </div>
  );
}
