import { useId, useRef } from "react";
import { ChartLegend } from "@/components/general/charts/ChartLegend";
import { ChartToolbar } from "@/components/general/charts/ChartToolbar";
import type { EChartHandle } from "@/components/general/charts/EChart";
import { ScatterChart } from "@/components/general/charts/ScatterChart";
import { SectionCard } from "@/components/general/SectionCard";
import { Checkbox } from "@/components/ui/checkbox";
import { PCA_TEXT } from "@/constants/results.constants";
import { usePcaColours } from "@/hooks/chart-view.hook";
import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";

/** PCA: the API's stats line and points as an interactive scatter, optionally by entropy category. */
export function PcaPanel({
  data,
  scales,
}: {
  data: AnalysisData;
  scales: ScalesData;
}) {
  const { pca } = data;
  const colourByEntropy = useProjectStore(
    (state) => state.chartView.pcaColourByEntropy,
  );
  const setChartView = useProjectStore((state) => state.setChartView);
  const colours = usePcaColours(scales);
  const chart = useRef<EChartHandle>(null);
  const checkboxId = useId();

  if (!pca.valid) {
    return (
      <SectionCard title={PCA_TEXT.TITLE}>
        <p className="text-muted-foreground">{pca.message}</p>
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title={PCA_TEXT.TITLE}
      subtitle={<span className="whitespace-pre">{pca.stats_text}</span>}
    >
      <div className="flex flex-col gap-3">
        <ChartToolbar onResetView={() => chart.current?.resetView()}>
          <div className="flex items-center gap-2 text-sm">
            <Checkbox
              id={checkboxId}
              checked={colourByEntropy}
              onCheckedChange={(checked) =>
                setChartView({ pcaColourByEntropy: checked === true })
              }
            />
            <label htmlFor={checkboxId}>{PCA_TEXT.COLOUR_BY_ENTROPY}</label>
          </div>
        </ChartToolbar>
        {colourByEntropy && (
          <ChartLegend
            label={PCA_TEXT.ENTROPY_LEGEND}
            items={scales.entropy_categories.map((category) => ({
              key: category.label,
              label: category.label,
              colour: category.fill,
            }))}
          />
        )}
        <div className="mx-auto w-full max-w-3xl">
          <ScatterChart
            ref={chart}
            pca={pca}
            colours={colours}
            colourByEntropy={colourByEntropy}
          />
        </div>
        <p className="text-xs text-muted-foreground">{PCA_TEXT.HINT}</p>
      </div>
    </SectionCard>
  );
}
