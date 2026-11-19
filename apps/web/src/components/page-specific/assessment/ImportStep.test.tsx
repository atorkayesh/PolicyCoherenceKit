import { fireEvent, screen, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ImportStep } from "@/components/page-specific/assessment/ImportStep";
import { ProjectStep } from "@/components/page-specific/assessment/ProjectStep";
import { importWorkbook } from "@/services/import.service";
import { useProjectStore } from "@/store/project.store";
import { IMPORT_CLEAN, IMPORT_DATA } from "@/test/fixtures/import.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";
import { renderWithQuery } from "@/test/render";
import { ApiError } from "@/utils/api.utils";

const navigate = vi.hoisted(() => vi.fn());
vi.mock("@tanstack/react-router", () => ({ useNavigate: () => navigate }));
vi.mock("@/services/import.service", () => ({ importWorkbook: vi.fn() }));
vi.mock("@/services/setup.service", () => ({ validateSetup: vi.fn() }));
vi.mock("sonner", () => ({ toast: { success: vi.fn() } }));

const store = () => useProjectStore.getState();
const nav = () => ({
  number: 4,
  onAdvance: vi.fn(),
  onBack: vi.fn(),
  onOpen: vi.fn(),
  isLast: false,
});
const upload = () =>
  fireEvent.change(screen.getByTestId("workbook-input"), {
    target: { files: [new File(["x"], "WEF Nexus Example.xlsx")] },
  });

describe("import into the project (step 4)", () => {
  beforeEach(() => {
    store().reset();
    navigate.mockReset();
    vi.mocked(importWorkbook).mockReset();
    vi.mocked(toast.success).mockReset();
  });

  it("sends the policies, appends new sheets and shows the grouped report", async () => {
    seedProject({ dms: ["Cara"] });
    vi.mocked(importWorkbook).mockResolvedValue(IMPORT_DATA);
    renderWithQuery(<ImportStep scales={SCALES} {...nav()} />);
    expect(screen.getByTestId("workbook-input").getAttribute("accept")).toBe(
      ".xlsx",
    );
    upload();
    await waitFor(() => expect(store().decisionMakers).toHaveLength(3));
    expect(vi.mocked(importWorkbook).mock.calls[0][1]).toEqual([
      "Energy",
      "Water",
      "Food",
    ]);
    expect(toast.success).toHaveBeenCalledWith(
      "Import Complete with Warnings",
      { description: "2 matrix/matrices imported." },
    );
    expect(
      screen.getByText("The following sheets have blank cells:"),
    ).toBeDefined();
    expect(screen.getByText("Bob: P1 → P2, P2 → P3")).toBeDefined();
  });

  it("asks before replacing rated matrices of same-name decision-makers", async () => {
    seedProject({ dms: ["Alice"], fill: "Cancelling" });
    vi.mocked(importWorkbook).mockResolvedValue(IMPORT_CLEAN);
    renderWithQuery(<ImportStep scales={SCALES} {...nav()} />);
    upload();
    expect(
      await screen.findByText(
        "The workbook has ratings for Alice, who already have ratings here. They will be replaced.",
      ),
    ).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(store().matrices["dm-1"][0][1]).toBe("Cancelling");
    upload();
    fireEvent.click(await screen.findByRole("button", { name: "Replace" }));
    expect(store().matrices["dm-1"][0][1]).toBe("Enabling");
    expect(toast.success).toHaveBeenCalledWith("Import Complete", {
      description: "1 matrix/matrices imported successfully.",
    });
  });

  it("applies nothing when the merge would exceed the decision-maker limit", async () => {
    seedProject({ dms: ["Cara"] });
    vi.mocked(importWorkbook).mockResolvedValue(IMPORT_DATA);
    const scales = {
      ...SCALES,
      rules: { ...SCALES.rules, max_decision_makers: 2 },
    };
    renderWithQuery(<ImportStep scales={scales} {...nav()} />);
    upload();
    expect((await screen.findByRole("alert")).textContent).toBe(
      "Import ErrorPlease enter at most 2 decision-makers.",
    );
    expect(store().decisionMakers).toHaveLength(1);
  });

  it("shows legacy titles for import errors, with the warning groups", async () => {
    seedProject();
    const groups = [
      {
        kind: "skipped",
        heading: "The following sheets were skipped:",
        messages: ["Sheet1: empty, skipped"],
      },
    ];
    vi.mocked(importWorkbook).mockRejectedValueOnce(
      new ApiError(
        "No valid matrices were found in the workbook.",
        422,
        "nothing_imported",
        { warning_groups: groups },
      ),
    );
    renderWithQuery(<ImportStep scales={SCALES} {...nav()} />);
    upload();
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Nothing Imported");
    expect(alert.textContent).toContain("The following sheets were skipped:");
    vi.mocked(importWorkbook).mockRejectedValueOnce(
      new ApiError(
        "The following sheets have a different policy list…",
        422,
        "policy_list_mismatch",
      ),
    );
    upload();
    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toContain(
        "Policy List Mismatch",
      ),
    );
    vi.mocked(importWorkbook).mockRejectedValueOnce(
      new ApiError(
        "Only .xlsx workbooks are supported.",
        422,
        "unsupported_file",
      ),
    );
    upload();
    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toBe(
        "Import ErrorOnly .xlsx workbooks are supported.",
      ),
    );
  });

  it("OK skips to the first unanswered step after import", () => {
    seedProject({ matricesAnswered: false });
    useProjectStore.setState({ answeredMatrices: ["dm-1"] });
    const props = nav();
    renderWithQuery(<ImportStep scales={SCALES} {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(store().answered).toContain("import");
    expect(props.onOpen).toHaveBeenCalledWith("matrix-2");
  });
});

describe("start from Excel (step 1)", () => {
  beforeEach(() => {
    store().reset();
    navigate.mockReset();
    vi.mocked(importWorkbook).mockReset();
  });

  it("replaces at once when nothing exists, naming the project after the file", async () => {
    vi.mocked(importWorkbook).mockResolvedValue(IMPORT_DATA);
    renderWithQuery(<ProjectStep scales={SCALES} {...nav()} />);
    upload();
    await waitFor(() =>
      expect(navigate).toHaveBeenCalledWith({ search: { step: "import" } }),
    );
    expect(vi.mocked(importWorkbook).mock.calls[0]).toEqual([
      expect.any(File),
      undefined,
    ]);
    expect(store().projectName).toBe("WEF Nexus Example");
    expect(store().decisionMakers.map((dm) => dm.name)).toEqual([
      "Alice",
      "Bob",
    ]);
  });

  it("asks before replacing existing answers and keeps a typed name", async () => {
    seedProject();
    vi.mocked(importWorkbook).mockResolvedValue(IMPORT_DATA);
    renderWithQuery(<ProjectStep scales={SCALES} {...nav()} />);
    fireEvent.change(screen.getByLabelText("Project Name"), {
      target: { value: "Typed" },
    });
    upload();
    expect(
      await screen.findByText(
        "The workbook replaces the decision-makers, policies and ratings you entered.",
      ),
    ).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Replace" }));
    expect(store().projectName).toBe("Typed");
    expect(store().decisionMakers[0].id).not.toBe("dm-1");
  });
});
