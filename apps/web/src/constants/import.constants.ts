/** Excel import texts (theme.py:101; app.py:2919-3035; plan Flow steps 1 and 4). */
export const IMPORT_TEXT = {
  BUTTON: "Import from Excel",
  START_LINE:
    "Or start from an Excel workbook: one sheet per decision-maker, with the policy names in row 1 and column 1.",
  FORMAT:
    "The workbook needs one sheet per decision-maker. Row 1 and column 1 hold your policy names in the same order, and the cells hold rating labels. Sheets named like one of your decision-makers fill that decision-maker's matrix; other sheets are added as new decision-makers.",
  ERROR_TITLE: "Import Error",
  COMPLETE: "Import Complete",
  COMPLETE_WITH_WARNINGS: "Import Complete with Warnings",
  /** The API's limit text, with the number from `/scales`. */
  TOO_MANY_DECISION_MAKERS: (max: number) =>
    `Please enter at most ${max} decision-makers.`,
} as const;

/** Legacy message-box titles of import error codes. */
export const IMPORT_ERROR_TITLES: Record<string, string> = {
  policy_list_mismatch: "Policy List Mismatch",
  nothing_imported: "Nothing Imported",
};

/** Confirms before an import replaces answers. */
export const IMPORT_CONFIRM_TEXT = {
  REPLACE_ALL_TITLE: "Replace your answers?",
  REPLACE_ALL:
    "The workbook replaces the decision-makers, policies and ratings you entered.",
  REPLACE_ALL_CONFIRM: "Replace",
  REPLACE_RATINGS_TITLE: "Replace ratings?",
  REPLACE_RATINGS: (names: string) =>
    `The workbook has ratings for ${names}, who already have ratings here. They will be replaced.`,
  REPLACE_RATINGS_CONFIRM: "Replace",
  CANCEL: "Cancel",
} as const;
