export const FLOW_TEXT = {
  BACK: "Back",
  NEXT: "OK",
  RUN: "Run Analysis",
  BACK_TO_INPUTS: "Back to inputs",
  EDIT: "Edit",
  STEPS_LABEL: "Steps",
  PROGRESS_LABEL: "Progress",
  KEYBOARD_HINT: "press Enter ↵",
  LOADING: "Loading the assessment options…",
  LOAD_FAILED: "The assessment options could not be loaded from the API.",
  RETRY: "Try again",
  CHECKING: "Checking the matrices…",
} as const;

/** Confirmation when a change would discard ratings (plan Flow section). */
export const RESET_CONFIRM_TEXT = {
  TITLE: "Discard ratings?",
  DECISION_MAKERS:
    "The removed decision-makers have ratings that will be lost. Continue?",
  POLICIES: "The removed policies have ratings that will be lost. Continue?",
  CONFIRM: "Continue",
  CANCEL: "Cancel",
} as const;

/** "Start over": clears every answer, matrix and result and returns to the first step. */
export const START_OVER_TEXT = {
  BUTTON: "Start over",
  TITLE: "Start over?",
  DESCRIPTION: "All answers, matrices and results will be cleared.",
  CONFIRM: "Start over",
  CANCEL: "Cancel",
} as const;

/** One-time toast on reaching the decision-makers step: answers live only in this page. */
export const REFRESH_NOTICE = {
  STEP: "decision-makers",
  STORAGE_KEY: "policycoherencekit:refresh-notice-shown",
  TITLE: "Heads up: your answers aren't saved",
  DESCRIPTION:
    "Refreshing or closing this page starts the assessment over. Use the Back button to change earlier answers.",
  DURATION_MS: 8000,
} as const;
