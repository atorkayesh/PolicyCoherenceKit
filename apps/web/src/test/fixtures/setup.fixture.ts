import type { SetupData } from "@/interfaces/setup.interface";

export const SETUP_PROJECT: SetupData = { project_name: "Nexus" };
export const SETUP_DMS: SetupData = { decision_makers: ["Alice", "Bob"] };
export const SETUP_POLICIES: SetupData = {
  policies: ["Energy", "Water", "Food"],
  codes: ["P1", "P2", "P3"],
};
