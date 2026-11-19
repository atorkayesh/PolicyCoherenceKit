import { useState } from "react";
import { DownloadButton } from "@/components/general/DownloadButton";
import { InlineError } from "@/components/general/InlineError";
import { EXPORT_TEXT } from "@/constants/results.constants";
import { useNetworkView, usePcaColours } from "@/hooks/chart-view.hook";
import { type ExportKind, useExportFile } from "@/hooks/export.hook";
import { useNetworkChartData } from "@/hooks/network-chart.hook";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";
import { errorMessage } from "@/utils/api.utils";
import { buildChartTheme } from "@/utils/chart-theme.utils";
import { buildNetworkOption } from "@/utils/network-chart.utils";
import { buildPcaOption } from "@/utils/pca-chart.utils";

const BUTTONS: readonly { kind: ExportKind; label: string }[] = [
  { kind: "xlsx", label: EXPORT_TEXT.XLSX },
  { kind: "network-png", label: EXPORT_TEXT.NETWORK_PNG },
  { kind: "network-svg", label: EXPORT_TEXT.NETWORK_SVG },
  { kind: "pca-png", label: EXPORT_TEXT.PCA_PNG },
  { kind: "pca-svg", label: EXPORT_TEXT.PCA_SVG },
  { kind: "txt", label: EXPORT_TEXT.TXT },
  { kind: "pdf", label: EXPORT_TEXT.PDF },
];

/**
 * Downloads of the results snapshot from any tab: XLSX and the interpretation PDF from the API;
 * network and PCA PNG/SVG rendered off-screen in the browser from the API's chart data (current
 * layout, focus and colour mode); the interpretation TXT in the browser.
 */
export function ExportBar({
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
  const network = useNetworkChartData(snapshot, snapshotHash, layout, focus);
  const colourByEntropy = useProjectStore(
    (state) => state.chartView.pcaColourByEntropy,
  );
  const interpretationText = useProjectStore(
    (state) => state.interpretationText,
  );
  const pcaColours = usePcaColours(scales);
  const [notice, setNotice] = useState<string | null>(null);
  const exportFile = useExportFile(snapshot, {
    networkOption: () =>
      network.data
        ? buildNetworkOption(network.data, scales.network, buildChartTheme())
        : null,
    pcaOption: () =>
      data.pca.valid
        ? buildPcaOption(
            data.pca,
            pcaColours,
            colourByEntropy,
            buildChartTheme(),
          )
        : null,
    interpretationText,
  });

  const disabledReason = (kind: ExportKind): string | undefined => {
    if (kind.startsWith("pca") && !data.pca.valid)
      return data.pca.message ?? undefined;
    return undefined;
  };
  const isDisabled = (kind: ExportKind) =>
    (kind.startsWith("network") && !network.data) ||
    (kind.startsWith("pca") && !data.pca.valid);

  const download = (kind: ExportKind) => {
    setNotice(null);
    exportFile.reset();
    if ((kind === "txt" || kind === "pdf") && !interpretationText.trim()) {
      setNotice(EXPORT_TEXT.NOTHING_TO_SAVE);
      return;
    }
    exportFile.mutate(kind);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        {BUTTONS.map((button) => (
          <DownloadButton
            key={button.kind}
            label={button.label}
            pending={
              exportFile.isPending && exportFile.variables === button.kind
            }
            disabled={isDisabled(button.kind)}
            title={disabledReason(button.kind)}
            onClick={() => download(button.kind)}
          />
        ))}
      </div>
      <InlineError
        title={notice ? EXPORT_TEXT.NOTHING_TO_SAVE_TITLE : null}
        message={
          notice ?? (exportFile.error ? errorMessage(exportFile.error) : null)
        }
      />
    </div>
  );
}
