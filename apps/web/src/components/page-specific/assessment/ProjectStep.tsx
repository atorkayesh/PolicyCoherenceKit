import { useId, useState } from "react";
import { StepFrame } from "@/components/page-specific/assessment/StepFrame";
import { WorkbookStartAction } from "@/components/page-specific/assessment/WorkbookStartAction";
import { Input } from "@/components/ui/input";
import { PROJECT_TEXT, STEP_TEXT } from "@/constants/steps.constants";
import { useValidateSetup } from "@/hooks/setup.hook";
import type { StepError, StepProps } from "@/interfaces/project.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";
import { stepError } from "@/utils/api.utils";

/** Step 1: the project name (a draft until OK, validated by `/setup/validate`), or start from Excel. */
export function ProjectStep({
  scales,
  ...nav
}: StepProps & { scales: ScalesData }) {
  const committed = useProjectStore((state) => state.projectName);
  const setProjectName = useProjectStore((state) => state.setProjectName);
  const [draft, setDraft] = useState(committed);
  const [error, setError] = useState<StepError | null>(null);
  const validate = useValidateSetup();
  const inputId = useId();
  const hintId = useId();

  const submit = () => {
    setError(null);
    validate.mutate(
      { project_name: draft },
      {
        onSuccess: (data) => {
          setProjectName(data.project_name ?? draft.trim());
          nav.onAdvance();
        },
        onError: (failure) => setError(stepError(failure)),
      },
    );
  };

  return (
    <StepFrame
      number={nav.number}
      eyebrow={PROJECT_TEXT.EYEBROW}
      title={STEP_TEXT.project.title}
      help={STEP_TEXT.project.help}
      error={error}
      pending={validate.isPending}
      onNext={submit}
      onBack={nav.onBack}
    >
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={inputId} className="text-sm font-medium">
            {PROJECT_TEXT.LABEL}
          </label>
          <Input
            id={inputId}
            value={draft}
            placeholder={PROJECT_TEXT.PLACEHOLDER}
            aria-describedby={hintId}
            onChange={(event) => setDraft(event.target.value)}
            className="h-11 text-base"
          />
          <p id={hintId} className="text-xs text-muted-foreground">
            {PROJECT_TEXT.HINT}
          </p>
        </div>
        <WorkbookStartAction
          scales={scales}
          draftName={draft}
          onError={setError}
        />
      </div>
    </StepFrame>
  );
}
