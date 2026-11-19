import { afterEach, describe, expect, it, vi } from "vitest";
import { checkMatrices } from "@/services/matrices.service";
import { sentRequest, stubJson } from "@/test/fetch";
import { CHECK_INCOMPLETE } from "@/test/fixtures/check.fixture";

describe("matrices service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("posts the project and returns completeness and options", async () => {
    const fetch = stubJson(CHECK_INCOMPLETE);
    const project = {
      project_name: "x",
      policies: ["a", "b"],
      decision_makers: [
        {
          name: "A",
          ratings: [
            ["Neutral", ""],
            ["", "Neutral"],
          ],
        },
      ],
    };
    await expect(checkMatrices(project)).resolves.toEqual(CHECK_INCOMPLETE);
    expect(sentRequest(fetch)).toMatchObject({
      url: "http://localhost:50002/api/v1/matrices/check",
      body: project,
    });
  });
});
