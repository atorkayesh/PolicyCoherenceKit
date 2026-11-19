import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { importError } from "@/components/page-specific/assessment/ImportReport";
import { ResetConfirmDialog } from "@/components/page-specific/assessment/ResetConfirmDialog";
import { WorkbookPicker } from "@/components/page-specific/assessment/WorkbookPicker";
import { IMPORT_CONFIRM_TEXT, IMPORT_TEXT } from "@/constants/import.constants";
import { useImportWorkbook } from "@/hooks/import.hook";
import type { ImportData } from "@/interfaces/import.interface";
import type { StepError } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";

/**
 * "Import from Excel" on the first step (legacy new project from import, app.py:3000-3035): the
 * workbook replaces decision-makers, policies and ratings, after a confirm if any exist. The typed
 * project name is kept; an empty one becomes the workbook's name. Opens the `import` step.
 */
export function WorkbookStartAction({
  scales,
  draftName,
  onError,
}: {
  scales: ScalesData;
  draftName: string;
  onError: (error: StepError | null) => void;
}) {
  const navigate = useNavigate({ from: "/" });
  const upload = useImportWorkbook();
  const applyWorkbook = useProjectStore((state) => state.applyWorkbook);
  const [pending, setPending] = useState<ImportData | null>(null);

  const apply = (data: ImportData) => {
    setPending(null);
    applyWorkbook("replace", data, scales.diagonal_label, draftName.trim());
    navigate({ search: { step: "import" } });
  };

  const onFile = (file: File) => {
    onError(null);
    upload.mutate(
      { file },
      {
        onSuccess: (data) => {
          const state = useProjectStore.getState();
          const hasAnswers =
            state.decisionMakers.length > 0 || state.policies.length > 0;
          if (hasAnswers) setPending(data);
          else apply(data);
        },
        onError: (error) => onError(importError(error)),
      },
    );
  };

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-dashed bg-card/60 px-4 py-3">
      <p className="text-sm text-muted-foreground">{IMPORT_TEXT.START_LINE}</p>
      <div>
        <WorkbookPicker
          accept={scales.imports.accept}
          pending={upload.isPending}
          onFile={onFile}
        />
      </div>
      <ResetConfirmDialog
        open={pending !== null}
        title={IMPORT_CONFIRM_TEXT.REPLACE_ALL_TITLE}
        paragraphs={[IMPORT_CONFIRM_TEXT.REPLACE_ALL]}
        confirmLabel={IMPORT_CONFIRM_TEXT.REPLACE_ALL_CONFIRM}
        cancelLabel={IMPORT_CONFIRM_TEXT.CANCEL}
        onConfirm={() => pending && apply(pending)}
        onCancel={() => setPending(null)}
      />
    </div>
  );
}
