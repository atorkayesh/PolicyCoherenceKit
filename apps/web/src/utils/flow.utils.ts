import { MATRIX_TEXT, STEP_TEXT } from "@/constants/steps.constants";
import type {
  FixedStepId,
  NamedItem,
  StepId,
  StoredAggregationOptions,
} from "@/interfaces/project.interface";

/** The question steps before the matrices. */
export const SETUP_STEPS: readonly FixedStepId[] = [
  "project",
  "decision-makers",
  "policies",
  "import",
];

const AFTER_MATRICES: readonly FixedStepId[] = [
  "review",
  "method",
  "weights",
  "median",
  "ties",
];

/** The state `questionSteps` reads. */
export interface FlowState {
  decisionMakers: readonly NamedItem[];
  method: string | null;
  aggregationOptions: StoredAggregationOptions | null;
  tieCount: number | null;
}

/** Key the aggregation options are stored for: the decision-maker names. */
export function namesKey(decisionMakers: readonly NamedItem[]): string {
  return decisionMakers.map((dm) => dm.name).join("\n");
}

/** The stored options if they were computed for the current decision-makers, else null. */
export function currentOptions(
  state: Pick<FlowState, "decisionMakers" | "aggregationOptions">,
): StoredAggregationOptions | null {
  const options = state.aggregationOptions;
  return options && options.forNames === namesKey(state.decisionMakers)
    ? options
    : null;
}

/** Step id of decision-maker `index`'s matrix (0-based index, 1-based id). */
export function matrixStepId(index: number): StepId {
  return `matrix-${index + 1}`;
}

/** 0-based decision-maker index of a matrix step, or null for other steps. */
export function matrixStepIndex(step: StepId): number | null {
  const match = /^matrix-(\d+)$/.exec(step);
  return match ? Number(match[1]) - 1 : null;
}

/** Which step follows `method` for `method` and the options (null: none, the method step runs). */
export function stepAfterMethod(
  method: string | null,
  options: StoredAggregationOptions | null,
  tieCount: number | null,
): FixedStepId | null {
  if (!options?.method_choice_available) return null;
  if (method === "weighted") return "weights";
  if (method === "median" && options.median_choice_applies) return "median";
  if (method === "majority" && (tieCount ?? 0) > 0) return "ties";
  return null;
}

/** Question steps in order for the current state (Results is not a question). */
export function questionSteps(state: FlowState): StepId[] {
  const after = stepAfterMethod(
    state.method,
    currentOptions(state),
    state.tieCount,
  );
  return [
    ...SETUP_STEPS,
    ...state.decisionMakers.map((_, i) => matrixStepId(i)),
    "review",
    "method",
    ...(after ? [after] : []),
  ];
}

/** Whether `value` names a step that can exist (search param validation). */
export function isStepId(value: string): value is StepId {
  return (
    value === "results" ||
    (SETUP_STEPS as readonly string[]).includes(value) ||
    (AFTER_MATRICES as readonly string[]).includes(value) ||
    /^matrix-[1-9]\d*$/.test(value)
  );
}

/** The first step that is not answered yet: the farthest step the user may open. */
export function firstUnansweredStep(
  steps: readonly StepId[],
  answered: ReadonlySet<StepId>,
): StepId {
  return steps.find((step) => !answered.has(step)) ?? steps[steps.length - 1];
}

/** The first unanswered step after `step`, else the next one in order. */
export function firstUnansweredAfter(
  step: StepId,
  steps: readonly StepId[],
  answered: ReadonlySet<StepId>,
): StepId {
  const later = steps.slice(steps.indexOf(step) + 1);
  return later.find((item) => !answered.has(item)) ?? nextStep(step, steps);
}

/** Whether `step` can be opened: all earlier steps are answered (Results needs results). */
export function canOpenStep(
  step: StepId,
  steps: readonly StepId[],
  answered: ReadonlySet<StepId>,
  hasResults: boolean,
): boolean {
  if (step === "results") return hasResults;
  const index = steps.indexOf(step);
  if (index < 0) return false;
  return steps.slice(0, index).every((earlier) => answered.has(earlier));
}

/** The step after `step`, or Results after the last question. */
export function nextStep(step: StepId, steps: readonly StepId[]): StepId {
  const index = steps.indexOf(step);
  return steps[index + 1] ?? "results";
}

/** The step before `step`; Results goes back to Review. */
export function previousStep(
  step: StepId,
  steps: readonly StepId[],
): StepId | null {
  if (step === "results") return "review";
  const index = steps.indexOf(step);
  return index > 0 ? steps[index - 1] : null;
}

/** Short label of a step for the step list. */
export function stepLabel(step: StepId): string {
  const index = matrixStepIndex(step);
  return index === null
    ? STEP_TEXT[step as FixedStepId].label
    : MATRIX_TEXT.LABEL(index);
}

/** Answered steps: fixed answers plus the matrix steps of answered decision-maker ids. */
export function answeredSteps(
  answered: readonly FixedStepId[],
  decisionMakers: readonly NamedItem[],
  answeredMatrices: readonly string[],
): Set<StepId> {
  const set = new Set<StepId>(answered);
  decisionMakers.forEach((dm, i) => {
    if (answeredMatrices.includes(dm.id)) set.add(matrixStepId(i));
  });
  return set;
}
