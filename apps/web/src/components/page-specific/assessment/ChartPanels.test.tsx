import {
  act,
  fireEvent,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import {
  afterAll,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { AggregatedPanel } from "@/components/page-specific/assessment/AggregatedPanel";
import { CoherenceScoresPanel } from "@/components/page-specific/assessment/CoherenceScoresPanel";
import { NetworkPanel } from "@/components/page-specific/assessment/NetworkPanel";
import { PcaPanel } from "@/components/page-specific/assessment/PcaPanel";
import { RangeOfInfluencePanel } from "@/components/page-specific/assessment/RangeOfInfluencePanel";
import { getNetworkChartData } from "@/services/charts.service";
import { useProjectStore } from "@/store/project.store";
import {
  ANALYSIS,
  ANALYSIS_PCA_INVALID,
  NETWORK_EGO_EMPTY,
  NETWORK_FULL,
} from "@/test/fixtures/analysis.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { renderWithQuery, stubLayout } from "@/test/render";
import { pickOption } from "@/test/select";

vi.mock("@tanstack/react-router", () => ({
  ClientOnly: ({ fallback }: { fallback: unknown }) => fallback,
}));
vi.mock("@/services/charts.service", () => ({ getNetworkChartData: vi.fn() }));

const store = () => useProjectStore.getState();

describe("table panels", () => {
  let restore: () => void;
  beforeAll(() => {
    restore = stubLayout();
  });
  afterAll(() => restore());

  it("formats coherence scores like Python and colours them by API bands", () => {
    renderWithQuery(<CoherenceScoresPanel data={ANALYSIS} />);
    const headers = screen.getAllByRole("columnheader");
    expect(headers.map((h) => h.textContent)).toEqual([
      "Code",
      "OI",
      "II",
      "WOI",
      "WII",
      "Policy",
    ]);
    expect(headers[1].getAttribute("title")).toBe(
      "Outgoing Influence\n(non-zero row count)",
    );
    const food = screen.getAllByRole("row")[3];
    const cells = within(food)
      .getAllByRole("cell")
      .map((c) => c.textContent);
    expect(cells).toEqual(["P3", "1", "0", "+0.00", "-0.00", "Food"]);
    expect(screen.getByText("-2.25").className).toContain(
      "bg-value-strong-negative",
    );
    expect(
      screen.getAllByText("2", { selector: "span" })[0].className,
    ).toContain("bg-count-very-high");
  });

  it("shows entropy with 4 decimals, categories and the fixed tooltip", () => {
    renderWithQuery(<RangeOfInfluencePanel data={ANALYSIS} scales={SCALES} />);
    expect(screen.getByText("max entropy = 1.0000")).toBeDefined();
    expect(screen.getByText("0.9183")).toBeDefined();
    expect(
      screen.getByText(/Low also covers policies with no outgoing influence\./),
    ).toBeDefined();
    expect(
      screen
        .getByRole("columnheader", { name: "Entropy" })
        .getAttribute("title"),
    ).toContain("(max = 1 with 2 policies)");
    expect(screen.getByText("H ≥ 75% of max")).toBeDefined();
  });

  it("shows aggregated scores with band colours and legacy tooltips", () => {
    renderWithQuery(<AggregatedPanel data={ANALYSIS} scales={SCALES} />);
    expect(screen.getByText("Aggregated score scale:")).toBeDefined();
    const cell = screen.getByText("-2.25");
    expect(cell.getAttribute("title")).toBe(
      "P2 → P1\nScore: -2.25\nColour band: Counteracting",
    );
    expect(cell.className).toContain("bg-rating-counteracting");
    expect(screen.getAllByText("-0.00")[0].getAttribute("title")).toBe(
      "P1 → P3\nScore: -0.00\nColour band: Neutral",
    );
    expect(screen.getAllByText("0.00")[0].getAttribute("title")).toBe(
      "P1 → P1\nScore: 0.00 (diagonal)",
    );
  });
});

describe("chart panels", () => {
  beforeEach(() => {
    store().reset();
    vi.mocked(getNetworkChartData).mockReset();
  });

  it("shows the PCA message and no chart when PCA is invalid", () => {
    renderWithQuery(<PcaPanel data={ANALYSIS_PCA_INVALID} scales={SCALES} />);
    expect(screen.getByText("PCA requires at least 3 policies.")).toBeDefined();
    expect(screen.queryByTestId("chart-skeleton")).toBeNull();
  });

  it("shows PCA stats, a clickable colour checkbox and the entropy legend", () => {
    renderWithQuery(<PcaPanel data={ANALYSIS} scales={SCALES} />);
    expect(
      screen.getByText("PC1: 62.5%   PC2: 30.1%   Total explained: 92.6%", {
        normalizer: (t) => t,
      }),
    ).toBeDefined();
    expect(screen.getByTestId("chart-skeleton")).toBeDefined();
    fireEvent.click(screen.getByText("Colour by entropy category"));
    expect(store().chartView.pcaColourByEntropy).toBe(true);
    expect(screen.getByText("Entropy categories:")).toBeDefined();
    expect(
      screen.getByText(
        "Hover over or tap a point to see the full policy name.",
      ),
    ).toBeDefined();
  });

  it("loads the network per layout and focus, with stats, legend and centrality order", async () => {
    vi.mocked(getNetworkChartData).mockImplementation(async (_, __, focus) =>
      focus === null ? NETWORK_FULL : NETWORK_EGO_EMPTY,
    );
    const { queryClient } = renderWithQuery(
      <NetworkPanel
        snapshot={REQUEST}
        snapshotHash="h1"
        data={ANALYSIS}
        scales={SCALES}
      />,
    );
    expect(
      screen.getByText("3 nodes  |  4 directed edges  |  density: 0.6667", {
        normalizer: (t) => t,
      }),
    ).toBeDefined();
    await waitFor(() =>
      expect(getNetworkChartData).toHaveBeenCalledWith(
        REQUEST,
        "force_directed",
        null,
      ),
    );
    expect(
      screen
        .getAllByRole("row")
        .slice(1)
        .map((r) => within(r).getAllByRole("cell")[0].textContent),
    ).toEqual(["P2", "P1", "P3"]);
    expect(
      screen
        .getByRole("button", { name: "Negative" })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: "Negative" }));
    expect(
      screen
        .getByRole("button", { name: "Negative" })
        .getAttribute("aria-pressed"),
    ).toBe("false");
    await pickOption(
      screen.getByRole("combobox", { name: "Layout" }),
      "Circular",
    );
    await waitFor(() =>
      expect(getNetworkChartData).toHaveBeenLastCalledWith(
        REQUEST,
        "circular",
        null,
      ),
    );
    await pickOption(
      screen.getByRole("combobox", { name: "Focus policy" }),
      "P3: Food",
    );
    await waitFor(() =>
      expect(getNetworkChartData).toHaveBeenLastCalledWith(
        REQUEST,
        "circular",
        2,
      ),
    );
    expect(
      await screen.findByText("P3 has no direct connections."),
    ).toBeDefined();
    expect(
      queryClient.getQueryData(["network-chart", "h1", "circular", 2]),
    ).toEqual(NETWORK_EGO_EMPTY);
    act(() => store().setChartView({ networkFocus: null }));
  });

  it("shows the network error inline", async () => {
    vi.mocked(getNetworkChartData).mockRejectedValue(
      new Error("Layout failed"),
    );
    renderWithQuery(
      <NetworkPanel
        snapshot={REQUEST}
        snapshotHash="h2"
        data={ANALYSIS}
        scales={SCALES}
      />,
    );
    expect(screen.getByText("Loading the network…")).toBeDefined();
    expect((await screen.findByRole("alert")).textContent).toBe(
      "Layout failed",
    );
  });
});
