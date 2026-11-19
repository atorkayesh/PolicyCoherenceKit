import { describe, expect, it } from "vitest";
import { CHART_TEXT } from "@/constants/chart.constants";
import { ANALYSIS } from "@/test/fixtures/analysis.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { buildChartTheme } from "@/utils/chart-theme.utils";
import { buildPcaOption, pcaAriaDescription } from "@/utils/pca-chart.utils";

const colours = {
  pointColour: "#2c4a6e",
  textColour: "#ffffff",
  categories: SCALES.entropy_categories,
};
const theme = buildChartTheme();

type Series = {
  name: string;
  itemStyle: { color: string };
  data: { value: number[]; name: string }[];
  markLine?: { data: unknown[]; lineStyle: { color: string; type: string } };
  tooltip: { formatter: (p: unknown) => string };
};

describe("buildPcaOption", () => {
  it("uses the API's bounds, axis names and points in one series", () => {
    const option = buildPcaOption(ANALYSIS.pca, colours, false, theme);
    const x = option.xAxis as { min: number; max: number; name: string };
    expect([x.min, x.max, x.name]).toEqual([-1.68, 1.28, "PC1 (62.5%)"]);
    expect((option.yAxis as { name: string }).name).toBe("PC2 (30.1%)");
    const [s] = option.series as Series[];
    expect(s.itemStyle.color).toBe("#2c4a6e");
    expect(s.data[0]).toEqual({ value: [-1.2, 0.3], name: "P1" });
    expect(s.tooltip.formatter({ dataIndex: 1 })).toBe("P2:  Water");
    expect(s.markLine?.data).toEqual([{ xAxis: 0 }, { yAxis: 0 }]);
    expect(s.markLine?.lineStyle).toMatchObject({
      color: theme.lineStrong,
      type: "dashed",
    });
    expect((option.legend as { show: boolean }).show).toBe(false);
  });

  it("splits points by entropy category with the API colours in colour mode", () => {
    const option = buildPcaOption(ANALYSIS.pca, colours, true, theme);
    const series = option.series as Series[];
    expect(
      series.map((s) => [s.name, s.itemStyle.color, s.data.length]),
    ).toEqual([
      ["Low", "#a3a3a3", 2],
      ["Low-to-Medium", "#a7f3d0", 0],
      ["Medium-to-High", "#34d399", 0],
      ["High", "#059669", 1],
    ]);
    expect(series[3].tooltip.formatter({ dataIndex: 0 })).toBe("P2:  Water");
  });

  it("describes the chart for assistive technology", () => {
    expect(pcaAriaDescription(ANALYSIS.pca, CHART_TEXT.PCA_ARIA)).toBe(
      "PCA scatter of 3 policies. PC1: 62.5%   PC2: 30.1%   Total explained: 92.6%",
    );
  });
});
