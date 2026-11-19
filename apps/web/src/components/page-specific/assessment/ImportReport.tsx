import type { ReactNode } from "react";
import { IMPORT_ERROR_TITLES, IMPORT_TEXT } from "@/constants/import.constants";
import {
  nothingImportedDataSchema,
  type WarningGroup,
} from "@/interfaces/import.interface";
import type { StepError } from "@/interfaces/project.interface";
import { ApiError, errorCode, errorMessage } from "@/utils/api.utils";

/** Grouped import warnings: each heading with its messages (verbatim). */
export function WarningGroups({ groups }: { groups: readonly WarningGroup[] }) {
  if (groups.length === 0) return null;
  return (
    <div className="flex flex-col gap-3">
      {groups.map((group) => (
        <div key={group.kind} className="flex flex-col gap-1">
          <p className="font-medium">{group.heading}</p>
          <ul className="flex flex-col gap-0.5 text-sm whitespace-pre-line">
            {group.messages.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

/** The last import's summary and its warnings. */
export function ImportReport({
  summary,
  groups,
}: {
  summary: string;
  groups: readonly WarningGroup[];
}) {
  return (
    <output className="flex flex-col gap-3 rounded-lg border bg-card px-4 py-3 text-sm text-foreground">
      <p className="font-medium whitespace-pre-line">{summary}</p>
      <WarningGroups groups={groups} />
    </output>
  );
}

/** An import failure as a step error: legacy title by code, the API's message and warnings. */
export function importError(error: unknown): StepError {
  const code = errorCode(error);
  let action: ReactNode = null;
  if (code === "nothing_imported" && error instanceof ApiError) {
    const parsed = nothingImportedDataSchema.safeParse(error.data);
    if (parsed.success) {
      action = (
        <div className="pt-1 text-foreground">
          <WarningGroups groups={parsed.data.warning_groups} />
        </div>
      );
    }
  }
  return {
    title: (code && IMPORT_ERROR_TITLES[code]) || IMPORT_TEXT.ERROR_TITLE,
    message: errorMessage(error),
    action,
  };
}
