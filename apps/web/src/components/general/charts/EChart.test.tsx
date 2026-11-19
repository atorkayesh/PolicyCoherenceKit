import { act, render, screen, waitFor } from "@testing-library/react";
import { createRef } from "react";
import { renderToString } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EChart, type EChartHandle } from "@/components/general/charts/EChart";

const fake = vi.hoisted(() => ({
  init: vi.fn(),
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  getDataURL: vi.fn(),
}));
vi.mock("@/utils/echarts.utils", () => ({
  echarts: {
    init: (...args: unknown[]) => {
      fake.init(...args);
      return fake;
    },
  },
}));

let observed: (() => void) | null = null;
class FakeResizeObserver {
  constructor(callback: () => void) {
    observed = callback;
  }
  observe() {}
  disconnect() {}
}

describe("EChart", () => {
  beforeEach(() => vi.stubGlobal("ResizeObserver", FakeResizeObserver));
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("inits once, sets the option with aria, resizes and disposes", async () => {
    const { rerender, unmount } = render(
      <EChart
        option={{ series: [] }}
        ariaDescription="A chart"
        aspectRatio={1}
      />,
    );
    await waitFor(() => expect(fake.setOption).toHaveBeenCalled());
    expect(fake.init).toHaveBeenCalledTimes(1);
    expect(fake.setOption).toHaveBeenLastCalledWith(
      {
        series: [],
        aria: { enabled: true, label: { description: "A chart" } },
      },
      { notMerge: true },
    );
    expect(screen.getByRole("img", { name: "A chart" })).toBeDefined();

    rerender(
      <EChart
        option={{ series: [{ type: "graph" }] }}
        ariaDescription="A chart"
        aspectRatio={1}
      />,
    );
    await waitFor(() => expect(fake.setOption).toHaveBeenCalledTimes(2));
    expect(fake.init).toHaveBeenCalledTimes(1);

    act(() => observed?.());
    expect(fake.resize).toHaveBeenCalled();

    unmount();
    expect(fake.dispose).toHaveBeenCalled();
  });

  it("resets the view through its ref", async () => {
    const ref = createRef<EChartHandle>();
    render(<EChart ref={ref} option={{}} ariaDescription="x" />);
    await waitFor(() => expect(fake.setOption).toHaveBeenCalledTimes(1));
    ref.current?.resetView();
    expect(fake.setOption).toHaveBeenCalledTimes(2);
    expect(ref.current?.getInstance()).toBe(fake);
  });

  it("renders the skeleton on the server, without ECharts", () => {
    const html = renderToString(
      <EChart option={{}} ariaDescription="x" aspectRatio={1} />,
    );
    expect(html).toContain("chart-skeleton");
    expect(fake.init).not.toHaveBeenCalled();
  });
});
