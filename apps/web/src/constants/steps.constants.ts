import type { FixedStepId } from "@/interfaces/project.interface";

/** Question, short label (step list) and helper text of each fixed step (plan Flow section). */
export const STEP_TEXT: Record<
  FixedStepId,
  { title: string; label: string; help?: string }
> = {
  project: {
    title: "What is this project called?",
    label: "Project",
    // app.py:1180-1182
    help: "Create a project to define policies, add decision-makers, and evaluate interactions across expert perspectives. The tool supports structured matrix input, aggregation methods, and advanced analytical outputs.",
  },
  "decision-makers": {
    title: "Who are the decision-makers?",
    label: "Decision-makers",
    help: "Add one or more decision-maker names.",
  },
  policies: {
    title: "Which policies are you assessing?",
    label: "Policies",
    help: "Add at least 2 policy names. Each policy gets a code (P1, P2, …) that the matrices use.",
  },
  import: {
    title: "Do you want to import ratings from Excel?",
    label: "Import",
    help: "This step is optional: press OK to rate the interactions here instead.",
  },
  review: {
    title: "Review your answers",
    label: "Review",
    help: "Check your answers, then choose how to combine the ratings. Every cell must be rated.",
  },
  method: { title: "How should the ratings be combined?", label: "Method" },
  weights: {
    title: "How much weight does each decision-maker carry?",
    label: "Weights",
  },
  median: { title: "Lower or upper median?", label: "Median" },
  ties: { title: "Resolve majority ties", label: "Ties" },
  results: { title: "Results", label: "Results" },
};

/** Step `project` (app.py:1170; dialogs.py:842; theme.py:109-112). */
export const PROJECT_TEXT = {
  EYEBROW: "Start a new policy coherence assessment",
  LABEL: "Project Name",
  HINT: "Use a clear descriptive title for this project.",
  PLACEHOLDER: "e.g. EU Clean Mobility Policy Coherence Assessment",
} as const;

/** Name list steps (dialogs.py:503-514, 862-875; theme.py:89). */
export const NAME_LIST_TEXT = {
  DECISION_MAKERS_LABEL: "Add decision-maker names",
  POLICIES_LABEL: "Add policy names",
  ADD: "Add",
  REMOVE_ROW: (index: number) => `Remove row ${index}`,
  ROW_LABEL: (label: string, index: number) => `${label} ${index}`,
  DECISION_MAKER_PLACEHOLDER: (index: number) =>
    `e.g. Expert ${spreadsheetLetters(index)}`,
  POLICY_PLACEHOLDER: (index: number) => `e.g. Policy ${index + 1}`,
  /** The legacy dialog starts with two empty rows. */
  INITIAL_ROWS: 2,
  /** Rows 1 and 2 have no remove button (legacy). */
  FIXED_ROWS: 2,
} as const;

/** A, B, …, Z, AA, AB, … for 0-based `index` (dialogs.py:862-872). */
export function spreadsheetLetters(index: number): string {
  let n = index + 1;
  let letters = "";
  while (n > 0) {
    const rest = (n - 1) % 26;
    letters = String.fromCharCode(65 + rest) + letters;
    n = Math.floor((n - 1) / 26);
  }
  return letters;
}

/** Matrix steps. */
export const MATRIX_TEXT = {
  TITLE: (index: number, count: number, name: string) =>
    `Decision-maker ${index + 1} of ${count}: ${name}`,
  HELP: (diagonalLabel: string) =>
    `How does each policy (row) influence each policy (column)? Each row is an influencing policy and each column an influenced policy; diagonal cells are fixed to ${diagonalLabel}.`,
  LABEL: (index: number) => `Matrix ${index + 1}`,
  LEGEND: "Click a cell to rate it:",
  PROGRESS: (filled: number, total: number) =>
    `${filled}/${total} cells filled`,
  CORNER: "Row → Column",
  BLANK: "--",
  CLEAR: "Clear rating",
  HEADER_TITLE: (code: string, policy: string) => `${code}:  ${policy}`,
  CELL_LABEL: (
    codeRow: string,
    policyRow: string,
    codeCol: string,
    policyCol: string,
  ) => `${codeRow} ${policyRow} → ${codeCol} ${policyCol}`,
} as const;

/** Matrix grid sizes in pixels (the virtualiser needs fixed sizes). */
export const MATRIX_GRID = {
  ROW_HEIGHT: 40,
  HEADER_HEIGHT: 40,
  CELL_WIDTH: 152,
  OVERSCAN: 4,
  /** Initial viewport before layout (also used in tests, where there is no layout). */
  INITIAL_RECT: { width: 1000, height: 480 },
} as const;
