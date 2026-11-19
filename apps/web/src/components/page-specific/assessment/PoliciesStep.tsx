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
  filledRows,
  itemsFromDraft,
  policyRemovalLosesRatings,
} from "@/utils/project-state.utils";

/** Step 3: policy names (a draft until OK); removing rated ones asks first; codes come from the API. */
export function PoliciesStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const committed = useProjectStore((state) => state.policies);
  const commit = useProjectStore((state) => state.commitPolicies);
  const [rows, setRows] = useState(() => initialRows(committed));
  const [error, setError] = useState<StepError | null>(null);
  const [confirming, setConfirming] = useState<{
    items: NamedItem[];
    codes: string[];
  } | null>(null);
  const validate = useValidateSetup();

  const apply = ({ items, codes }: { items: NamedItem[]; codes: string[] }) => {
    setConfirming(null);
    commit(items, codes, scales.diagonal_label);
    nav.onAdvance();
  };

  const submit = () => {
    setError(null);
    const names = filledRows(rows).map((row) => row.name);
    validate.mutate(
      { policies: names },
      {
        onSuccess: (data) => {
          const items = itemsFromDraft(rows, data.policies ?? names);
          const change = { items, codes: data.codes ?? [] };
          const state = useProjectStore.getState();
          if (policyRemovalLosesRatings(state, rows)) setConfirming(change);
          else apply(change);
        },
        onError: (failure) => setError(stepError(failure)),
      },
    );
  };

  return (
    <StepFrame
      number={nav.number}
      title={STEP_TEXT.policies.title}
      help={STEP_TEXT.policies.help}
      error={error}
      pending={validate.isPending}
      onNext={submit}
      onBack={nav.onBack}
    >
      <NameListEditor
        label={NAME_LIST_TEXT.POLICIES_LABEL}
        rows={rows}
        max={scales.rules.max_policies}
        placeholder={NAME_LIST_TEXT.POLICY_PLACEHOLDER}
        onChange={setRows}
      />
      <ResetConfirmDialog
        open={confirming !== null}
        paragraphs={[RESET_CONFIRM_TEXT.POLICIES]}
        onConfirm={() => confirming && apply(confirming)}
        onCancel={() => setConfirming(null)}
      />
    </StepFrame>
  );
}
