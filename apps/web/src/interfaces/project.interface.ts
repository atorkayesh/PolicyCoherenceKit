import type { ReactNode } from "react";
import { z } from "zod";

/** A decision-maker or policy with a stable id, so renames and removals never move ratings. */
export interface NamedItem {
  id: string;
  name: string;
}

/** Ids of the fixed flow steps; `matrix-{i}` is decision-maker i's matrix (1-based). */
export type FixedStepId =
  | "project"
  | "decision-makers"
  | "policies"
  | "import"
  | "review"
  | "method"
  | "weights"
  | "median"
  | "ties"
  | "results";

export type StepId = FixedStepId | `matrix-${number}`;

/** What the flow shell gives every question step. */
export interface StepProps {
  /** 1-based position shown above the question. */
  number: number;
  /** Mark the step answered and open the next one. */
  onAdvance: () => void;
  /** Open the previous step; null on the first step. */
  onBack: (() => void) | null;
  /** Open any step (Edit links, error links, import jumps). */
  onOpen: (step: StepId) => void;
  /** Whether this is the last question step (its OK runs the analysis). */
  isLast: boolean;
}

/** Search params of `/`: the open step; anything invalid is dropped (the guard then redirects). */
export const flowSearchSchema = z.object({
  step: z.string().optional().catch(undefined),
});

/** One row of a name list draft: `id` is the committed item it edits, null for a new row. */
export interface DraftRow {
  key: string;
  id: string | null;
  name: string;
}

/** The last `/matrices/check` options with the decision-maker names they were computed for. */
export interface StoredAggregationOptions {
  decision_maker_count: number;
  method_choice_available: boolean;
  forced_method: string | null;
  median_choice_applies: boolean;
  forNames: string;
}

/** Chart controls of the Results screen. */
export interface ChartView {
  pcaColourByEntropy: boolean;
  networkLayout: string | null;
  networkFocus: number | null;
}

/** An inline error under a question: the API's message, its legacy title and an optional link. */
export interface StepError {
  message: string;
  title?: string | null;
  action?: ReactNode;
}
