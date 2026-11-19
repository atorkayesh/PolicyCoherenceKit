import { describe, expect, it } from "vitest";
import type { StoredAggregationOptions } from "@/interfaces/project.interface";
import {
  answeredSteps,
  canOpenStep,
  currentOptions,
  firstUnansweredAfter,
  firstUnansweredStep,
  isStepId,
  matrixStepIndex,
  nextStep,
  previousStep,
  questionSteps,
  stepLabel,
} from "@/utils/flow.utils";

const DMS = [
  { id: "a", name: "A" },
  { id: "b", name: "B" },
  { id: "c", name: "C" },
  { id: "d", name: "D" },
];
const options = (
  applies: boolean,
  names = "A\nB\nC\nD",
): StoredAggregationOptions => ({
  decision_maker_count: 4,
  method_choice_available: true,
  forced_method: null,
  median_choice_applies: applies,
  forNames: names,
});
const BASE = [
  "project",
  "decision-makers",
  "policies",
  "import",
  "matrix-1",
  "matrix-2",
  "matrix-3",
  "matrix-4",
  "review",
  "method",
];

describe("questionSteps", () => {
  it("lists setup, one matrix per decision-maker, review and method", () => {
    expect(
      questionSteps({
        decisionMakers: DMS,
        method: null,
        aggregationOptions: null,
        tieCount: null,
      }),
    ).toEqual(BASE);
  });

  it("adds weights, median or ties only where they apply", () => {
    const state = {
      decisionMakers: DMS,
      aggregationOptions: options(true),
      tieCount: 0,
    };
    expect(questionSteps({ ...state, method: "weighted" }).at(-1)).toBe(
      "weights",
    );
    expect(questionSteps({ ...state, method: "median" }).at(-1)).toBe("median");
    expect(
      questionSteps({
        ...state,
        method: "median",
        aggregationOptions: options(false),
      }).at(-1),
    ).toBe("method");
    expect(questionSteps({ ...state, method: "majority" }).at(-1)).toBe(
      "method",
    );
    expect(
      questionSteps({ ...state, method: "majority", tieCount: 2 }).at(-1),
    ).toBe("ties");
  });

  it("treats options for other decision-makers as unknown", () => {
    const state = {
      decisionMakers: DMS,
      aggregationOptions: options(true, "A\nB"),
      tieCount: 0,
    };
    expect(currentOptions(state)).toBeNull();
    expect(questionSteps({ ...state, method: "weighted" }).at(-1)).toBe(
      "method",
    );
  });
});

describe("navigation", () => {
  const steps = questionSteps({
    decisionMakers: DMS.slice(0, 2),
    method: null,
    aggregationOptions: null,
    tieCount: null,
  });
  const answered = answeredSteps(
    ["project", "decision-makers", "policies", "import"],
    DMS.slice(0, 2),
    ["b"],
  );

  it("reads answered matrix steps from decision-maker ids", () => {
    expect(answered.has("matrix-2")).toBe(true);
    expect(answered.has("matrix-1")).toBe(false);
  });

  it("guards steps and finds the first unanswered one", () => {
    expect(firstUnansweredStep(steps, answered)).toBe("matrix-1");
    expect(canOpenStep("matrix-2", steps, answered, false)).toBe(false);
    expect(canOpenStep("matrix-1", steps, answered, false)).toBe(true);
    expect(canOpenStep("results", steps, answered, false)).toBe(false);
    expect(canOpenStep("results", steps, answered, true)).toBe(true);
    expect(firstUnansweredAfter("import", steps, answered)).toBe("matrix-1");
    expect(firstUnansweredAfter("import", steps, new Set(steps))).toBe(
      "matrix-1",
    );
  });

  it("moves forwards and backwards", () => {
    expect(nextStep("method", steps)).toBe("results");
    expect(previousStep("project", steps)).toBeNull();
    expect(previousStep("results", steps)).toBe("review");
    expect(previousStep("review", steps)).toBe("matrix-2");
  });

  it("validates ids and labels", () => {
    expect(isStepId("matrix-12")).toBe(true);
    expect(isStepId("matrix-0")).toBe(false);
    expect(isStepId("ties")).toBe(true);
    expect(isStepId("solver")).toBe(false);
    expect(matrixStepIndex("matrix-3")).toBe(2);
    expect(stepLabel("matrix-3")).toBe("Matrix 3");
    expect(stepLabel("decision-makers")).toBe("Decision-makers");
  });
});
