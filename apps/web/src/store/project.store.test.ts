import { beforeEach, describe, expect, it } from "vitest";
import { useProjectStore } from "@/store/project.store";
import { ANALYSIS } from "@/test/fixtures/analysis.fixture";
import { IMPORT_DATA } from "@/test/fixtures/import.fixture";

const store = () => useProjectStore.getState();
const N = "Neutral";

function seed() {
  store().commitDecisionMakers(
    [
      { id: "a", name: "Alice" },
      { id: "b", name: "Bob" },
    ],
    N,
  );
  store().commitPolicies(
    [
      { id: "p1", name: "Energy" },
      { id: "p2", name: "Water" },
    ],
    ["P1", "P2"],
    N,
  );
  store().setCell("a", 0, 1, "Enabling");
  store().markMatrixAnswered("a");
  store().setWeightText("a", "0.5");
}

describe("project store", () => {
  beforeEach(() => store().reset());

  it("keeps matrix, weight text and answered step across rename and reorder", () => {
    seed();
    store().setWeights({ a: 0.5, b: 0.5 });
    store().markAnswered("weights");
    store().commitDecisionMakers(
      [
        { id: "b", name: "Bob" },
        { id: "a", name: "Alicia" },
      ],
      N,
    );
    expect(store().matrices.a[0][1]).toBe("Enabling");
    expect(store().weightTexts.a).toBe("0.5");
    expect(store().answeredMatrices).toEqual(["a"]);
    expect(store().weights).toEqual({ a: 0.5, b: 0.5 });
    expect(store().answered).toContain("weights");
  });

  it("drops a removed decision-maker and clears weights when the set changes", () => {
    seed();
    store().setWeights({ a: 0.5, b: 0.5 });
    store().markAnswered("weights");
    store().commitDecisionMakers(
      [
        { id: "b", name: "Bob" },
        { id: "c", name: "Cara" },
      ],
      N,
    );
    expect(store().matrices.a).toBeUndefined();
    expect(store().matrices.c).toEqual([
      [N, ""],
      ["", N],
    ]);
    expect(store().weightTexts).toEqual({});
    expect(store().answeredMatrices).toEqual([]);
    expect(store().weights).toBeNull();
    expect(store().answered).not.toContain("weights");
  });

  it("remaps matrices by policy id; matrix steps stay answered", () => {
    seed();
    store().commitPolicies(
      [
        { id: "p3", name: "Food" },
        { id: "p1", name: "Energy" },
        { id: "p2", name: "Water" },
      ],
      ["P1", "P2", "P3"],
      N,
    );
    expect(store().matrices.a[1][2]).toBe("Enabling");
    expect(store().matrices.a[0]).toEqual([N, "", ""]);
    expect(store().codes).toEqual(["P1", "P2", "P3"]);
    expect(store().answeredMatrices).toEqual(["a"]);
  });

  it("replaces everything with a workbook, keeping a typed project name", () => {
    seed();
    store().applyWorkbook("replace", IMPORT_DATA, N, "My project");
    const state = store();
    expect(state.projectName).toBe("My project");
    expect(state.decisionMakers.map((dm) => dm.name)).toEqual(["Alice", "Bob"]);
    expect(state.decisionMakers[0].id).not.toBe("a");
    expect(state.policies.map((p) => p.name)).toEqual([
      "Energy",
      "Water",
      "Food",
    ]);
    expect(state.matrices[state.decisionMakers[1].id][0][1]).toBe("");
    expect(state.answered).toEqual(
      expect.arrayContaining([
        "project",
        "decision-makers",
        "policies",
        "import",
      ]),
    );
    expect(state.answeredMatrices).toHaveLength(2);
    expect(state.importReport?.summaryMessage).toBe(
      "2 matrix/matrices imported.",
    );
    store().applyWorkbook("replace", IMPORT_DATA, N, "");
    expect(store().projectName).toBe("WEF Nexus Example");
  });

  it("merges a workbook: same-name sheets fill, others are appended", () => {
    store().commitDecisionMakers([{ id: "a", name: "Alice" }], N);
    store().commitPolicies(
      IMPORT_DATA.policies.map((name, i) => ({ id: `p${i}`, name })),
      IMPORT_DATA.codes,
      N,
    );
    store().applyWorkbook("merge", IMPORT_DATA, N);
    const state = store();
    expect(state.decisionMakers[0]).toEqual({ id: "a", name: "Alice" });
    expect(state.decisionMakers[1].name).toBe("Bob");
    expect(state.matrices.a[0][1]).toBe("Enabling");
    expect(state.answeredMatrices).toEqual(["a", state.decisionMakers[1].id]);
  });

  it("stores results with the snapshot hash and resets", () => {
    seed();
    const request = {
      project_name: "x",
      policies: [],
      decision_makers: [],
      aggregation: {
        method: "average",
        weights: null,
        median_choice: null,
        tie_choices: [],
      },
    };
    store().setResults(request, ANALYSIS);
    expect(store().snapshotHash).not.toBe("");
    store().setChartView({ networkFocus: 2 });
    expect(store().chartView.networkFocus).toBe(2);
    store().reset();
    expect(store().results).toBeNull();
    expect(store().decisionMakers).toEqual([]);
  });
});
