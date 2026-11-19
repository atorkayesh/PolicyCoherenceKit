import { type Ref, useMemo } from "react";
import {
  EChart,
  type EChartHandle,
  useChartTheme,
} from "@/components/general/charts/EChart";
import { CHART_SIZE, CHART_TEXT } from "@/constants/chart.constants";
import type { PcaData } from "@/interfaces/analysis.interface";
import {
  buildPcaOption,
  type PcaColours,
  pcaAriaDescription,
} from "@/utils/pca-chart.utils";

/**
 * Scatter of the API's PCA points with its axis bounds and names, dashed zero lines, zoom inside
 * the plot, and the policy label as tooltip. Colour mode splits the points by entropy category.
 */
export function ScatterChart({
  pca,
  colours,
  colourByEntropy,
  ref,
}: {
  pca: PcaData;
  colours: PcaColours;
  colourByEntropy: boolean;
  ref?: Ref<EChartHandle>;
}) {
  const theme = useChartTheme();
  const option = useMemo(
    () => buildPcaOption(pca, colours, colourByEntropy, theme),
    [pca, colours, colourByEntropy, theme],
  );
  return (
    <EChart
      ref={ref}
      option={option}
      aspectRatio={CHART_SIZE.PCA_ASPECT}
      ariaDescription={pcaAriaDescription(pca, CHART_TEXT.PCA_ARIA)}
    />
  );
}
