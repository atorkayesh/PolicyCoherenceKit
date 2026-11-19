import { useMemo } from "react";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";
import type { PcaColours } from "@/utils/pca-chart.utils";

/** The network layout and focus of the Results screen (default layout from `/scales`). */
export function useNetworkView(scales: ScalesData) {
  const view = useProjectStore((state) => state.chartView);
  return {
    layout: view.networkLayout ?? scales.network.default_layout,
    focus: view.networkFocus,
  };
}

/** PCA colours from `/scales` (points, labels, entropy categories). */
export function usePcaColours(scales: ScalesData): PcaColours {
  return useMemo(
    () => ({
      pointColour: scales.pca.point_colour,
      textColour: scales.network.node_text_colour,
      categories: scales.entropy_categories,
    }),
    [scales],
  );
}
