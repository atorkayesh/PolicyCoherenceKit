import { afterEach, describe, expect, it, vi } from "vitest";
import { getNetworkChartData } from "@/services/charts.service";
import { sentRequest, stubJson } from "@/test/fetch";
import {
  NETWORK_EGO_EMPTY,
  NETWORK_FULL,
} from "@/test/fixtures/analysis.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";

describe("charts service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("requests the layout of the full network", async () => {
    const fetch = stubJson(NETWORK_FULL);
    await expect(
      getNetworkChartData(REQUEST, "circular", null),
    ).resolves.toEqual(NETWORK_FULL);
    expect(sentRequest(fetch).url).toBe(
      "http://localhost:50002/api/v1/analysis/charts/network?layout=circular",
    );
  });

  it("adds the focus policy index", async () => {
    const fetch = stubJson(NETWORK_EGO_EMPTY);
    await getNetworkChartData(REQUEST, "force_directed", 2);
    expect(sentRequest(fetch).url).toBe(
      "http://localhost:50002/api/v1/analysis/charts/network?layout=force_directed&focus=2",
    );
  });
});
