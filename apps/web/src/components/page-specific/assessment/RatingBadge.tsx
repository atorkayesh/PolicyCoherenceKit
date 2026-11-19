import { RATING_TOKENS, tokenFor } from "@/constants/theme.constants";
import { cn } from "@/lib/utils";

/** A rating label in its theme colours (AA contrast). */
export function RatingBadge({
  label,
  className,
}: {
  label: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        tokenFor(RATING_TOKENS, label),
        className,
      )}
    >
      {label}
    </span>
  );
}
