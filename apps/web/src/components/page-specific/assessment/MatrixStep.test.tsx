import { fireEvent, screen } from "@testing-library/react";
import {
  afterAll,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { MatrixStep } from "@/components/page-specific/assessment/MatrixStep";
import { useProjectStore } from "@/store/project.store";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";
import { renderWithQuery, stubLayout } from "@/test/render";
import { pickOption } from "@/test/select";

const store = () => useProjectStore.getState();
const nav = () => ({
  number: 5,
  onAdvance: vi.fn(),
  onBack: vi.fn(),
  onOpen: vi.fn(),
  isLast: false,
});
const cell = (name: string) => screen.getByRole("combobox", { name });

describe("MatrixStep", () => {
  let restore: () => void;
  beforeAll(() => {
    restore = stubLayout();
  });
  afterAll(() => restore());
  beforeEach(() => store().reset());

  it("shows the title, legend, progress, codes and a fixed diagonal", () => {
    seedProject();
    renderWithQuery(<MatrixStep index={1} scales={SCALES} {...nav()} />);
    expect(screen.getByRole("heading").textContent).toBe(
      "Decision-maker 2 of 2: Bob",
    );
    expect(screen.getByText("Click a cell to rate it:")).toBeDefined();
    expect(screen.getByText("0/6 cells filled")).toBeDefined();
    expect(screen.getByText("Row → Column")).toBeDefined();
    expect(
      screen.getByText("P2", { selector: "div" }).getAttribute("title"),
    ).toBe("P2:  Water");
    const diagonal = cell("P1 Energy → P1 Energy") as HTMLButtonElement;
    expect(
      diagonal.disabled || diagonal.getAttribute("data-disabled") !== null,
    ).toBe(true);
    expect(diagonal.textContent).toContain("Neutral");
    const first = cell("P1 Energy → P2 Water");
    expect(first.textContent).toContain("--");
    expect(document.activeElement).toBe(first);
  });

  it("rates, clears with the option and with Delete, and counts filled cells", async () => {
    seedProject();
    renderWithQuery(<MatrixStep index={0} scales={SCALES} {...nav()} />);
    await pickOption(cell("P1 Energy → P2 Water"), "Reinforcing");
    expect(store().matrices["dm-1"][0][1]).toBe("Reinforcing");
    expect(screen.getByText("1/6 cells filled")).toBeDefined();
    expect(cell("P1 Energy → P2 Water").className).toContain(
      "bg-rating-reinforcing",
    );
    await pickOption(cell("P1 Energy → P2 Water"), "Clear rating");
    expect(store().matrices["dm-1"][0][1]).toBe("");
    await pickOption(cell("P2 Water → P1 Energy"), "Cancelling");
    fireEvent.keyDown(cell("P2 Water → P1 Energy"), { key: "Delete" });
    expect(store().matrices["dm-1"][1][0]).toBe("");
    expect(store().matrices["dm-2"][1][0]).toBe("");
  });

  it("does not advance on Enter inside a cell, but OK marks the matrix answered", () => {
    seedProject();
    const props = nav();
    renderWithQuery(<MatrixStep index={0} scales={SCALES} {...props} />);
    fireEvent.keyDown(cell("P1 Energy → P2 Water"), { key: "Enter" });
    expect(props.onAdvance).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(props.onAdvance).toHaveBeenCalled();
  });

  it("re-renders only the changed cell", async () => {
    seedProject();
    renderWithQuery(<MatrixStep index={0} scales={SCALES} {...nav()} />);
    const other = cell("P3 Food → P1 Energy");
    await pickOption(cell("P1 Energy → P2 Water"), "Enabling");
    expect(cell("P3 Food → P1 Energy")).toBe(other);
  });
});
