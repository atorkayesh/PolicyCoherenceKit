import { afterEach, describe, expect, it, vi } from "vitest";
import { validateSetup } from "@/services/setup.service";
import { sentRequest, stubJson } from "@/test/fetch";
import { errorBody } from "@/test/fixtures/scales.fixture";
import { SETUP_POLICIES } from "@/test/fixtures/setup.fixture";
import { ApiError } from "@/utils/api.utils";

describe("setup service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("posts only the parts to validate and returns names and codes", async () => {
    const fetch = stubJson(SETUP_POLICIES);
    await expect(
      validateSetup({ policies: ["Energy", "Water", "Food"] }),
    ).resolves.toEqual(SETUP_POLICIES);
    expect(sentRequest(fetch)).toMatchObject({
      url: "http://localhost:50002/api/v1/setup/validate",
      method: "POST",
      body: { policies: ["Energy", "Water", "Food"] },
    });
  });

  it("throws the legacy message with code and title", async () => {
    stubJson(
      errorBody("invalid_setup", "Policy names must be unique.", {
        title: "Duplicate Policies",
        field: "policies",
      }),
      422,
      true,
    );
    const error = (await validateSetup({ policies: ["a", "a"] }).catch(
      (e: unknown) => e,
    )) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect([error.status, error.code, error.message]).toEqual([
      422,
      "invalid_setup",
      "Policy names must be unique.",
    ]);
    expect(error.data).toEqual({
      title: "Duplicate Policies",
      field: "policies",
    });
  });
});
