import { describe, expect, it } from "vitest";
import {
  buildAnalysisRequest,
  hashString,
  previewRequest,
  type RequestInputs,
  requestKey,
  tieKey,
} from "@/utils/analysis-request.utils";

const RULES = { default_method: "average", default_median_choice: "lower" };
const INPUTS: RequestInputs = {
  projectName: "  Nexus ",
  decisionMakers: [
    { id: "d1", name: " Alice " },
    { id: "d2", name: "Bob" },
  ],
  policies: [
    { id: "p1", name: "Energy" },
    { id: "p2", name: "Water " },
  ],
  matrices: {
    d1: [
      ["Neutral", "Enabling"],
      ["", "Neutral"],
    ],
    d2: [
      ["Neutral", ""],
      ["", "Neutral"],
    ],
  },
  method: null,
  weights: null,
  medianChoice: null,
  tieChoices: {},
};

describe("buildAnalysisRequest", () => {
  it("trims names and uses the default method", () => {
    const request = buildAnalysisRequest(INPUTS, RULES);
    expect(request.project_name).toBe("Nexus");
    expect(request.policies).toEqual(["Energy", "Water"]);
    expect(request.decision_makers[0]).toEqual({
      name: "Alice",
      ratings: INPUTS.matrices.d1,
    });
    expect(request.aggregation).toEqual({
      method: "average",
      weights: null,
      median_choice: null,
      tie_choices: [],
    });
  });

  it("lists weights in decision-maker order by id", () => {
    const request = buildAnalysisRequest(
      { ...INPUTS, method: "weighted", weights: { d2: 0.4, d1: 0.6 } },
      RULES,
    );
    expect(request.aggregation.weights).toEqual([0.6, 0.4]);
    const partial = buildAnalysisRequest(
      { ...INPUTS, method: "weighted", weights: { d1: 1 } },
      RULES,
    );
    expect(partial.aggregation.weights).toBeNull();
  });

  it("defaults the median choice and maps tie choices to indices", () => {
    expect(
      buildAnalysisRequest({ ...INPUTS, method: "median" }, RULES).aggregation
        .median_choice,
    ).toBe("lower");
    const majority = buildAnalysisRequest(
      {
        ...INPUTS,
        method: "majority",
        tieChoices: {
          [tieKey("p2", "p1")]: "Enabling",
          [tieKey("gone", "p1")]: "Neutral",
        },
      },
      RULES,
    );
    expect(majority.aggregation.tie_choices).toEqual([
      { row: 1, col: 0, rating: "Enabling" },
    ]);
    expect(previewRequest(majority).aggregation.tie_choices).toEqual([]);
  });

  it("hashes requests stably", () => {
    const a = requestKey(buildAnalysisRequest(INPUTS, RULES));
    expect(hashString(a)).toBe(hashString(a));
    expect(hashString(a)).not.toBe(hashString(`${a} `));
    expect(requestKey(null)).toBe("");
  });
});
