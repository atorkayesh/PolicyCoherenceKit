import { afterEach, describe, expect, it, vi } from "vitest";
import { runAnalysis } from "@/services/analysis.service";
import { sentRequest, stubJson } from "@/test/fetch";
import { ANALYSIS } from "@/test/fixtures/analysis.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";
import { errorBody } from "@/test/fixtures/scales.fixture";
import type { ApiError } from "@/utils/api.utils";

describe("analysis service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("runs the analysis and keeps negative zero", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(
        new Response(
          `{"success":true,"data":${JSON.stringify(ANALYSIS).replace('"wii":0,', '"wii":-0.0,')}}`,
        ),
      );
    vi.stubGlobal("fetch", fetch);
    const data = await runAnalysis(REQUEST);
    expect(data.aggregation.method_label).toBe("Average");
    expect(Object.is(data.coherence_scores[2].wii, -0)).toBe(true);
    expect(sentRequest(fetch)).toMatchObject({
      url: "http://localhost:50002/api/v1/analysis",
      method: "POST",
    });
  });

  it("throws unresolved ties with their code", async () => {
    stubJson(
      errorBody("unresolved_tie", "Please select a rating for cell P1 → P2."),
      422,
      true,
    );
    const error = (await runAnalysis(REQUEST).catch(
      (e: unknown) => e,
    )) as ApiError;
    expect([error.code, error.message]).toEqual([
      "unresolved_tie",
      "Please select a rating for cell P1 → P2.",
    ]);
  });
});
