import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { StartOverButton } from "@/components/page-specific/assessment/StartOverButton";
import { useProjectStore } from "@/store/project.store";

const navigate = vi.hoisted(() => vi.fn());
vi.mock("@tanstack/react-router", () => ({ useNavigate: () => navigate }));

const store = () => useProjectStore.getState();

describe("StartOverButton", () => {
  beforeEach(() => {
    store().reset();
    navigate.mockReset();
  });

  it("is hidden while nothing has been answered", () => {
    render(<StartOverButton />);
    expect(screen.queryByRole("button", { name: "Start over" })).toBeNull();
  });

  it("keeps everything when the dialog is cancelled", () => {
    useProjectStore.setState({ answered: ["project", "decision-makers"] });
    render(<StartOverButton />);
    fireEvent.click(screen.getByRole("button", { name: "Start over" }));
    expect(
      screen.getByText("All answers, matrices and results will be cleared."),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(store().answered).toEqual(["project", "decision-makers"]);
    expect(navigate).not.toHaveBeenCalled();
  });

  it("clears every answer and opens the first step after confirmation", () => {
    useProjectStore.setState({ answered: ["project"], projectName: "Nexus" });
    render(<StartOverButton />);
    fireEvent.click(screen.getByRole("button", { name: "Start over" }));
    const confirm = screen
      .getAllByRole("button", { name: "Start over" })
      .find((button) => button.closest("[role=alertdialog]"));
    fireEvent.click(confirm as HTMLElement);
    expect(store().answered).toEqual([]);
    expect(store().projectName).toBe("");
    expect(navigate).toHaveBeenCalledWith({ search: { step: "project" } });
  });
});

describe("StartOverButton look", () => {
  it("turns its text red on hover only, without a background", () => {
    useProjectStore.setState({ answered: ["project"] });
    render(<StartOverButton />);
    const button = screen.getByRole("button", { name: "Start over" });
    expect(button.className).toContain("hover:text-destructive");
    expect(button.className).toContain("hover:bg-transparent");
  });
});
