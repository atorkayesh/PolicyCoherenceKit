import { afterEach, describe, expect, it, vi } from "vitest";
import { getScales } from "@/services/scales.service";
import { sentRequest, stubJson } from "@/test/fetch";
import { SCALES } from "@/test/fixtures/scales.fixture";

describe("scales service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads and validates the scales", async () => {
    const fetch = stubJson(SCALES);
    await expect(getScales()).resolves.toEqual(SCALES);
    expect(sentRequest(fetch).url).toBe("http://localhost:50002/api/v1/scales");
  });

  it("rejects a response that breaks the contract", async () => {
    stubJson({ ...SCALES, rules: null });
    await expect(getScales()).rejects.toThrow();
  });
});
