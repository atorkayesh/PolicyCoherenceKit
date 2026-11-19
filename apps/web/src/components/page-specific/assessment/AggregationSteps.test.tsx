import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MedianStep } from "@/components/page-specific/assessment/MedianStep";
import { MethodStep } from "@/components/page-specific/assessment/MethodStep";
import { TiesStep } from "@/components/page-specific/assessment/TiesStep";
import { WeightsStep } from "@/components/page-specific/assessment/WeightsStep";
import { previewAggregation } from "@/services/aggregation.service";
import { runAnalysis } from "@/services/analysis.service";
import { checkMatrices } from "@/services/matrices.service";
import { getScales } from "@/services/scales.service";
import { checkWeights } from "@/services/weights.service";
import { useProjectStore } from "@/store/project.store";
import {
  MAJORITY_PREVIEW,
  PREVIEW_NO_TIES,
} from "@/test/fixtures/aggregation.fixture";
import { ANALYSIS } from "@/test/fixtures/analysis.fixture";
import {
  CHECK_COMPLETE_TWO,
  choiceOptions,
} from "@/test/fixtures/check.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";
import { renderWithQuery } from "@/test/render";
import { pickOption } from "@/test/select";
import { ApiError } from "@/utils/api.utils";

vi.mock("@/services/scales.service", () => ({ getScales: vi.fn() }));
vi.mock("@/services/matrices.service", () => ({ checkMatrices: vi.fn() }));
vi.mock("@/services/aggregation.service", () => ({
  previewAggregation: vi.fn(),
}));
vi.mock("@/services/analysis.service", () => ({ runAnalysis: vi.fn() }));
vi.mock("@/services/weights.service", () => ({ checkWeights: vi.fn() }));

const store = () => useProjectStore.getState();
const nav = () => ({
  number: 8,
  onAdvance: vi.fn(),
  onBack: vi.fn(),
  onOpen: vi.fn(),
  isLast: true,
});
const FOUR = ["A", "B", "C", "D"];
const withOptions = (n: number) =>
  store().setAggregationOptions({
    ...choiceOptions(n),
    forNames: FOUR.slice(0, n).join("\n"),
  });

