import { type KeyboardEvent, memo } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MATRIX_TEXT } from "@/constants/steps.constants";
import { RATING_TOKENS, tokenFor } from "@/constants/theme.constants";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/store/project.store";

/** Item value that clears the cell (never a rating label). */
const CLEAR_VALUE = "__clear__";

/**
 * One rating as a themed shadcn select. It subscribes to its own cell only, so changing a cell
 * re-renders that cell and not the grid. Blank shows `--`; `Clear rating`, Delete or Backspace
 * empties it; the diagonal is fixed.
 */
export const MatrixCell = memo(function MatrixCell({
  dmId,
  row,
  col,
  label,
  ratings,
  diagonalLabel,
  autoFocus = false,
}: {
  dmId: string;
  row: number;
  col: number;
  /** Accessible name: `{code} {policy} → {code} {policy}`. */
  label: string;
  ratings: readonly string[];
  diagonalLabel: string;
  /** The step's initial focus (see StepFrame). */
  autoFocus?: boolean;
}) {
  const value = useProjectStore(
    (state) => state.matrices[dmId]?.[row]?.[col] ?? "",
  );
  const setCell = useProjectStore((state) => state.setCell);
  const diagonal = row === col;

  const clearOnDelete = (event: KeyboardEvent<HTMLButtonElement>) => {
    if ((event.key === "Delete" || event.key === "Backspace") && value) {
      event.preventDefault();
      setCell(dmId, row, col, "");
    }
  };

  return (
    <Select
      value={diagonal ? diagonalLabel : value || null}
      disabled={diagonal}
      onValueChange={(next) => {
        if (typeof next !== "string") return;
        setCell(dmId, row, col, next === CLEAR_VALUE ? "" : next);
      }}
    >
      <SelectTrigger
        aria-label={label}
        data-autofocus={autoFocus || undefined}
        onKeyDown={clearOnDelete}
        className={cn(
          "h-full w-full rounded-md px-1.5 text-base sm:text-sm disabled:bg-muted disabled:text-muted-foreground disabled:opacity-100",
          diagonal
            ? "bg-muted"
            : value
              ? cn(
                  tokenFor(RATING_TOKENS, value),
                  "border-transparent font-medium",
                )
              : "bg-card",
        )}
      >
        <SelectValue
          className="truncate"
          placeholder={
            <span className="text-muted-foreground">{MATRIX_TEXT.BLANK}</span>
          }
        />
      </SelectTrigger>
      <SelectContent alignItemWithTrigger={false} className="min-w-44">
        {(ratings.includes(diagonalLabel)
          ? ratings
          : [diagonalLabel, ...ratings]
        ).map((rating) => (
          <SelectItem
            key={rating}
            value={rating}
            className="text-base sm:text-sm"
          >
            {rating}
          </SelectItem>
        ))}
        {value && !diagonal && (
          <SelectItem
            value={CLEAR_VALUE}
            className="border-t text-base text-muted-foreground sm:text-sm"
          >
            {MATRIX_TEXT.CLEAR}
          </SelectItem>
        )}
      </SelectContent>
    </Select>
  );
});
