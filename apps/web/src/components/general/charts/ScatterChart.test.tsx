// @vitest-environment node
import { describe, expect, it } from "vitest";
import { ANALYSIS } from "@/test/fixtures/analysis.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { buildChartTheme } from "@/utils/chart-theme.utils";
import { echarts } from "@/utils/echarts.utils";
import { buildPcaOption } from "@/utils/pca-chart.utils";

describe("ScatterChart option with the real SVG renderer", () => {
  it("renders every policy code into the SVG", () => {
    const chart = echarts.init(null, null, {
      renderer: "svg",
      ssr: true,
      width: 800,
      height: 600,
    });
    chart.setOption(
      buildPcaOption(
        ANALYSIS.pca,
        {
          pointColour: "#2c4a6e",
          textColour: "#ffffff",
          categories: SCALES.entropy_categories,
        },
        true,
        buildChartTheme(),
      ),
    );
    const svg = chart.renderToSVGString();
    chart.dispose();
    expect(svg.startsWith("<svg")).toBe(true);
    for (const code of ["P1", "P2", "P3"]) expect(svg).toContain(`>${code}<`);
    expect(svg).toContain("PC1 (62.5%)");
  });
});
