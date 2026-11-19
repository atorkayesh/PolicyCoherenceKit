import { useState } from "react";
import {
  initialRows,
  NameListEditor,
} from "@/components/page-specific/assessment/NameListEditor";
import { ResetConfirmDialog } from "@/components/page-specific/assessment/ResetConfirmDialog";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { RESET_CONFIRM_TEXT } from "@/constants/flow.constants";
import { NAME_LIST_TEXT, STEP_TEXT } from "@/constants/steps.constants";
import { useValidateSetup } from "@/hooks/setup.hook";
import type {
  NamedItem,
  StepError,
  StepProps,
} from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";
import { stepError } from "@/utils/api.utils";
import {
  decisionMakerRemovalLosesRatings,
  filledRows,
  itemsFromDraft,
} from "@/utils/project-state.utils";

/** Step 2: decision-maker names (a draft until OK); removing rated ones asks first. */
export function DecisionMakersStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const committed = useProjectStore((state) => state.decisionMakers);
  const commit = useProjectStore((state) => state.commitDecisionMakers);
  const [rows, setRows] = useState(() => initialRows(committed));
  const [error, setError] = useState<StepError | null>(null);
  const [confirming, setConfirming] = useState<NamedItem[] | null>(null);
  const validate = useValidateSetup();

  const apply = (items: NamedItem[]) => {
    setConfirming(null);
    commit(items, scales.diagonal_label);
    nav.onAdvance();
  };

  const submit = () => {
    setError(null);
    const names = filledRows(rows).map((row) => row.name);
    validate.mutate(
      { decision_makers: names },
      {
        onSuccess: (data) => {
          const items = itemsFromDraft(rows, data.decision_makers ?? names);
          const state = useProjectStore.getState();
          if (decisionMakerRemovalLosesRatings(state, rows))
            setConfirming(items);
          else apply(items);
        },
        onError: (failure) => setError(stepError(failure)),
      },
    );
  };

  return (
    <StepFrame
      number={nav.number}
      title={STEP_TEXT["decision-makers"].title}
      help={STEP_TEXT["decision-makers"].help}
      error={error}
      pending={validate.isPending}
      onNext={submit}
      onBack={nav.onBack}
    >
      <NameListEditor
        label={NAME_LIST_TEXT.DECISION_MAKERS_LABEL}
        rows={rows}
        max={scales.rules.max_decision_makers}
        placeholder={NAME_LIST_TEXT.DECISION_MAKER_PLACEHOLDER}
        onChange={setRows}
      />
      <ResetConfirmDialog
        open={confirming !== null}
        paragraphs={[RESET_CONFIRM_TEXT.DECISION_MAKERS]}
        onConfirm={() => confirming && apply(confirming)}
        onCancel={() => setConfirming(null)}
      />
    </StepFrame>
  );
}
