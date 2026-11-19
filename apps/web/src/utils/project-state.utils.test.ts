import { describe, expect, it } from "vitest";
import { IMPORT_DATA } from "@/test/fixtures/import.fixture";
import {
  countAfterMerge,
  decisionMakerRemovalLosesRatings,
  filledRows,
  itemsFromDraft,
  mergeReplacesRatings,
  policyRemovalLosesRatings,
} from "@/utils/project-state.utils";

const row = (id: string | null, name: string) => ({
  key: id ?? name,
  id,
  name,
});

describe("project state helpers", () => {
  it("ignores empty rows and names items with the API's trimmed names", () => {
    const rows = [row("a", " Alice "), row(null, "  "), row(null, "Bob")];
    expect(filledRows(rows)).toHaveLength(2);
    const items = itemsFromDraft(rows, ["Alice", "Bob"]);
    expect(items[0]).toEqual({ id: "a", name: "Alice" });
    expect(items[1].name).toBe("Bob");
    expect(items[1].id).not.toBe("a");
  });

  it("asks before removals that lose ratings", () => {
    const data = {
      decisionMakers: [
        { id: "a", name: "A" },
        { id: "b", name: "B" },
      ],
      policies: [
        { id: "p1", name: "X" },
        { id: "p2", name: "Y" },
      ],
      matrices: {
        a: [
          ["Neutral", "Enabling"],
          ["", "Neutral"],
        ],
        b: [
          ["Neutral", ""],
          ["", "Neutral"],
        ],
      },
    };
    // Removing B (no ratings) needs no confirm; removing A (rated) does.
    expect(decisionMakerRemovalLosesRatings(data, [row("a", "A")])).toBe(false);
    expect(decisionMakerRemovalLosesRatings(data, [row("b", "B")])).toBe(true);
    expect(
      decisionMakerRemovalLosesRatings(data, [
        row("a", "A"),
        row("b", "B"),
        row(null, "C"),
      ]),
    ).toBe(false);
    expect(policyRemovalLosesRatings(data, [row("p1", "X")])).toBe(true);
    expect(
      policyRemovalLosesRatings(data, [
        row("p1", "X"),
        row("p2", "Y"),
        row(null, "Z"),
      ]),
    ).toBe(false);
  });

  it("counts a merge and names the decision-makers whose ratings it replaces", () => {
    const dms = [
      { id: "a", name: "Alice" },
      { id: "c", name: "Cara" },
    ];
    expect(countAfterMerge(dms, IMPORT_DATA)).toBe(3);
    const matrices = {
      a: [
        ["Neutral", "Enabling"],
        ["", "Neutral"],
      ],
      c: [],
    };
    expect(
      mergeReplacesRatings({ decisionMakers: dms, matrices }, IMPORT_DATA),
    ).toEqual(["Alice"]);
  });
});
