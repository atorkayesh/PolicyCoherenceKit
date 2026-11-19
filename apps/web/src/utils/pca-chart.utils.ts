import type { EChartsOption } from "echarts";
import { CHART_SIZE } from "@/constants/chart.constants";
import type { PcaData, PcaPoint } from "@/interfaces/analysis.interface";
import type { EntropyCategory } from "@/interfaces/scales.interface";
import {
  baseOption,
  type ChartTheme,
  escapeHtml,
} from "@/utils/chart-theme.utils";

/** Colours of the PCA scatter (all from `/scales`). */
export interface PcaColours {
  pointColour: string;
  textColour: string;
  categories: readonly EntropyCategory[];
}

const datum = (point: PcaPoint) => ({
  value: [point.x, point.y],
  name: point.code,
});

/**
 * The ECharts option of the PCA scatter: points, axis bounds and axis names are the API's. With
 * `colourByEntropy`, one series per entropy category (legend toggles them), else one series.
 */
export function buildPcaOption(
  pca: PcaData,
  colours: PcaColours,
  colourByEntropy: boolean,
  theme: ChartTheme,
): EChartsOption {
  const bounds = pca.bounds;
  const groups = colourByEntropy
    ? colours.categories.map((category) => ({
        name: category.label,
        colour: category.fill,
        points: pca.points.filter((p) => p.entropy_category === category.label),
      }))
    : [{ name: "", colour: colours.pointColour, points: pca.points }];
  const axis = (name: string | null, min?: number, max?: number) => ({
    type: "value" as const,
    name: name ?? "",
    nameLocation: "middle" as const,
    nameGap: 28,
    nameTextStyle: { color: theme.muted, fontFamily: theme.fontFamily },
    min,
    max,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: theme.muted, fontFamily: theme.fontFamily },
    splitLine: { lineStyle: { color: theme.border } },
  });
  const zeroLine = {
    silent: true,
    symbol: "none",
    label: { show: false },
    lineStyle: { color: theme.lineStrong, type: "dashed" as const, width: 1 },
    data: [{ xAxis: 0 }, { yAxis: 0 }],
  };

  return {
    ...baseOption(theme),
    grid: { left: 56, right: 24, top: colourByEntropy ? 40 : 16, bottom: 48 },
    legend: colourByEntropy
      ? {
          top: 4,
          textStyle: { color: theme.text, fontFamily: theme.fontFamily },
          data: groups.map((group) => group.name),
        }
      : { show: false },
    xAxis: axis(pca.x_axis_label, bounds?.x_min, bounds?.x_max),
    yAxis: axis(pca.y_axis_label, bounds?.y_min, bounds?.y_max),
    dataZoom: [
      { type: "inside", xAxisIndex: 0, filterMode: "none" },
      { type: "inside", yAxisIndex: 0, filterMode: "none" },
    ],
    series: groups.map((group, index) => ({
      type: "scatter",
      name: group.name,
      symbolSize: CHART_SIZE.PCA_SYMBOL_SIZE,
      itemStyle: { color: group.colour },
      label: {
        show: true,
        position: "inside",
        formatter: "{b}",
        color: colours.textColour,
        fontWeight: "bold",
        fontFamily: theme.fontFamily,
        fontSize: 10,
      },
      tooltip: {
        formatter: (params: unknown) =>
          escapeHtml(
            group.points[(params as { dataIndex: number }).dataIndex]?.label ??
              "",
          ),
      },
      data: group.points.map(datum),
      markLine: index === 0 ? zeroLine : undefined,
    })),
  };
}

/** Text alternative of the PCA chart (aria description). */
export function pcaAriaDescription(
  pca: PcaData,
  describe: (stats: string, count: number) => string,
): string {
  return describe(pca.stats_text ?? "", pca.points.length);
}
