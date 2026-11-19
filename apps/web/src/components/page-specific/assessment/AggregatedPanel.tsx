import { AggregatedGrid } from "@/components/page-specific/assessment/AggregatedGrid";
import { RatingLegend } from "@/components/page-specific/assessment/RatingLegend";
import { AGGREGATED_TEXT, TAB_LABELS } from "@/constants/results.constants";
import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { ScalesData } from "@/interfaces/scales.interface";

/** Aggregated: the score scale legend and the aggregated matrix. */
export function AggregatedPanel({
  data,
  scales,
}: {
  data: AnalysisData;
  scales: ScalesData;
}) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-semibold">{TAB_LABELS.AGGREGATED}</h3>
      <RatingLegend label={AGGREGATED_TEXT.LEGEND} ratings={scales.ratings} />
      <AggregatedGrid aggregation={data.aggregation} />
    </div>
  );
}
