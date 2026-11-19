import { decisionMakerWord } from "@/utils/format.utils";

/** Review step rows. */
export const REVIEW_TEXT = {
  PROJECT: "Project Name",
  DECISION_MAKERS: "Decision-makers",
  POLICIES: "Policies",
  IMPORT: "Import",
  RATED_HERE: "Rated in the browser",
  MATRIX: (name: string) => `Matrix: ${name}`,
  BLANKS: (count: number) => `${count} blank ${count === 1 ? "cell" : "cells"}`,
  MORE: (count: number) => `(+${count} more)`,
  INCOMPLETE_TITLE: "Incomplete Matrices",
} as const;

/** Method step (aggregation_dialog.py:119; plan fix for UI report item 12). */
export const METHOD_TEXT = {
  GROUP_LABEL: "Aggregation method",
  CHOICE_HELP: (n: number) =>
    `${n} decision-makers detected — choose how to combine their ratings.`,
  FORCED_HELP: (n: number) => `${n} ${decisionMakerWord(n)} detected.`,
  FORCED_NOTE: (min: number, label: string) =>
    `With fewer than ${min} decision-makers, the ratings are combined with ${label}. Choosing a method needs at least ${min} decision-makers.`,
} as const;

/** Weights step (aggregation_dialog.py:477, fixed text). */
export const WEIGHTS_TEXT = {
  HELP: (min: string, max: string, target: string, tolerance: string) =>
    `Enter a value between ${min} and ${max} for each decision-maker. Weights must sum to ${target} (±${tolerance}).`,
} as const;

/** Median step (aggregation_dialog.py:305-310). */
export const MEDIAN_TEXT = {
  GROUP_LABEL: "Median choice",
  HELP: (n: number) =>
    `${n} decision-makers detected. Choose which median should be used for aggregation.`,
} as const;

/** Ties step (aggregation_dialog.py:672-739). */
export const TIES_TEXT = {
  HELP: (k: number) =>
    `${k} cell(s) ended in a tie. Please select the rating for each one.`,
  HEADING: (codeRow: string, codeCol: string) => `${codeRow} → ${codeCol}`,
  POLICIES: (policyRow: string, policyCol: string) =>
    `${policyRow} → ${policyCol}`,
  OPTIONS_PREFIX: "Tied options: ",
  OPTIONS_SEPARATOR: "  |  ",
  VOTES: "Votes:",
  VOTE: (name: string, rating: string) => `${name}: ${rating}`,
  SELECT_LABEL: "Selected rating",
  PLACEHOLDER: "Select a rating",
  NONE: "No ties remain.",
  /** Above this count the tie cards render in a virtualised list. */
  VIRTUALISE_ABOVE: 50,
  CARD_HEIGHT: 200,
} as const;

/** Links offered with run errors. */
export const RUN_ERROR_LINKS: Record<string, { label: string; step: string }> =
  {
    incomplete_matrices: { label: "Review", step: "review" },
    unresolved_tie: { label: "Ties", step: "ties" },
  };
