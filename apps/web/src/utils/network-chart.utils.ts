import type { EChartsOption } from "echarts";
import { CHART_SIZE } from "@/constants/chart.constants";
import type {
  NetworkChartData,
  NetworkEdge,
} from "@/interfaces/chart.interface";
import type { NetworkScale } from "@/interfaces/scales.interface";
import {
  baseOption,
  type ChartTheme,
  escapeHtml,
} from "@/utils/chart-theme.utils";

/** Which legend entries are switched off. */
export interface NetworkHidden {
  positive: boolean;
  negative: boolean;
  isolated: boolean;
}

export const NO_HIDDEN: NetworkHidden = {
  positive: false,
  negative: false,
  isolated: false,
};

/** Ids of the two invisible corner nodes that pin the API's layout box (P9: no stretching). */
const ANCHOR_IDS = ["anchor-top-left", "anchor-bottom-right"] as const;

/**
 * Curveness of an edge. ECharts places the control point perpendicular to the edge's own direction
 * (`simpleLayoutHelper.js`), so both edges of a two-way pair take the same value and bend to
 * opposite sides; one-way edges are straight.
 */
export function edgeCurveness(edge: Pick<NetworkEdge, "two_way">): number {
  return edge.two_way ? CHART_SIZE.TWO_WAY_CURVENESS : 0;
}

/** Whether an edge is shown under the legend toggles. */
function edgeVisible(edge: NetworkEdge, hidden: NetworkHidden): boolean {
  return edge.sign === "negative" ? !hidden.negative : !hidden.positive;
}

/**
 * The ECharts option of the directed network: node positions, sizes, colours, edge widths and
 * labels are the API's; the browser only maps them to the graph series.
 */
export function buildNetworkOption(
  data: NetworkChartData,
  colours: Pick<NetworkScale, "node_text_colour">,
  theme: ChartTheme,
  hidden: NetworkHidden = NO_HIDDEN,
): EChartsOption {
  const nodes = data.nodes.filter(
    (node) => !(hidden.isolated && node.isolated),
  );
  const shown = new Set(nodes.map((node) => node.index));
  const edges = data.edges.filter(
    (edge) =>
      edgeVisible(edge, hidden) &&
      shown.has(edge.source) &&
      shown.has(edge.target),
  );
  const { width, height } = data.canvas;
  const anchors = [
    { id: ANCHOR_IDS[0], x: 0, y: 0 },
    { id: ANCHOR_IDS[1], x: width, y: height },
  ].map((anchor) => ({
    ...anchor,
    name: "",
    symbolSize: 0,
    silent: true,
    label: { show: false },
    tooltip: { show: false },
    itemStyle: { opacity: 0 },
  }));
  const padding = CHART_SIZE.NETWORK_PADDING;

  return {
    ...baseOption(theme),
    title: data.title
      ? {
          text: data.title,
          left: "center",
          top: 4,
          textStyle: {
            color: theme.text,
            fontFamily: theme.fontFamily,
            fontSize: 14,
          },
        }
      : undefined,
    series: [
      {
        type: "graph",
        layout: "none",
        roam: true,
        draggable: false,
        left: padding,
        right: padding,
        top: padding,
        bottom: padding,
        edgeSymbol: ["none", "arrow"],
        edgeSymbolSize: 10,
        label: {
          show: true,
          position: "inside",
          color: colours.node_text_colour,
          fontWeight: "bold",
          fontFamily: theme.fontFamily,
          fontSize: 11,
        },
        edgeLabel: {
          color: theme.text,
          fontFamily: theme.fontFamily,
          fontSize: 11,
        },
        emphasis: { focus: "adjacency" },
        data: [
          ...nodes.map((node) => ({
            id: String(node.index),
            name: node.code,
            x: node.x,
            y: node.y,
            symbolSize: node.radius * 2,
            itemStyle: { color: node.fill },
            tooltip: { formatter: () => escapeHtml(node.label) },
          })),
          ...anchors,
        ],
        links: edges.map((edge) => ({
          source: String(edge.source),
          target: String(edge.target),
          lineStyle: {
            color: edge.colour,
            width: edge.width,
            curveness: edgeCurveness(edge),
            opacity: 1,
          },
          label: edge.label
            ? { show: true, formatter: edge.label }
            : { show: false },
          tooltip: { show: false },
        })),
      },
    ],
  };
}

/** Text alternative of the network chart (aria description). */
export function networkAriaDescription(
  data: NetworkChartData,
  describe: (stats: string, layout: string) => string,
): string {
  const parts = [describe(data.stats.text, data.layout_label)];
  if (data.title) parts.unshift(data.title);
  if (data.empty_message) parts.push(data.empty_message);
  return parts.join(" ");
}
