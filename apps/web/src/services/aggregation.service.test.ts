import { afterEach, describe, expect, it, vi } from "vitest";
import { previewAggregation } from "@/services/aggregation.service";
import { sentRequest, stubJson } from "@/test/fetch";
import { MAJORITY_PREVIEW } from "@/test/fixtures/aggregation.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";

describe("aggregation service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("previews ties with null scores", async () => {
    const fetch = stubJson(MAJORITY_PREVIEW);
    const data = await previewAggregation(REQUEST);
    expect(data.ties).toHaveLength(2);
    expect(data.scores[0][1]).toBeNull();
    expect(data.ties[0].votes[0]).toEqual({
      decision_maker: "A",
      rating: "Reinforcing",
    });
    expect(sentRequest(fetch)).toMatchObject({
      url: "http://localhost:50002/api/v1/aggregation/preview",
      body: REQUEST,
    });
  });
});
