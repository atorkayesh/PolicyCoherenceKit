import type { MatrixCheckData } from "@/interfaces/check.interface";

/** Two decision-makers, 3 policies, complete: Average is forced. */
export const CHECK_COMPLETE_TWO: MatrixCheckData = {
  complete: true,
  decision_makers: [
    {
      name: "Alice",
      filled: 6,
      total: 6,
      complete: true,
      blank_count: 0,
      blank_cells: [],
    },
    {
      name: "Bob",
      filled: 6,
      total: 6,
      complete: true,
      blank_count: 0,
      blank_cells: [],
    },
  ],
  incomplete_message: null,
  aggregation_options: {
    decision_maker_count: 2,
    method_choice_available: false,
    forced_method: "average",
    median_choice_applies: true,
  },
};

/** One decision-maker with 12 blanks (only the first 10 listed). */
export const CHECK_INCOMPLETE: MatrixCheckData = {
  complete: false,
  decision_makers: [
    {
      name: "Alice",
      filled: 8,
      total: 20,
      complete: false,
      blank_count: 12,
      blank_cells: Array.from({ length: 10 }, (_, k) => ({
        row: 0,
        col: k + 1,
        code_row: "P1",
        code_col: `P${k + 2}`,
      })),
    },
  ],
  incomplete_message:
    "Please fill all cells before aggregating.\n\n  Alice: P1 → P2, P1 → P3",
  aggregation_options: {
    decision_maker_count: 1,
    method_choice_available: false,
    forced_method: "average",
    median_choice_applies: false,
  },
};

/** Options for `n` decision-makers with a choice (n ≥ 3). */
export function choiceOptions(
  n: number,
): MatrixCheckData["aggregation_options"] {
  return {
    decision_maker_count: n,
    method_choice_available: true,
    forced_method: null,
    median_choice_applies: n % 2 === 0,
  };
}
