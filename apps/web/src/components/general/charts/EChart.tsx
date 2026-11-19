import { ClientOnly } from "@tanstack/react-router";
import type { EChartsOption } from "echarts";
import type { ECharts } from "echarts/core";
import {
  type Ref,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import { cn } from "@/lib/utils";
import { type ChartFileKind, downloadChart } from "@/utils/chart-export.utils";
import { buildChartTheme, type ChartTheme } from "@/utils/chart-theme.utils";

/** What a parent can do with a chart. */
export interface EChartHandle {
  getInstance: () => ECharts | null;
  /** Undo zoom and pan. */
  resetView: () => void;
  /** Download the current option as PNG (2400×1800, 300 dpi) or SVG. */
  download: (kind: ChartFileKind, fileName: string) => Promise<void>;
}

export interface EChartProps {
  option: EChartsOption;
  /** Text alternative (ECharts `aria`); the tables beside the charts give the details. */
  ariaDescription: string;
  /** Width / height; the chart keeps it at every width. */
  aspectRatio?: number;
  height?: number;
  renderer?: "canvas" | "svg";
  className?: string;
  ref?: Ref<EChartHandle>;
}

/** The chart theme read from the CSS variables once per mount. */
export function useChartTheme(): ChartTheme {
  return useMemo(() => buildChartTheme(), []);
}

/** The option with the aria description switched on. */
export function withAria(
  option: EChartsOption,
  description: string,
): EChartsOption {
  return { ...option, aria: { enabled: true, label: { description } } };
}

function sizeStyle(aspectRatio?: number, height?: number) {
  return aspectRatio ? { aspectRatio: String(aspectRatio) } : { height };
}

/**
 * Themed base chart: client only (ECharts needs `window`), the chunk loaded with `import()`, one
 * instance per mount (init on mount, `setOption` with `notMerge` on change, resized by a
 * `ResizeObserver`, disposed on unmount). Skeleton while loading or on the server.
 */
export function EChart(props: EChartProps) {
  return (
    <ClientOnly
      fallback={
        <div
          aria-hidden="true"
          data-testid="chart-skeleton"
          className={cn(
            "w-full animate-pulse rounded-lg bg-muted",
            props.className,
          )}
          style={sizeStyle(props.aspectRatio, props.height)}
        />
      }
    >
      <ClientChart {...props} />
    </ClientOnly>
  );
}

function ClientChart({
  option,
  ariaDescription,
  aspectRatio,
  height = 400,
  renderer = "canvas",
  className,
  ref,
}: EChartProps) {
  const host = useRef<HTMLDivElement>(null);
  const chart = useRef<ECharts | null>(null);
  const [ready, setReady] = useState(false);
  const fullOption = useMemo(
    () => withAria(option, ariaDescription),
    [option, ariaDescription],
  );

  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | null = null;
    void import("@/utils/echarts.utils").then(({ echarts }) => {
      if (disposed || !host.current) return;
      const instance = echarts.init(host.current, null, { renderer });
      chart.current = instance;
      if (typeof ResizeObserver !== "undefined") {
        observer = new ResizeObserver(() => instance.resize());
        observer.observe(host.current);
      }
      setReady(true);
    });
    return () => {
      disposed = true;
      observer?.disconnect();
      chart.current?.dispose();
      chart.current = null;
    };
  }, [renderer]);

  useEffect(() => {
    if (ready) chart.current?.setOption(fullOption, { notMerge: true });
  }, [ready, fullOption]);

  useImperativeHandle(
    ref,
    () => ({
      getInstance: () => chart.current,
      resetView: () => chart.current?.setOption(fullOption, { notMerge: true }),
      download: (kind, fileName) => downloadChart(fullOption, kind, fileName),
    }),
    [fullOption],
  );

  return (
    <div
      ref={host}
      role="img"
      aria-label={ariaDescription}
      className={cn("w-full", className)}
      style={sizeStyle(aspectRatio, height)}
    />
  );
}
