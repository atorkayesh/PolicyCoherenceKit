import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ResultsCard } from "@/components/page-specific/assessment/ResultsCard";
import { previewAggregation } from "@/services/aggregation.service";
import { runAnalysis } from "@/services/analysis.service";
import { getNetworkChartData } from "@/services/charts.service";
import { exportInterpretationPdf } from "@/services/explanation.service";
import { exportXlsx } from "@/services/export.service";
import { checkMatrices } from "@/services/matrices.service";
import { getScales } from "@/services/scales.service";
import { useProjectStore } from "@/store/project.store";
import { MAJORITY_PREVIEW } from "@/test/fixtures/aggregation.fixture";
import {
  ANALYSIS,
  ANALYSIS_PCA_INVALID,
  NETWORK_FULL,
} from "@/test/fixtures/analysis.fixture";
import {
  CHECK_COMPLETE_TWO,
  CHECK_INCOMPLETE,
  choiceOptions,
} from "@/test/fixtures/check.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";
import { renderWithQuery } from "@/test/render";
import { downloadChart } from "@/utils/chart-export.utils";
import { saveBlob } from "@/utils/download.utils";

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
  ClientOnly: ({ fallback }: { fallback: unknown }) => fallback,
}));
vi.mock("@/services/scales.service", () => ({ getScales: vi.fn() }));
vi.mock("@/services/matrices.service", () => ({ checkMatrices: vi.fn() }));
vi.mock("@/services/aggregation.service", () => ({
  previewAggregation: vi.fn(),
}));
vi.mock("@/services/analysis.service", () => ({ runAnalysis: vi.fn() }));
vi.mock("@/services/charts.service", () => ({ getNetworkChartData: vi.fn() }));
vi.mock("@/services/export.service", () => ({ exportXlsx: vi.fn() }));
vi.mock("@/services/explanation.service", () => ({
  getExplanationProviders: vi.fn(() => new Promise(() => {})),
  exportInterpretationPdf: vi.fn(),
}));
vi.mock("@/utils/download.utils", () => ({ saveBlob: vi.fn() }));
vi.mock("@/utils/chart-export.utils", () => ({ downloadChart: vi.fn() }));

const store = () => useProjectStore.getState();
const onOpen = vi.fn();

function showResults(data = ANALYSIS) {
  seedProject({ fill: "Enabling" });
  useProjectStore.setState({ snapshot: null });
  // The current answers produce REQUEST's shape; store it as the snapshot.
  store().setResults(REQUEST, data);
  return renderWithQuery(<ResultsCard onBack={vi.fn()} onOpen={onOpen} />);
}

describe("ResultsCard", () => {
  beforeEach(() => {
    store().reset();
    onOpen.mockReset();
    for (const fn of [
      checkMatrices,
      previewAggregation,
      runAnalysis,
      exportXlsx,
      saveBlob,
      downloadChart,
      exportInterpretationPdf,
    ])
      vi.mocked(fn).mockReset();
    vi.mocked(getScales).mockResolvedValue(SCALES);
    vi.mocked(getNetworkChartData).mockResolvedValue(NETWORK_FULL);
  });

  it("opens Results Insights by default and switches tabs", async () => {
    showResults();
    expect(await screen.findByText("Key Insights")).toBeDefined();
    fireEvent.click(screen.getByRole("tab", { name: "Coherence Scores" }));
    expect(
      await screen.findByRole("columnheader", { name: "WOI" }),
    ).toBeDefined();
    expect(screen.getByRole("columnheader", { name: "Policy" })).toBeDefined();
  });

  it("exports the snapshot, not the current answers", async () => {
    showResults();
    store().setProjectName("Changed");
    vi.mocked(exportXlsx).mockResolvedValue({
      blob: new Blob(["x"]),
      filename: "Nexus_coherence.xlsx",
    });
    fireEvent.click(
      await screen.findByRole("button", { name: "Export Excel" }),
    );
    await waitFor(() =>
      expect(saveBlob).toHaveBeenCalledWith(
        expect.any(Blob),
        "Nexus_coherence.xlsx",
      ),
    );
    expect(exportXlsx).toHaveBeenCalledWith(REQUEST);
    expect(
      await screen.findByText(
        "Your inputs changed since this analysis. Run again to update.",
      ),
    ).toBeDefined();
  });

  it("renders charts off-screen for PNG and SVG downloads", async () => {
    showResults();
    const png = await screen.findByRole("button", {
      name: "Save Network plot as PNG",
    });
    await waitFor(() =>
      expect((png as HTMLButtonElement).disabled).toBe(false),
    );
    fireEvent.click(png);
    await waitFor(() =>
      expect(downloadChart).toHaveBeenCalledWith(
        expect.objectContaining({ series: expect.any(Array) }),
        "png",
        "network_plot",
      ),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Save PCA plot as SVG" }),
    );
    await waitFor(() =>
      expect(downloadChart).toHaveBeenLastCalledWith(
        expect.anything(),
        "svg",
        "pca_plot",
      ),
    );
  });

  it("disables PCA downloads when PCA is invalid, and asks for an interpretation first", async () => {
    showResults(ANALYSIS_PCA_INVALID);
    const pca = (await screen.findByRole("button", {
      name: "Save PCA plot as PNG",
    })) as HTMLButtonElement;
    expect(pca.disabled).toBe(true);
    expect(pca.title).toBe("PCA requires at least 3 policies.");
    fireEvent.click(screen.getByRole("button", { name: "Download as TXT" }));
    expect(screen.getByRole("alert").textContent).toBe(
      "Nothing to SaveGenerate an interpretation first.",
    );
    act(() => store().setInterpretationText("Text"));
    fireEvent.click(screen.getByRole("button", { name: "Download as TXT" }));
    await waitFor(() =>
      expect(saveBlob).toHaveBeenCalledWith(
        expect.any(Blob),
        "policy_interpretation.txt",
      ),
    );
  });

  it("Re-run opens Review when the matrices are incomplete", async () => {
    showResults();
    store().setCell("dm-1", 0, 1, "");
    vi.mocked(checkMatrices).mockResolvedValue(CHECK_INCOMPLETE);
    fireEvent.click(await screen.findByRole("button", { name: "Re-run" }));
    await waitFor(() => expect(onOpen).toHaveBeenCalledWith("review"));
    expect(runAnalysis).not.toHaveBeenCalled();
  });

  it("Re-run opens Ties when majority ties are unresolved, else runs", async () => {
    showResults();
    store().setMethod("majority");
    vi.mocked(checkMatrices).mockResolvedValue({
      ...CHECK_COMPLETE_TWO,
      aggregation_options: choiceOptions(3),
    });
    vi.mocked(previewAggregation).mockResolvedValue(MAJORITY_PREVIEW);
    fireEvent.click(await screen.findByRole("button", { name: "Re-run" }));
    await waitFor(() => expect(onOpen).toHaveBeenCalledWith("ties"));
    store().setMethod("average");
    vi.mocked(checkMatrices).mockResolvedValue(CHECK_COMPLETE_TWO);
    vi.mocked(runAnalysis).mockResolvedValue({
      ...ANALYSIS,
      project_name: "Again",
    });
    store().setProjectName("Again");
    fireEvent.click(await screen.findByRole("button", { name: "Re-run" }));
    await waitFor(() => expect(store().results?.project_name).toBe("Again"));
    expect(store().snapshot?.project_name).toBe("Again");
  });
});
