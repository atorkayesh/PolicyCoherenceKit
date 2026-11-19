import { useState } from "react";
import { ReviewRow } from "@/components/page-specific/assessment/ReviewRow";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { REVIEW_TEXT } from "@/constants/aggregation.constants";
import { FLOW_TEXT } from "@/constants/flow.constants";
import { STEP_TEXT } from "@/constants/steps.constants";
import { useMatrixCheck } from "@/hooks/matrix-check.hook";
import type { MatrixCheckData } from "@/interfaces/check.interface";
import type { StepError, StepProps } from "@/interfaces/project.interface";
import { useProjectStore } from "@/store/project.store";
import { stepError } from "@/utils/api.utils";
import { matrixStepId, namesKey } from "@/utils/flow.utils";

type DmCheck = MatrixCheckData["decision_makers"][number];

/** `{filled}/{total} cells filled`, then the blank count and the first blank cells. */
function matrixSummary(check: DmCheck | undefined): string {
  if (!check) return "";
  const lines = [`${check.filled}/${check.total} cells filled`];
  if (!check.complete) {
    const cells = check.blank_cells.map((c) => `${c.code_row} → ${c.code_col}`);
    const more = check.blank_count - check.blank_cells.length;
    const suffix = more > 0 ? ` ${REVIEW_TEXT.MORE(more)}` : "";
    lines.push(
      `${REVIEW_TEXT.BLANKS(check.blank_count)}: ${cells.join(", ")}${suffix}`,
    );
  }
  return lines.join("\n");
}

/** Every answer with an Edit link; OK checks completeness with the API before the method step. */
export function ReviewStep(nav: StepProps) {
  const state = useProjectStore();
  const check = useMatrixCheck();
  const [error, setError] = useState<StepError | null>(null);
  const [checking, setChecking] = useState(false);

  const submit = async () => {
    setError(null);
    setChecking(true);
    const result = await check.refetch();
    setChecking(false);
    if (result.error || !result.data) {
      setError(stepError(result.error));
      return;
    }
    if (!result.data.complete) {
      setError({
        title: REVIEW_TEXT.INCOMPLETE_TITLE,
        message: result.data.incomplete_message ?? "",
      });
      return;
    }
    state.setAggregationOptions({
      ...result.data.aggregation_options,
      forNames: namesKey(useProjectStore.getState().decisionMakers),
    });
    nav.onAdvance();
  };

  const codes = state.codes;
  return (
    <StepFrame
      number={nav.number}
      wide
      title={STEP_TEXT.review.title}
      help={STEP_TEXT.review.help}
      error={error}
      pending={checking}
      focusNext
      onNext={() => void submit()}
      onBack={nav.onBack}
    >
      <dl className="divide-y rounded-lg border bg-card px-4">
        <ReviewRow
          label={REVIEW_TEXT.PROJECT}
          onEdit={() => nav.onOpen("project")}
        >
          {state.projectName}
        </ReviewRow>
        <ReviewRow
          label={REVIEW_TEXT.DECISION_MAKERS}
          onEdit={() => nav.onOpen("decision-makers")}
        >
          {state.decisionMakers.map((dm) => dm.name).join(", ")}
        </ReviewRow>
        <ReviewRow
          label={REVIEW_TEXT.POLICIES}
          onEdit={() => nav.onOpen("policies")}
        >
          {state.policies.map((p, i) => `${codes[i]}: ${p.name}`).join(", ")}
        </ReviewRow>
        <ReviewRow
          label={REVIEW_TEXT.IMPORT}
          onEdit={() => nav.onOpen("import")}
        >
          {state.importReport?.summaryMessage ?? REVIEW_TEXT.RATED_HERE}
        </ReviewRow>
        {state.decisionMakers.map((dm, index) => (
          <ReviewRow
            key={dm.id}
            label={REVIEW_TEXT.MATRIX(dm.name)}
            onEdit={() => nav.onOpen(matrixStepId(index))}
          >
            <span className="whitespace-pre-line">
              {check.isPending
                ? FLOW_TEXT.CHECKING
                : matrixSummary(check.data?.decision_makers[index])}
            </span>
          </ReviewRow>
        ))}
      </dl>
    </StepFrame>
  );
}
