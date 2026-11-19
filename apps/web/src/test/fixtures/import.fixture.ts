import type { ImportData } from "@/interfaces/import.interface";

/** A workbook with two sheets for 3 policies; Bob's sheet has blanks. */
export const IMPORT_DATA: ImportData = {
  policies: ["Energy", "Water", "Food"],
  codes: ["P1", "P2", "P3"],
  matrices: [
    {
      decision_maker: "Alice",
      ratings: [
        ["Neutral", "Enabling", "Constraining"],
        ["Reinforcing", "Neutral", "Neutral"],
        ["Neutral", "Indivisible", "Neutral"],
      ],
    },
    {
      decision_maker: "Bob",
      ratings: [
        ["Neutral", "", "Enabling"],
        ["Neutral", "Neutral", ""],
        ["Cancelling", "Neutral", "Neutral"],
      ],
    },
  ],
  warning_groups: [
    {
      kind: "blank_cells",
      heading: "The following sheets have blank cells:",
      messages: ["Bob: P1 → P2, P2 → P3"],
    },
  ],
  imported_count: 2,
  summary_message: "2 matrix/matrices imported.",
  suggested_project_name: "WEF Nexus Example",
};

/** A clean single-sheet import. */
export const IMPORT_CLEAN: ImportData = {
  ...IMPORT_DATA,
  matrices: [IMPORT_DATA.matrices[0]],
  warning_groups: [],
  imported_count: 1,
  summary_message: "1 matrix/matrices imported successfully.",
};
