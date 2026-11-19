import { describe, expect, it } from "vitest";
import { CHART_TEXT } from "@/constants/chart.constants";
import {
  NETWORK_EGO_EMPTY,
  NETWORK_FULL,
} from "@/test/fixtures/analysis.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { buildChartTheme } from "@/utils/chart-theme.utils";
import {
  buildNetworkOption,
  edgeCurveness,
  networkAriaDescription,
} from "@/utils/network-chart.utils";

type Series = {
  data: {
    id: string;
    name: string;
    x: number;
    y: number;
    symbolSize: number;
    itemStyle: { color: string };
    tooltip?: { formatter?: () => string };
  }[];
  links: {
    source: string;
    target: string;
    lineStyle: { color: string; width: number; curveness: number };
    label: { show: boolean; formatter?: string };
  }[];
  roam: boolean;
  draggable: boolean;
  layout: string;
  edgeSymbol: string[];
};

const theme = buildChartTheme();
const series = (option: ReturnType<typeof buildNetworkOption>) =>
  (option.series as Series[])[0];

/** ECharts' quadratic control point (simpleLayoutHelper.js) for an edge from p1 to p2. */
function controlPoint(p1: number[], p2: number[], c: number) {
  return [
    (p1[0] + p2[0]) / 2 - (p1[1] - p2[1]) * c,
    (p1[1] + p2[1]) / 2 - (p2[0] - p1[0]) * c,
  ];
}

describe("buildNetworkOption", () => {
  it("places nodes where the API says, sized by radius and coloured by fill", () => {
    const s = series(buildNetworkOption(NETWORK_FULL, SCALES.network, theme));
    expect(s.layout).toBe("none");
    expect(s.roam).toBe(true);
    expect(s.draggable).toBe(false);
    expect(s.edgeSymbol).toEqual(["none", "arrow"]);
    const p3 = s.data.find((n) => n.id === "2");
    expect(p3).toMatchObject({
      name: "P3",
      x: 300,
      y: 80,
      symbolSize: 36,
      itemStyle: { color: "#aaaaaa" },
    });
    expect(p3?.tooltip?.formatter?.()).toBe("P3:  Food");
    // Two invisible anchors pin the 600×600 layout box (no stretching).
    expect(
      s.data.filter((n) => n.symbolSize === 0).map((n) => [n.x, n.y]),
    ).toEqual([
      [0, 0],
      [600, 600],
    ]);
  });

  it("draws per-edge colours and widths, and bends a two-way pair to opposite sides", () => {
    const s = series(buildNetworkOption(NETWORK_FULL, SCALES.network, theme));
    expect(s.links.map((l) => [l.lineStyle.color, l.lineStyle.width])).toEqual([
      ["#1a6e3c", 2.5],
      ["#b71c1c", 4],
    ]);
    const [forward, back] = s.links;
    const a = [100, 300];
    const b = [500, 300];
    const cpForward = controlPoint(a, b, forward.lineStyle.curveness);
    const cpBack = controlPoint(b, a, back.lineStyle.curveness);
    // The pair lies on y = 300: the two curves must bulge to different sides of it.
    expect(Math.sign(cpForward[1] - 300)).toBe(-Math.sign(cpBack[1] - 300));
    expect(edgeCurveness({ two_way: false })).toBe(0);
  });

  it("hides edges and isolated nodes switched off in the legend", () => {
    const s = series(
      buildNetworkOption(NETWORK_FULL, SCALES.network, theme, {
        positive: false,
        negative: true,
        isolated: true,
      }),
    );
    expect(s.links).toHaveLength(1);
    expect(s.links[0].lineStyle.color).toBe("#1a6e3c");
    expect(s.data.some((n) => n.id === "2")).toBe(false);
  });

  it("shows the ego title and edge labels from the API", () => {
    const withLabel = {
      ...NETWORK_FULL,
      edges: [{ ...NETWORK_FULL.edges[0], label: "+1.50" }],
    };
    expect(
      series(buildNetworkOption(withLabel, SCALES.network, theme)).links[0]
        .label,
    ).toEqual({ show: true, formatter: "+1.50" });
    const ego = buildNetworkOption(NETWORK_EGO_EMPTY, SCALES.network, theme);
    expect((ego.title as { text: string }).text).toBe(
      "Ego Network:  P3  (Food)",
    );
    expect(
      networkAriaDescription(NETWORK_EGO_EMPTY, CHART_TEXT.NETWORK_ARIA),
    ).toContain("P3 has no direct connections.");
  });
});
