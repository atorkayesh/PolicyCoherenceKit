import { type Ref, useMemo } from "react";
import {
  EChart,
  type EChartHandle,
  useChartTheme,
} from "@/components/general/charts/EChart";
import { CHART_SIZE, CHART_TEXT } from "@/constants/chart.constants";
import type { NetworkChartData } from "@/interfaces/chart.interface";
import type { NetworkScale } from "@/interfaces/scales.interface";
import {
  buildNetworkOption,
  type NetworkHidden,
  NO_HIDDEN,
  networkAriaDescription,
} from "@/utils/network-chart.utils";

/**
 * Directed network graph from the API's chart data (positions, colours, widths, labels), drawn in a
 * square plot so the layout is never stretched. Zoom and pan; no dragging. The ego view's empty
 * message is shown below the chart, never over a node.
 */
export function DirectedNetworkChart({
  data,
  colours,
  hidden = NO_HIDDEN,
  ref,
}: {
  data: NetworkChartData;
  colours: Pick<NetworkScale, "node_text_colour">;
  hidden?: NetworkHidden;
  ref?: Ref<EChartHandle>;
}) {
  const theme = useChartTheme();
  const option = useMemo(
    () => buildNetworkOption(data, colours, theme, hidden),
    [data, colours, theme, hidden],
  );
  return (
    <div className="flex w-full flex-col items-center gap-2">
      <div className="w-full max-w-[min(100%,42rem)]">
        <EChart
          ref={ref}
          option={option}
          aspectRatio={CHART_SIZE.NETWORK_ASPECT}
          ariaDescription={networkAriaDescription(
            data,
            CHART_TEXT.NETWORK_ARIA,
          )}
        />
      </div>
      {data.empty_message && (
        <p className="text-sm text-muted-foreground">{data.empty_message}</p>
      )}
    </div>
  );
}
