import { useRef, useState } from "react";
import { ChartLegend } from "@/components/general/charts/ChartLegend";
import { ChartToolbar } from "@/components/general/charts/ChartToolbar";
import { DirectedNetworkChart } from "@/components/general/charts/DirectedNetworkChart";
import type { EChartHandle } from "@/components/general/charts/EChart";
import { InlineError } from "@/components/general/InlineError";
import { SectionCard } from "@/components/general/SectionCard";
import { CentralityTable } from "@/components/page-specific/assessment/CentralityTable";
import { NetworkSelects } from "@/components/page-specific/assessment/NetworkSelects";
import { NETWORK_TEXT } from "@/constants/results.constants";
import { useNetworkView } from "@/hooks/chart-view.hook";
import { useNetworkChartData } from "@/hooks/network-chart.hook";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { errorMessage } from "@/utils/api.utils";
import { type NetworkHidden, NO_HIDDEN } from "@/utils/network-chart.utils";

/** Network Analysis: stats, Layout and Focus selects, the graph (API chart data) and centrality. */
export function NetworkPanel({
  snapshot,
  snapshotHash,
  data,
  scales,
}: {
  snapshot: AnalysisRequest;
  snapshotHash: string;
  data: AnalysisData;
  scales: ScalesData;
}) {
  const { layout, focus } = useNetworkView(scales);
  const chartData = useNetworkChartData(snapshot, snapshotHash, layout, focus);
  const chart = useRef<EChartHandle>(null);
  const [hidden, setHidden] = useState<NetworkHidden>(NO_HIDDEN);
  const colours = scales.network;
  const legend = [
    {
      key: "positive",
      label: NETWORK_TEXT.POSITIVE,
      colour: colours.positive_colour,
    },
    {
      key: "negative",
      label: NETWORK_TEXT.NEGATIVE,
      colour: colours.negative_colour,
    },
    {
      key: "isolated",
      label: NETWORK_TEXT.ISOLATED,
      colour: colours.isolated_colour,
    },
  ] as const;

  return (
    <SectionCard
      title={NETWORK_TEXT.TITLE}
      subtitle={
        <span className="whitespace-pre-wrap wrap-break-word">
          {data.network.stats_text}
        </span>
      }
    >
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-3 lg:col-span-2">
          <ChartToolbar onResetView={() => chart.current?.resetView()}>
            <NetworkSelects scales={scales} policies={data.aggregation} />
          </ChartToolbar>
          <ChartLegend
            items={legend.map((item) => ({
              ...item,
              hidden: hidden[item.key],
            }))}
            onToggle={(key) =>
              setHidden((old) => ({
                ...old,
                [key]: !old[key as keyof NetworkHidden],
              }))
            }
          />
          {chartData.isPending && (
            <p className="text-sm text-muted-foreground">
              {NETWORK_TEXT.LOADING}
            </p>
          )}
          <InlineError
            message={chartData.error ? errorMessage(chartData.error) : null}
          />
          {chartData.data && (
            <DirectedNetworkChart
              ref={chart}
              data={chartData.data}
              colours={colours}
              hidden={hidden}
            />
          )}
        </div>
        <CentralityTable network={data.network} />
      </div>
    </SectionCard>
  );
}
