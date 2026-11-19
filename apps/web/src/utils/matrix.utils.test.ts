import { describe, expect, it } from "vitest";
import {
  countFilled,
  createMatrix,
  hasRatings,
  hasRatingsInPolicies,
  remapMatrix,
  setMatrixCell,
} from "@/utils/matrix.utils";

describe("matrix utils", () => {
  it("creates blank matrices with the diagonal label", () => {
    expect(createMatrix(2, "Neutral")).toEqual([
      ["Neutral", ""],
      ["", "Neutral"],
    ]);
  });

  it("remaps by policy id: kept cells stay, new ones are blank, removed ones go", () => {
    const matrix = [
      ["Neutral", "Enabling", "Cancelling"],
      ["Reinforcing", "Neutral", ""],
      ["Constraining", "Enabling", "Neutral"],
    ];
    const remapped = remapMatrix(
      matrix,
      ["a", "b", "c"],
      ["c", "a", "d"],
      "Neutral",
    );
    expect(remapped).toEqual([
      ["Neutral", "Constraining", ""],
      ["Cancelling", "Neutral", ""],
      ["", "", "Neutral"],
    ]);
  });

  it("detects ratings, also in removed policies", () => {
    const matrix = [
      ["Neutral", "Enabling"],
      ["", "Neutral"],
    ];
    expect(hasRatings(matrix)).toBe(true);
    expect(hasRatings(createMatrix(2, "Neutral"))).toBe(false);
    expect(hasRatingsInPolicies(matrix, ["a", "b"], new Set(["b"]))).toBe(true);
    expect(
      hasRatingsInPolicies(
        [
          ["Neutral", ""],
          ["Enabling", "Neutral"],
        ],
        ["a", "b"],
        new Set(),
      ),
    ).toBe(false);
  });

  it("counts filled off-diagonal cells and copies only the changed row", () => {
    const matrix = createMatrix(3, "Neutral");
    const next = setMatrixCell(matrix, 0, 1, "Enabling");
    expect(countFilled(next)).toEqual({ filled: 1, total: 6 });
    expect(next[1]).toBe(matrix[1]);
    expect(next[0]).not.toBe(matrix[0]);
  });
});
