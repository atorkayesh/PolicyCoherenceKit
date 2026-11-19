import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DirectedNetworkChart } from "@/components/general/charts/DirectedNetworkChart";
import {
  NETWORK_EGO_EMPTY,
  NETWORK_FULL,
} from "@/test/fixtures/analysis.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";

const fake = vi.hoisted(() => ({
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
}));
vi.mock("@/utils/echarts.utils", () => ({ echarts: { init: () => fake } }));

describe("DirectedNetworkChart", () => {
  beforeEach(() =>
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
      },
    ),
  );
  afterEach(() => vi.unstubAllGlobals());

  it("draws the API's graph and describes it", async () => {
    render(
      <DirectedNetworkChart data={NETWORK_FULL} colours={SCALES.network} />,
    );
    await waitFor(() => expect(fake.setOption).toHaveBeenCalled());
    const option = fake.setOption.mock.calls.at(-1)?.[0];
    expect(option.series[0].type).toBe("graph");
    expect(option.aria.label.description).toContain("Force-Directed layout");
    expect(screen.getByRole("img").getAttribute("style")).toContain(
      "aspect-ratio: 1",
    );
  });

  it("shows the ego empty message below the chart", () => {
    render(
      <DirectedNetworkChart
        data={NETWORK_EGO_EMPTY}
        colours={SCALES.network}
      />,
    );
    expect(screen.getByText("P3 has no direct connections.")).toBeDefined();
  });
});
