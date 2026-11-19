import type { EChartsOption } from "echarts";
import { CHART_EXPORT } from "@/constants/chart.constants";
import { saveBlob } from "@/utils/download.utils";
import { dataUrlToBytes, withPngDpi } from "@/utils/png.utils";

export type ChartFileKind = "png" | "svg";

/** Interactive-only components left out of downloads. */
const EXCLUDED = ["dataZoom", "toolbox"];

/** File name of a chart download: `network_plot.png`, `pca_plot.svg`, … */
export function chartFileName(base: string, kind: ChartFileKind): string {
  return `${base}.${kind}`;
}

/** The option for a static download: white background, no animation, no zoom state. */
export function exportOption(option: EChartsOption): EChartsOption {
  return {
    ...option,
    animation: false,
    backgroundColor: CHART_EXPORT.BACKGROUND,
  };
}

/** Wait for the web fonts, so Manrope is used in the image (not a fallback). */
async function fontsReady(): Promise<void> {
  if (typeof document !== "undefined" && document.fonts) {
    await document.fonts.ready;
  }
}

/** PNG 2400×1800 (800×600 at pixel ratio 3) with a 300 dpi `pHYs` chunk. */
async function renderPng(option: EChartsOption): Promise<Blob> {
  const { echarts } = await import("@/utils/echarts.utils");
  await fontsReady();
  const host = document.createElement("div");
  host.style.cssText = `position:fixed;left:-20000px;top:0;width:${CHART_EXPORT.WIDTH}px;height:${CHART_EXPORT.HEIGHT}px;`;
  document.body.append(host);
  const chart = echarts.init(host, null, {
    renderer: "canvas",
    width: CHART_EXPORT.WIDTH,
    height: CHART_EXPORT.HEIGHT,
  });
  try {
    chart.setOption(exportOption(option));
    const url = chart.getDataURL({
      type: "png",
      pixelRatio: CHART_EXPORT.PIXEL_RATIO,
      backgroundColor: CHART_EXPORT.BACKGROUND,
      excludeComponents: EXCLUDED,
    });
    const bytes = withPngDpi(dataUrlToBytes(url), CHART_EXPORT.DPI);
    return new Blob([bytes as BlobPart], { type: "image/png" });
  } finally {
    chart.dispose();
    host.remove();
  }
}

/** SVG from the SVG renderer (server-side mode: no DOM needed). */
async function renderSvg(option: EChartsOption): Promise<Blob> {
  const { echarts } = await import("@/utils/echarts.utils");
  await fontsReady();
  const chart = echarts.init(null, null, {
    renderer: "svg",
    ssr: true,
    width: CHART_EXPORT.WIDTH,
    height: CHART_EXPORT.HEIGHT,
  });
  try {
    chart.setOption(exportOption(option));
    const svg = chart.renderToSVGString();
    return new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  } finally {
    chart.dispose();
  }
}

/** Render `option` off-screen and download it as `{base}.png` or `{base}.svg`. */
export async function downloadChart(
  option: EChartsOption,
  kind: ChartFileKind,
  base: string,
): Promise<void> {
  const blob =
    kind === "png" ? await renderPng(option) : await renderSvg(option);
  saveBlob(blob, chartFileName(base, kind));
}
