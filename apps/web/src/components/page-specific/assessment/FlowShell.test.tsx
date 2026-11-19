import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FlowShell } from "@/components/page-specific/assessment/FlowShell";
import { checkMatrices } from "@/services/matrices.service";
import { getScales } from "@/services/scales.service";
import { validateSetup } from "@/services/setup.service";
import { useProjectStore } from "@/store/project.store";
import { ANALYSIS } from "@/test/fixtures/analysis.fixture";
import { CHECK_COMPLETE_TWO } from "@/test/fixtures/check.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";
import { renderWithQuery } from "@/test/render";

const router = vi.hoisted(() => ({
  search: {} as { step?: string },
  navigate: vi.fn(),
}));
vi.mock("@tanstack/react-router", () => ({
  useSearch: () => router.search,
  useNavigate: () => router.navigate,
  ClientOnly: ({ fallback }: { fallback: unknown }) => fallback,
  Navigate: ({ search }: { search: { step: string } }) => (
    <p>redirect:{search.step}</p>
  ),
}));
vi.mock("@/services/scales.service", () => ({ getScales: vi.fn() }));
vi.mock("@/services/setup.service", () => ({ validateSetup: vi.fn() }));
vi.mock("@/services/matrices.service", () => ({
  checkMatrices: vi.fn(() => new Promise(() => {})),
}));
vi.mock("@/services/charts.service", () => ({
  getNetworkChartData: vi.fn(() => new Promise(() => {})),
}));
vi.mock("@/services/explanation.service", () => ({
  getExplanationProviders: vi.fn(() => new Promise(() => {})),
}));

const store = () => useProjectStore.getState();
function openStep(step: string) {
  router.search = { step };
  return renderWithQuery(<FlowShell />);
}

describe("FlowShell", () => {
  beforeEach(() => {
    store().reset();
    router.navigate.mockReset();
    vi.mocked(getScales).mockReset().mockResolvedValue(SCALES);
    vi.mocked(checkMatrices)
      .mockReset()
      .mockImplementation(() => new Promise(() => {}));
  });

  it("shows loading, then an error with Try again", async () => {
    vi.mocked(getScales).mockRejectedValue(new Error("down"));
    openStep("project");
    expect(screen.getByText("Loading the assessment options…")).toBeDefined();
    expect(
      await screen.findByText(
        "The assessment options could not be loaded from the API.",
      ),
    ).toBeDefined();
    expect(screen.getByRole("button", { name: "Try again" })).toBeDefined();
  });

  it("redirects without a step to the first question", async () => {
    openStep("");
    expect(await screen.findByText("redirect:project")).toBeDefined();
  });

  it("redirects to the first unanswered step when earlier steps are missing", async () => {
    seedProject({
      answered: ["project", "decision-makers"],
      matricesAnswered: false,
    });
    openStep("matrix-2");
    expect(await screen.findByText("redirect:policies")).toBeDefined();
  });

  it("opens Results only with results", async () => {
    openStep("results");
    expect(await screen.findByText("redirect:project")).toBeDefined();
  });

  it("continues with Enter and goes back with Shift+Enter", async () => {
    vi.mocked(validateSetup).mockResolvedValue({ decision_makers: ["Alice"] });
    store().markAnswered("project");
    openStep("decision-makers");
    const input = (await screen.findAllByRole("textbox"))[0];
    fireEvent.change(input, { target: { value: "Alice" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(router.navigate).toHaveBeenLastCalledWith({
      search: { step: "project" },
    });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() =>
      expect(router.navigate).toHaveBeenLastCalledWith({
        search: { step: "policies" },
      }),
    );
    expect(store().answered).toContain("decision-makers");
  });

  it("starts Review on OK so Enter continues to Method, not an Edit link", async () => {
    seedProject({ fill: "Enabling" });
    vi.mocked(checkMatrices).mockResolvedValue(CHECK_COMPLETE_TWO);
    openStep("review");
    const ok = await screen.findByRole("button", { name: "OK" });
    await waitFor(() => expect(document.activeElement).toBe(ok));
    // A focused button handles Enter natively (a click), so emulate the browser.
    fireEvent.keyDown(ok, { key: "Enter" });
    fireEvent.click(ok);
    await waitFor(() =>
      expect(router.navigate).toHaveBeenLastCalledWith({
        search: { step: "method" },
      }),
    );
    expect(router.navigate).not.toHaveBeenCalledWith({
      search: { step: "project" },
    });
  });

  it("lists the steps, opens answered ones and shows progress", async () => {
    seedProject();
    openStep("matrix-1");
    const list = await screen.findByRole("navigation", { name: "Steps" });
    expect(list.textContent).toContain("Matrix 2");
    fireEvent.click(screen.getByRole("button", { name: /Policies/ }));
    expect(router.navigate).toHaveBeenCalledWith({
      search: { step: "policies" },
    });
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "50",
    );
  });

  it("shows Results with the subtitle, forced note and seven tabs", async () => {
    seedProject({ fill: "Enabling" });
    store().setResults(REQUEST, ANALYSIS);
    openStep("results");
    expect(
      await screen.findByText(
        'Analysis complete for "Nexus"  |  method: Average  |  2 decision-makers',
        {
          normalizer: (text) => text,
        },
      ),
    ).toBeDefined();
    expect(
      screen.getByText(
        "Fewer than 3 decision-makers: the ratings were combined with Average.",
      ),
    ).toBeDefined();
    expect(screen.getAllByRole("tab").map((tab) => tab.textContent)).toEqual([
      "Results Insights",
      "Aggregated",
      "Coherence Scores",
      "Range of Influence",
      "PCA",
      "Network Analysis",
      "AI Interpretation",
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Back to inputs" }));
    expect(router.navigate).toHaveBeenCalledWith({
      search: { step: "review" },
    });
  });
});
