import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DecisionMakersStep } from "@/components/page-specific/assessment/DecisionMakersStep";
import { PoliciesStep } from "@/components/page-specific/assessment/PoliciesStep";
import { ProjectStep } from "@/components/page-specific/assessment/ProjectStep";
import { validateSetup } from "@/services/setup.service";
import { useProjectStore } from "@/store/project.store";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";
import { renderWithQuery } from "@/test/render";
import { ApiError } from "@/utils/api.utils";

vi.mock("@tanstack/react-router", () => ({ useNavigate: () => vi.fn() }));
vi.mock("@/services/setup.service", () => ({ validateSetup: vi.fn() }));
vi.mock("@/services/import.service", () => ({ importWorkbook: vi.fn() }));

const store = () => useProjectStore.getState();
const nav = () => ({
  number: 1,
  onAdvance: vi.fn(),
  onBack: vi.fn(),
  onOpen: vi.fn(),
  isLast: false,
});
const legacyError = (title: string, message: string) =>
  new ApiError(message, 422, "invalid_setup", { title });

describe("ProjectStep", () => {
  beforeEach(() => {
    store().reset();
    vi.mocked(validateSetup).mockReset();
  });

  it("shows the legacy texts and commits the API's trimmed name", async () => {
    vi.mocked(validateSetup).mockResolvedValue({ project_name: "Nexus" });
    const props = nav();
    renderWithQuery(<ProjectStep scales={SCALES} {...props} />);
    expect(
      screen.getByText("Start a new policy coherence assessment"),
    ).toBeDefined();
    expect(screen.getByRole("heading").textContent).toBe(
      "What is this project called?",
    );
    const input = screen.getByLabelText("Project Name");
    expect(input.getAttribute("placeholder")).toBe(
      "e.g. EU Clean Mobility Policy Coherence Assessment",
    );
    expect(document.activeElement).toBe(input);
    fireEvent.change(input, { target: { value: "  Nexus " } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(props.onAdvance).toHaveBeenCalled());
    expect(validateSetup).toHaveBeenCalledWith(
      { project_name: "  Nexus " },
      expect.anything(),
    );
    expect(store().projectName).toBe("Nexus");
  });

  it("shows the legacy title and message inline", async () => {
    vi.mocked(validateSetup).mockRejectedValue(
      legacyError("Project Name Required", "Please enter a project name."),
    );
    const props = nav();
    renderWithQuery(<ProjectStep scales={SCALES} {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe(
      "Project Name RequiredPlease enter a project name.",
    );
    expect(props.onAdvance).not.toHaveBeenCalled();
    expect(screen.getByTestId("workbook-input").getAttribute("accept")).toBe(
      ".xlsx",
    );
  });
});

describe("DecisionMakersStep", () => {
  beforeEach(() => {
    store().reset();
    vi.mocked(validateSetup).mockReset();
  });

  it("starts with two rows and the legacy placeholders; Add focuses a new row", () => {
    renderWithQuery(<DecisionMakersStep scales={SCALES} {...nav()} />);
    const rows = screen.getAllByRole("textbox");
    expect(rows.map((row) => row.getAttribute("placeholder"))).toEqual([
      "e.g. Expert A",
      "e.g. Expert B",
    ]);
    expect(screen.queryByRole("button", { name: /Remove row/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    const third = screen.getAllByRole("textbox")[2];
    expect(third.getAttribute("placeholder")).toBe("e.g. Expert C");
    expect(document.activeElement).toBe(third);
    expect(screen.getByRole("button", { name: "Remove row 3" })).toBeDefined();
  });

  it("disables Add at the limit from /scales", () => {
    const scales = {
      ...SCALES,
      rules: { ...SCALES.rules, max_decision_makers: 2 },
    };
    renderWithQuery(<DecisionMakersStep scales={scales} {...nav()} />);
    expect(
      (screen.getByRole("button", { name: "Add" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });

  it("commits new decision-makers with blank matrices, ignoring empty rows", async () => {
    vi.mocked(validateSetup).mockResolvedValue({ decision_makers: ["Alice"] });
    const props = nav();
    renderWithQuery(<DecisionMakersStep scales={SCALES} {...props} />);
    fireEvent.change(screen.getAllByRole("textbox")[0], {
      target: { value: "Alice " },
    });
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    await waitFor(() => expect(props.onAdvance).toHaveBeenCalled());
    expect(validateSetup).toHaveBeenCalledWith(
      { decision_makers: ["Alice "] },
      expect.anything(),
    );
    expect(store().decisionMakers.map((dm) => dm.name)).toEqual(["Alice"]);
  });

  it("shows duplicate errors and discards the draft on Back", async () => {
    vi.mocked(validateSetup).mockRejectedValue(
      legacyError(
        "Duplicate Decision-Makers",
        "Decision-maker names must be unique.",
      ),
    );
    const props = nav();
    renderWithQuery(<DecisionMakersStep scales={SCALES} {...props} />);
    fireEvent.change(screen.getAllByRole("textbox")[0], {
      target: { value: "A" },
    });
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Duplicate Decision-Makers",
    );
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(props.onBack).toHaveBeenCalled();
    expect(store().decisionMakers).toEqual([]);
  });

  it("asks before removing a rated decision-maker; Cancel keeps everything", async () => {
    seedProject({ fill: "Enabling" });
    vi.mocked(validateSetup).mockResolvedValue({ decision_makers: ["Bob"] });
    const props = nav();
    renderWithQuery(<DecisionMakersStep scales={SCALES} {...props} />);
    fireEvent.change(screen.getAllByRole("textbox")[0], {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(
      await screen.findByText(
        "The removed decision-makers have ratings that will be lost. Continue?",
      ),
    ).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(store().decisionMakers).toHaveLength(2);
    expect(props.onAdvance).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    fireEvent.click(await screen.findByRole("button", { name: "Continue" }));
    expect(store().decisionMakers.map((dm) => dm.id)).toEqual(["dm-2"]);
    expect(props.onAdvance).toHaveBeenCalled();
  });
});

describe("PoliciesStep", () => {
  beforeEach(() => {
    store().reset();
    vi.mocked(validateSetup).mockReset();
  });

  it("commits policies with the API's codes and remaps matrices", async () => {
    seedProject({ policies: ["Energy", "Water"], fill: "Enabling" });
    vi.mocked(validateSetup).mockResolvedValue({
      policies: ["Energy", "Water", "Food"],
      codes: ["P1", "P2", "P3"],
    });
    const props = nav();
    renderWithQuery(<PoliciesStep scales={SCALES} {...props} />);
    expect(screen.getByRole("heading").textContent).toBe(
      "Which policies are you assessing?",
    );
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    fireEvent.change(screen.getAllByRole("textbox")[2], {
      target: { value: "Food" },
    });
    expect(screen.getAllByRole("textbox")[2].getAttribute("placeholder")).toBe(
      "e.g. Policy 3",
    );
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    await waitFor(() => expect(props.onAdvance).toHaveBeenCalled());
    expect(store().codes).toEqual(["P1", "P2", "P3"]);
    expect(store().matrices["dm-1"][0]).toEqual(["Neutral", "Enabling", ""]);
  });

  it("shows Too Few Policies inline", async () => {
    vi.mocked(validateSetup).mockRejectedValue(
      legacyError("Too Few Policies", "Please enter at least 2 policy names."),
    );
    renderWithQuery(<PoliciesStep scales={SCALES} {...nav()} />);
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect((await screen.findByRole("alert")).textContent).toBe(
      "Too Few PoliciesPlease enter at least 2 policy names.",
    );
  });
});
