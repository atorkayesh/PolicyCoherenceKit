/** Matrices hold rating labels, `""` = blank; row = influencing policy, column = influenced. */

/** A blank `size × size` matrix with the diagonal label. */
export function createMatrix(size: number, diagonal: string): string[][] {
  return Array.from({ length: size }, (_, i) =>
    Array.from({ length: size }, (_, j) => (i === j ? diagonal : "")),
  );
}

/** `matrix` with the diagonal forced to `diagonal` (imports, remaps). */
export function withDiagonal(matrix: string[][], diagonal: string): string[][] {
  return matrix.map((row, i) =>
    row.map((cell, j) => (i === j ? diagonal : cell)),
  );
}

/**
 * Re-align `matrix` (aligned to `fromIds`) to `toIds`: kept policies keep their cells, new ones
 * are blank, removed ones are dropped.
 */
export function remapMatrix(
  matrix: string[][],
  fromIds: readonly string[],
  toIds: readonly string[],
  diagonal: string,
): string[][] {
  const position = new Map(fromIds.map((id, index) => [id, index]));
  return toIds.map((rowId, i) =>
    toIds.map((colId, j) => {
      if (i === j) return diagonal;
      const r = position.get(rowId);
      const c = position.get(colId);
      return r === undefined || c === undefined ? "" : (matrix[r]?.[c] ?? "");
    }),
  );
}

/** Whether any off-diagonal cell is rated. */
export function hasRatings(matrix: readonly (readonly string[])[]): boolean {
  return matrix.some((row, i) => row.some((cell, j) => i !== j && cell !== ""));
}

/** Whether a rated cell lies in a row or column whose policy id is in `removed`. */
export function hasRatingsInPolicies(
  matrix: readonly (readonly string[])[],
  policyIds: readonly string[],
  removed: ReadonlySet<string>,
): boolean {
  return matrix.some((row, i) =>
    row.some(
      (cell, j) =>
        i !== j &&
        cell !== "" &&
        (removed.has(policyIds[i]) || removed.has(policyIds[j])),
    ),
  );
}

/** Filled and total off-diagonal cells (progress text only; completeness comes from the API). */
export function countFilled(matrix: readonly (readonly string[])[]): {
  filled: number;
  total: number;
} {
  const size = matrix.length;
  let filled = 0;
  matrix.forEach((row, i) => {
    row.forEach((cell, j) => {
      if (i !== j && cell !== "") filled += 1;
    });
  });
  return { filled, total: size * (size - 1) };
}

/** Copy of `matrix` with one cell changed; only that row is copied. */
export function setMatrixCell(
  matrix: string[][],
  row: number,
  col: number,
  value: string,
): string[][] {
  return matrix.map((cells, r) =>
    r !== row ? cells : cells.map((cell, c) => (c === col ? value : cell)),
  );
}
