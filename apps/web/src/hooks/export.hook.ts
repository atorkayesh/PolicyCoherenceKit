import { useMutation } from "@tanstack/react-query";
import type { EChartsOption } from "echarts";
import { INTERPRETATION_FILES } from "@/constants/explanation.constants";
import { MUTATION_KEYS } from "@/constants/query.constants";
import { EXPORT_FILES } from "@/constants/results.constants";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import { exportInterpretationPdf } from "@/services/explanation.service";
import { exportXlsx } from "@/services/export.service";
import { type ChartFileKind, downloadChart } from "@/utils/chart-export.utils";
import { saveBlob } from "@/utils/download.utils";

/** The downloads of the export bar. */
export type ExportKind =
  | "xlsx"
  | "network-png"
  | "network-svg"
  | "pca-png"
  | "pca-svg"
  | "txt"
  | "pdf";

/** What an export needs besides the snapshot: chart options and the interpretation text. */
export interface ExportSources {
  networkOption: () => EChartsOption | null;
  pcaOption: () => EChartsOption | null;
  interpretationText: string;
}

async function chart(
  build: () => EChartsOption | null,
  kind: ChartFileKind,
  base: string,
) {
  const option = build();
  if (option) await downloadChart(option, kind, base);
}

/** Download one export of the results snapshot under the legacy file name. */
export function useExportFile(
  snapshot: AnalysisRequest,
  sources: ExportSources,
) {
  return useMutation({
    mutationKey: MUTATION_KEYS.EXPORT_FILE,
    mutationFn: async (kind: ExportKind) => {
      switch (kind) {
        case "xlsx": {
          const file = await exportXlsx(snapshot);
          saveBlob(file.blob, file.filename);
          return;
        }
        case "network-png":
          return chart(sources.networkOption, "png", EXPORT_FILES.NETWORK);
        case "network-svg":
          return chart(sources.networkOption, "svg", EXPORT_FILES.NETWORK);
        case "pca-png":
          return chart(sources.pcaOption, "png", EXPORT_FILES.PCA);
        case "pca-svg":
          return chart(sources.pcaOption, "svg", EXPORT_FILES.PCA);
        case "txt":
          saveBlob(
            new Blob([sources.interpretationText], {
              type: "text/plain;charset=utf-8",
            }),
            INTERPRETATION_FILES.TXT,
          );
          return;
        case "pdf": {
          const file = await exportInterpretationPdf(
            sources.interpretationText,
          );
          saveBlob(file.blob, file.filename);
          return;
        }
      }
    },
  });
}
