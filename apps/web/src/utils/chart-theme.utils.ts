import type { EChartsOption } from "echarts";

/** Chart chrome from the theme CSS variables (warm-white tokens), read at render time. */
export interface ChartTheme {
  text: string;
  muted: string;
  lineStrong: string;
  border: string;
  popover: string;
  radius: number;
  fontFamily: string;
  spacing: number;
}

/** The theme's base values, used only where CSS variables cannot be read (SSR, tests). */
const FALLBACK: ChartTheme = {
  text: "#023d6b",
  muted: "#6f6a60",
  lineStrong: "#d6cfc2",
  border: "#e8e3d9",
  popover: "#fffdf9",
  radius: 10,
  fontFamily: "'Manrope Variable', 'Helvetica Neue', Helvetica, sans-serif",
  spacing: 4,
};

/** A CSS length (`0.625rem`, `10px`) in pixels; rem uses the root font size. */
function toPixels(value: string, rootSize: number, fallback: number): number {
  const number = Number.parseFloat(value);
  if (Number.isNaN(number)) return fallback;
  return value.trim().endsWith("rem") ? number * rootSize : number;
}

/** Read the chart theme from the document's CSS variables. */
export function buildChartTheme(): ChartTheme {
  if (typeof document === "undefined") return FALLBACK;
  const root = document.documentElement;
  const style = getComputedStyle(root);
  const read = (name: string, fallback: string) =>
    style.getPropertyValue(name).trim() || fallback;
  const rootSize = Number.parseFloat(style.fontSize) || 16;
  return {
    text: read("--foreground", FALLBACK.text),
    muted: read("--muted-foreground", FALLBACK.muted),
    lineStrong: read("--line-strong", FALLBACK.lineStrong),
    border: read("--border", FALLBACK.border),
    popover: read("--popover", FALLBACK.popover),
    radius: toPixels(read("--radius", ""), rootSize, FALLBACK.radius),
    fontFamily: read("--font-sans", FALLBACK.fontFamily),
    spacing: toPixels(read("--spacing", ""), rootSize, FALLBACK.spacing),
  };
}

/** Escape text for ECharts HTML tooltips. */
export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Shared chrome: font, text colour and a tooltip that looks like a shadcn popover. */
export function baseOption(theme: ChartTheme): EChartsOption {
  return {
    animation: false,
    textStyle: { fontFamily: theme.fontFamily, color: theme.text },
    tooltip: {
      trigger: "item",
      backgroundColor: theme.popover,
      borderColor: theme.border,
      borderWidth: 1,
      padding: [theme.spacing * 1.5, theme.spacing * 2.5],
      textStyle: {
        color: theme.text,
        fontFamily: theme.fontFamily,
        fontSize: 12,
      },
      extraCssText: `border-radius:${theme.radius}px;box-shadow:0 1px 2px rgba(17,24,39,0.08);`,
    },
  };
}