describe("aggregation steps", () => {
  beforeEach(() => {
    store().reset();
    for (const fn of [
      getScales,
      checkMatrices,
      previewAggregation,
      runAnalysis,
      checkWeights,
    ])
      vi.mocked(fn).mockReset();
    vi.mocked(getScales).mockResolvedValue(SCALES);
    vi.mocked(runAnalysis).mockResolvedValue(ANALYSIS);
  });

  it("explains the forced method with 2 decision-makers and runs", async () => {
    seedProject({ fill: "Enabling" });
    vi.mocked(checkMatrices).mockResolvedValue(CHECK_COMPLETE_TWO);
    const props = nav();
    renderWithQuery(<MethodStep scales={SCALES} {...props} />);
    expect(
      await screen.findByText("2 decision-makers detected."),
    ).toBeDefined();
    expect(
      screen.getByText(
        "With fewer than 3 decision-makers, the ratings are combined with Average. Choosing a method needs at least 3 decision-makers.",
      ),
    ).toBeDefined();
    expect(screen.queryByRole("radiogroup")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Run Analysis" }));
    await waitFor(() => expect(props.onOpen).toHaveBeenCalledWith("results"));
    expect(store().results).toBe(ANALYSIS);
    expect(store().answered).toContain("method");
  });

  it("offers the methods with 4 decision-makers; Weighted continues with OK", async () => {
    seedProject({ dms: FOUR, fill: "Enabling" });
    withOptions(4);
    const props = nav();
    renderWithQuery(<MethodStep scales={SCALES} {...props} />);
    expect(
      screen.getByText(
        "4 decision-makers detected — choose how to combine their ratings.",
      ),
    ).toBeDefined();
    fireEvent.keyDown(screen.getByRole("radiogroup"), { key: "d" });
    expect(store().method).toBe("weighted");
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(props.onAdvance).toHaveBeenCalled();
  });

  it("previews Majority and opens Ties only when there are ties", async () => {
    seedProject({ dms: FOUR.slice(0, 3), fill: "Enabling" });
    withOptions(3);
    store().setMethod("majority");
    vi.mocked(previewAggregation).mockResolvedValueOnce(MAJORITY_PREVIEW);
    const props = nav();
    renderWithQuery(<MethodStep scales={SCALES} {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "Run Analysis" }));
    await waitFor(() => expect(props.onAdvance).toHaveBeenCalled());
    expect(store().tieCount).toBe(2);
    expect(
      vi.mocked(previewAggregation).mock.calls[0][0].aggregation.tie_choices,
    ).toEqual([]);
  });

  it("shows the median step help and runs with the default choice", async () => {
    seedProject({ dms: FOUR, fill: "Enabling" });
    store().setMethod("median");
    const props = nav();
    renderWithQuery(<MedianStep scales={SCALES} {...props} />);
    expect(
      screen.getByText(
        "4 decision-makers detected. Choose which median should be used for aggregation.",
      ),
    ).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Run Analysis" }));
    await waitFor(() => expect(runAnalysis).toHaveBeenCalled());
    expect(
      vi.mocked(runAnalysis).mock.calls[0][0].aggregation.median_choice,
    ).toBe("lower");
  });

  it("shows the live sum and focuses the first invalid weight", async () => {
    seedProject({ dms: ["A", "B", "C"], fill: "Enabling" });
    store().setMethod("weighted");
    vi.mocked(checkWeights).mockResolvedValue({
      total: 0.9,
      sum_text: "Sum: 0.9",
      within_tolerance: false,
      valid: false,
      weights: [0.5, 0.4, null],
      errors: [],
      first_error: {
        index: 2,
        decision_maker: "C",
        title: "Missing Weight",
        message: 'Please enter a weight for "C".',
      },
    });
    renderWithQuery(<WeightsStep scales={SCALES} {...nav()} />);
    expect(
      screen.getByText(
        "Enter a value between 0.0 and 1.0 for each decision-maker. Weights must sum to 1.0 (±0.01).",
      ),
    ).toBeDefined();
    const sum = await screen.findByText("Sum: 0.9");
    expect(sum.className).toContain("text-destructive");
    fireEvent.change(screen.getByLabelText("A"), { target: { value: "0.5" } });
    expect(store().weightTexts["dm-1"]).toBe("0.5");
    fireEvent.click(screen.getByRole("button", { name: "Run Analysis" }));
    expect((await screen.findByRole("alert")).textContent).toBe(
      'Missing WeightPlease enter a weight for "C".',
    );
    expect(document.activeElement).toBe(screen.getByLabelText("C"));
  });

  it("stores valid weights by id and runs", async () => {
    seedProject({ dms: ["A", "B"], fill: "Enabling" });
    store().setMethod("weighted");
    vi.mocked(checkWeights).mockResolvedValue({
      total: 1,
      sum_text: "Sum: 1.0",
      within_tolerance: true,
      valid: true,
      weights: [0.4, 0.6],
      errors: [],
      first_error: null,
    });
    const props = nav();
    renderWithQuery(<WeightsStep scales={SCALES} {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "Run Analysis" }));
    await waitFor(() => expect(props.onOpen).toHaveBeenCalledWith("results"));
    expect(store().weights).toEqual({ "dm-1": 0.4, "dm-2": 0.6 });
    expect(vi.mocked(runAnalysis).mock.calls[0][0].aggregation.weights).toEqual(
      [0.4, 0.6],
    );
  });

  it("renders ties with options and votes, and links run errors to Ties", async () => {
    seedProject({ dms: ["A", "B", "C", "D", "E"], fill: "Enabling" });
    store().setMethod("majority");
    vi.mocked(previewAggregation).mockResolvedValue(MAJORITY_PREVIEW);
    vi.mocked(runAnalysis).mockRejectedValueOnce(
      new ApiError(
        "Please select a rating for cell P2 → P3.",
        422,
        "unresolved_tie",
      ),
    );
    const props = nav();
    renderWithQuery(<TiesStep scales={SCALES} {...props} />);
    expect(
      await screen.findByText(
        "2 cell(s) ended in a tie. Please select the rating for each one.",
      ),
    ).toBeDefined();
    expect(screen.getByText("P1 → P2")).toBeDefined();
    expect(screen.getByText("Energy → Water")).toBeDefined();
    expect(
      screen.getAllByText(
        (_, el) =>
          el?.tagName === "P" &&
          el.textContent === "Tied options: Reinforcing (+2)  |  Enabling (+1)",
      ),
    ).toHaveLength(1);
    expect(screen.getByText(/A: Reinforcing, B: Enabling/)).toBeDefined();
    await pickOption(
      screen.getAllByRole("combobox", { name: "Selected rating" })[0],
      "Enabling",
    );
    expect(store().tieChoices["p-1>p-2"]).toBe("Enabling");
    fireEvent.click(screen.getByRole("button", { name: "Run Analysis" }));
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Please select a rating for cell P2 → P3.",
    );
    fireEvent.click(screen.getByRole("button", { name: "Ties" }));
    expect(props.onOpen).toHaveBeenCalledWith("ties");
    expect(
      vi.mocked(runAnalysis).mock.calls[0][0].aggregation.tie_choices,
    ).toEqual([{ row: 0, col: 1, rating: "Enabling" }]);
  });

  it("says when no ties remain", async () => {
    seedProject({ dms: ["A", "B", "C"], fill: "Enabling" });
    store().setMethod("majority");
    vi.mocked(previewAggregation).mockResolvedValue(PREVIEW_NO_TIES);
    renderWithQuery(<TiesStep scales={SCALES} {...nav()} />);
    expect(await screen.findByText("No ties remain.")).toBeDefined();
  });
});
