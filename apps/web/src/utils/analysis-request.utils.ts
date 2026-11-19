import type {
  AnalysisRequest,
  ProjectInput,
  TieChoice,
} from "@/interfaces/aggregation.interface";
import type { NamedItem } from "@/interfaces/project.interface";
import type { ScalesRules } from "@/interfaces/scales.interface";

/** The answers a request is built from (the store's state). */
export interface RequestInputs {
  projectName: string;
  decisionMakers: NamedItem[];
  policies: NamedItem[];
  matrices: Record<string, string[][]>;
  method: string | null;
  weights: Record<string, number> | null;
  medianChoice: string | null;
  tieChoices: Record<string, string>;
}

/** Key of a tie choice: the row and column policy ids. */
export function tieKey(rowPolicyId: string, colPolicyId: string): string {
  return `${rowPolicyId}>${colPolicyId}`;
}

/** The project part: trimmed names, ratings aligned to the policies. */
export function buildProjectInput(inputs: RequestInputs): ProjectInput {
  return {
    project_name: inputs.projectName.trim(),
    policies: inputs.policies.map((policy) => policy.name.trim()),
    decision_makers: inputs.decisionMakers.map((dm) => ({
      name: dm.name.trim(),
      ratings: inputs.matrices[dm.id] ?? [],
    })),
  };
}

/** Tie choices as 0-based indices into the current policies (choices of removed policies dropped). */
export function buildTieChoices(
  policies: readonly NamedItem[],
  tieChoices: Record<string, string>,
): TieChoice[] {
  const index = new Map(policies.map((policy, i) => [policy.id, i]));
  return Object.entries(tieChoices).flatMap(([key, rating]) => {
    const [rowId, colId] = key.split(">");
    const row = index.get(rowId);
    const col = index.get(colId);
    return row === undefined || col === undefined || !rating
      ? []
      : [{ row, col, rating }];
  });
}

/** The `AnalysisRequest` for the current answers, exactly as the backend contract defines it. */
export function buildAnalysisRequest(
  inputs: RequestInputs,
  rules: Pick<ScalesRules, "default_method" | "default_median_choice">,
): AnalysisRequest {
  const method = inputs.method ?? rules.default_method;
  const weights = inputs.decisionMakers.map((dm) => inputs.weights?.[dm.id]);
  const allWeights = weights.every((weight) => weight !== undefined);
  return {
    ...buildProjectInput(inputs),
    aggregation: {
      method,
      weights:
        method === "weighted" && allWeights ? (weights as number[]) : null,
      median_choice:
        method === "median"
          ? (inputs.medianChoice ?? rules.default_median_choice)
          : null,
      tie_choices:
        method === "majority"
          ? buildTieChoices(inputs.policies, inputs.tieChoices)
          : [],
    },
  };
}

/** The request for the ties preview: the tie choices are left out, so only the ties are listed. */
export function previewRequest(request: AnalysisRequest): AnalysisRequest {
  return {
    ...request,
    aggregation: { ...request.aggregation, tie_choices: [] },
  };
}

/** Stable key of a request, for query keys and comparing against the results snapshot. */
export function requestKey(request: unknown): string {
  return request ? JSON.stringify(request) : "";
}

/** Short FNV-1a hash of a string (query keys use it instead of a ~10 MB request). */
export function hashString(value: string): string {
  let hash = 0x811c9dc5;
  for (let i = 0; i < value.length; i++) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return `${(hash >>> 0).toString(16)}-${value.length}`;
}
