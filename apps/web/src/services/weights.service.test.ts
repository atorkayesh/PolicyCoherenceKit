import { afterEach, describe, expect, it, vi } from "vitest";
import { checkWeights } from "@/services/weights.service";
import { sentRequest, stubJson } from "@/test/fetch";

const RESULT = {
  total: null,
  sum_text: "Sum: —",
  within_tolerance: false,
  valid: false,
  weights: [0.5, null],
  errors: [
    {
      index: 1,
      decision_maker: "B",
      title: "Invalid Value",
      message: 'Weight for "B" must be a number.',
    },
  ],
  first_error: {
    index: 1,
    decision_maker: "B",
    title: "Invalid Value",
    message: 'Weight for "B" must be a number.',
  },
};

describe("weights service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("posts the raw texts and returns the check", async () => {
    const fetch = stubJson(RESULT);
    await expect(
      checkWeights({ decision_makers: ["A", "B"], weights: ["0.5", "x"] }),
    ).resolves.toEqual(RESULT);
    expect(sentRequest(fetch)).toMatchObject({
      url: "http://localhost:50002/api/v1/weights/check",
      body: { decision_makers: ["A", "B"], weights: ["0.5", "x"] },
    });
  });
});
