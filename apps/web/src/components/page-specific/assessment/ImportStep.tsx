import { useState } from "react";
import { toast } from "sonner";
import {
  ImportReport,
  importError,
} from "@/components/page-specific/assessment/ImportReport";
import { ResetConfirmDialog } from "@/components/page-specific/assessment/ResetConfirmDialog";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { WorkbookPicker } from "@/components/page-specific/assessment/WorkbookPicker";
import { IMPORT_CONFIRM_TEXT, IMPORT_TEXT } from "@/constants/import.constants";
import { STEP_TEXT } from "@/constants/steps.constants";
import { useImportWorkbook } from "@/hooks/import.hook";
import type { ImportData } from "@/interfaces/import.interface";
import type { StepError, StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";
import {
  answeredSteps,
  firstUnansweredAfter,
  questionSteps,
} from "@/utils/flow.utils";
import {
  countAfterMerge,
  mergeReplacesRatings,
} from "@/utils/project-state.utils";

/**
 * Step 4 (optional): import ratings into the project (legacy app.py:2919-2998). The policy list must
 * match; same-name sheets fill that decision-maker's matrix, other sheets are added. OK skips to
 * the first unanswered step, so imported matrices are skipped.
 */
export function ImportStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const report = useProjectStore((state) => state.importReport);
  const applyWorkbook = useProjectStore((state) => state.applyWorkbook);
  const markAnswered = useProjectStore((state) => state.markAnswered);
  const upload = useImportWorkbook();
  const [error, setError] = useState<StepError | null>(null);
  const [pending, setPending] = useState<{
    data: ImportData;
    names: string[];
  } | null>(null);

  const apply = (data: ImportData) => {
    setPending(null);
    applyWorkbook("merge", data, scales.diagonal_label);
    const warned = data.warning_groups.length > 0;
    toast.success(
      warned ? IMPORT_TEXT.COMPLETE_WITH_WARNINGS : IMPORT_TEXT.COMPLETE,
      {
        description: data.summary_message,
      },
    );
  };

  const onFile = (file: File) => {
    setError(null);
    const policies = useProjectStore.getState().policies.map((p) => p.name);
    upload.mutate(
      { file, policies },
      {
        onSuccess: (data) => {
          const state = useProjectStore.getState();
          const max = scales.rules.max_decision_makers;
          if (countAfterMerge(state.decisionMakers, data) > max) {
            setError({
              title: IMPORT_TEXT.ERROR_TITLE,
              message: IMPORT_TEXT.TOO_MANY_DECISION_MAKERS(max),
            });
            return;
          }
          const names = mergeReplacesRatings(state, data);
          if (names.length > 0) setPending({ data, names });
          else apply(data);
        },
        onError: (failure) => setError(importError(failure)),
      },
    );
  };

  const next = () => {
    markAnswered("import");
    const state = useProjectStore.getState();
    const steps = questionSteps(state);
    const answered = answeredSteps(
      state.answered,
      state.decisionMakers,
      state.answeredMatrices,
    );
    nav.onOpen(firstUnansweredAfter("import", steps, answered));
  };

  return (
    <StepFrame
      number={nav.number}
      title={STEP_TEXT.import.title}
      help={
        <>
          <p>{STEP_TEXT.import.help}</p>
          <p className="text-sm">{IMPORT_TEXT.FORMAT}</p>
        </>
      }
      error={error}
      pending={upload.isPending}
      focusNext
      onNext={next}
      onBack={nav.onBack}
    >
      <div className="flex flex-col gap-4">
        <div>
          <WorkbookPicker
            accept={scales.imports.accept}
            pending={upload.isPending}
            onFile={onFile}
          />
        </div>
        {report && (
          <ImportReport
            summary={report.summaryMessage}
            groups={report.warningGroups}
          />
        )}
      </div>
      <ResetConfirmDialog
        open={pending !== null}
        title={IMPORT_CONFIRM_TEXT.REPLACE_RATINGS_TITLE}
        paragraphs={[
          IMPORT_CONFIRM_TEXT.REPLACE_RATINGS(pending?.names.join(", ") ?? ""),
        ]}
        confirmLabel={IMPORT_CONFIRM_TEXT.REPLACE_RATINGS_CONFIRM}
        cancelLabel={IMPORT_CONFIRM_TEXT.CANCEL}
        onConfirm={() => pending && apply(pending.data)}
        onCancel={() => setPending(null)}
      />
    </StepFrame>
  );
}
