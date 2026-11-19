import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";

export const warningGroupSchema = z.object({
  kind: z.string(),
  heading: z.string(),
  messages: z.array(z.string()),
});

export type WarningGroup = z.infer<typeof warningGroupSchema>;

/** `POST /imports/workbook`: one matrix per sheet, plus the grouped warnings. */
export const importDataSchema = z.object({
  policies: z.array(z.string()),
  codes: z.array(z.string()),
  matrices: z.array(
    z.object({
      decision_maker: z.string(),
      ratings: z.array(z.array(z.string())),
    }),
  ),
  warning_groups: z.array(warningGroupSchema),
  imported_count: z.number(),
  summary_message: z.string(),
  suggested_project_name: z.string().nullish(),
});

export const importResponseSchema = apiResponseSchema(importDataSchema);

export type ImportData = z.infer<typeof importDataSchema>;

/** The import report the `import` step shows (the last successful import). */
export interface ImportReport {
  summaryMessage: string;
  warningGroups: WarningGroup[];
}

/** `data` of a `nothing_imported` error. */
export const nothingImportedDataSchema = z.object({
  warning_groups: z.array(warningGroupSchema).default([]),
});
