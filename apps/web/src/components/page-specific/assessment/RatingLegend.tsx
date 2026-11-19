import { RatingBadge } from "@/components/page-specific/assessment/RatingBadge";
import type { ScalesData } from "@/interfaces/scales.interface";

/** A legend label and the seven rating badges in the API's order. */
export function RatingLegend({
  label,
  ratings,
}: {
  label: string;
  ratings: ScalesData["ratings"];
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="mr-1 text-sm text-muted-foreground">{label}</span>
      {ratings.map((rating) => (
        <RatingBadge key={rating.label} label={rating.label} />
      ))}
    </div>
  );
}
