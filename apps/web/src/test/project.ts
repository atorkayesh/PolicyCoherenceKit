import type { NamedItem } from "@/interfaces/project.interface";
import { useProjectStore } from "@/store/project.store";
import { createMatrix } from "@/utils/matrix.utils";

/** Options of `seedProject`. */
export interface SeedOptions {
  dms?: string[];
  policies?: string[];
  /** Rate every off-diagonal cell with this label (else blank). */
  fill?: string;
  /** Mark every step up to and including these answered. */
  answered?: Parameters<
    ReturnType<typeof useProjectStore.getState>["markAnswered"]
  >[0][];
  matricesAnswered?: boolean;
}

/** Put a project into the store: ids `dm-1…`, `p-1…`, codes `P1…`. */
export function seedProject({
  dms = ["Alice", "Bob"],
  policies = ["Energy", "Water", "Food"],
  fill,
  answered = ["project", "decision-makers", "policies", "import"],
  matricesAnswered = true,
}: SeedOptions = {}) {
  const decisionMakers: NamedItem[] = dms.map((name, i) => ({
    id: `dm-${i + 1}`,
    name,
  }));
  const items: NamedItem[] = policies.map((name, i) => ({
    id: `p-${i + 1}`,
    name,
  }));
  const matrix = () =>
    createMatrix(items.length, "Neutral").map((row, i) =>
      row.map((cell, j) => (i === j ? cell : (fill ?? ""))),
    );
  useProjectStore.setState({
    projectName: "Nexus",
    decisionMakers,
    policies: items,
    codes: items.map((_, i) => `P${i + 1}`),
    matrices: Object.fromEntries(decisionMakers.map((dm) => [dm.id, matrix()])),
    answered,
    answeredMatrices: matricesAnswered ? decisionMakers.map((dm) => dm.id) : [],
  });
  return { decisionMakers, policies: items };
}
