import { memo, useId } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TIES_TEXT } from "@/constants/aggregation.constants";
import type { Tie } from "@/interfaces/aggregation.interface";
import { useProjectStore } from "@/store/project.store";
import { formatSigned } from "@/utils/format.utils";

/** `Tied options: Enabling (+1)  |  Neutral (+0)` (aggregation_dialog.py:722-729). */
export function tiedOptionsText(tie: Tie): string {
  return (
    TIES_TEXT.OPTIONS_PREFIX +
    tie.tied_options
      .map((option) => `${option.label} (${formatSigned(option.score, 0)})`)
      .join(TIES_TEXT.OPTIONS_SEPARATOR)
  );
}

/** One tied cell: the pair, the tied options, each decision-maker's vote and the choice. */
export const TieCard = memo(function TieCard({
  tie,
  choiceKey,
}: {
  tie: Tie;
  /** Store key of the choice: the row and column policy ids. */
  choiceKey: string;
}) {
  const chosen = useProjectStore((state) => state.tieChoices[choiceKey] ?? "");
  const setTieChoice = useProjectStore((state) => state.setTieChoice);
  const selectId = useId();
  const valid = tie.tied_options.some((option) => option.label === chosen);

  return (
    <div className="flex flex-col gap-2 rounded-lg border bg-card px-4 py-3">
      <div>
        <p className="font-semibold">
          {TIES_TEXT.HEADING(tie.code_row, tie.code_col)}
        </p>
        <p className="text-sm text-muted-foreground">
          {TIES_TEXT.POLICIES(tie.policy_row, tie.policy_col)}
        </p>
      </div>
      <p className="text-sm whitespace-pre">{tiedOptionsText(tie)}</p>
      <div className="text-sm">
        <span className="text-muted-foreground">{TIES_TEXT.VOTES}</span>{" "}
        {tie.votes
          .map((vote) => TIES_TEXT.VOTE(vote.decision_maker, vote.rating))
          .join(", ")}
      </div>
      <div className="flex flex-col gap-1 text-sm sm:max-w-xs">
        <span id={selectId}>{TIES_TEXT.SELECT_LABEL}</span>
        <Select
          value={valid ? chosen : null}
          onValueChange={(next) => {
            if (typeof next === "string") setTieChoice(choiceKey, next);
          }}
        >
          <SelectTrigger
            aria-labelledby={selectId}
            className="h-9 w-full bg-card max-sm:h-11"
          >
            <SelectValue placeholder={TIES_TEXT.PLACEHOLDER} />
          </SelectTrigger>
          <SelectContent alignItemWithTrigger={false}>
            {tie.tied_options.map((option) => (
              <SelectItem key={option.label} value={option.label}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
});
