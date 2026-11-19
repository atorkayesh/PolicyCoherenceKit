import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReviewStep } from "@/components/page-specific/assessment/ReviewStep";
import { checkMatrices } from "@/services/matrices.service";
import { getScales } from "@/services/scales.service";
import { useProjectStore } from "@/store/project.store";
import {
  CHECK_COMPLETE_TWO,
  CHECK_INCOMPLETE,
} from "@/test/fixtures/check.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";
import { renderWithQuery } from "@/test/render";

vi.mock("@/services/scales.service", () => ({ getScales: vi.fn() }));
vi.mock("@/services/matrices.service", () => ({ checkMatrices: vi.fn() }));

const store = () => useProjectStore.getState();
const nav = () => ({
  number: 7,
  onAdvance: vi.fn(),
  onBack: vi.fn(),
  onOpen: vi.fn(),
  isLast: false,
});

describe("ReviewStep", () => {
  beforeEach(() => {
    store().reset();
    vi.mocked(getScales).mockResolvedValue(SCALES);
    vi.mocked(checkMatrices).mockReset();
  });

  it("lists every answer with Edit links and the API's blank cells", async () => {
    seedProject({ dms: ["Alice"], policies: ["A", "B", "C", "D", "E"] });
    vi.mocked(checkMatrices).mockResolvedValue(CHECK_INCOMPLETE);
    const props = nav();
    renderWithQuery(<ReviewStep {...props} />);
    expect(screen.getByText("P1: A, P2: B, P3: C, P4: D, P5: E")).toBeDefined();
    expect(screen.getByText("Rated in the browser")).toBeDefined();
    expect(
      await screen.findByText(
        /12 blank cells: P1 → P2, P1 → P3, .*P1 → P11 \(\+2 more\)/,
      ),
    ).toBeDefined();
    expect(screen.getByText(/8\/20 cells filled/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Edit Matrix: Alice" }));
    expect(props.onOpen).toHaveBeenCalledWith("matrix-1");
    fireEvent.click(screen.getByRole("button", { name: "Edit Policies" }));
    expect(props.onOpen).toHaveBeenCalledWith("policies");
  });

  it("blocks on incomplete matrices with the API message", async () => {
    seedProject({ dms: ["Alice"] });
    vi.mocked(checkMatrices).mockResolvedValue(CHECK_INCOMPLETE);
    const props = nav();
    renderWithQuery(<ReviewStep {...props} />);
    fireEvent.click(await screen.findByRole("button", { name: "OK" }));
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Incomplete Matrices");
    expect(alert.textContent).toContain("Alice: P1 → P2, P1 → P3");
    expect(props.onAdvance).not.toHaveBeenCalled();
  });

  it("stores the aggregation options for the current names and moves on", async () => {
    seedProject({ fill: "Enabling" });
    vi.mocked(checkMatrices).mockResolvedValue(CHECK_COMPLETE_TWO);
    const props = nav();
    renderWithQuery(<ReviewStep {...props} />);
    fireEvent.click(await screen.findByRole("button", { name: "OK" }));
    await waitFor(() => expect(props.onAdvance).toHaveBeenCalled());
    expect(store().aggregationOptions).toMatchObject({
      method_choice_available: false,
      forNames: "Alice\nBob",
    });
  });
});
