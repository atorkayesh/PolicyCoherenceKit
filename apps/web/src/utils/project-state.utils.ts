import type { ImportData } from "@/interfaces/import.interface";
import type {
  DraftRow,
  FixedStepId,
  NamedItem,
} from "@/interfaces/project.interface";
import {
  createMatrix,
  hasRatings,
  hasRatingsInPolicies,
  remapMatrix,
  withDiagonal,
} from "@/utils/matrix.utils";

/** A new stable id for a decision-maker or policy. */
export function newId(): string {
  return crypto.randomUUID();
}

/** The parts of the state the pure commit helpers read and write. */
export interface ProjectData {
  projectName: string;
  decisionMakers: NamedItem[];
  policies: NamedItem[];
  codes: string[];
  matrices: Record<string, string[][]>;
  answered: FixedStepId[];
  answeredMatrices: string[];
  weightTexts: Record<string, string>;
  weights: Record<string, number> | null;
  tieChoices: Record<string, string>;
}

/** Draft rows that hold a name (empty rows are ignored, as in the legacy dialog). */
export function filledRows(rows: readonly DraftRow[]): DraftRow[] {
  return rows.filter((row) => row.name.trim() !== "");
}

/** Committed items for the filled draft rows, named by the API's trimmed names (same order). */
export function itemsFromDraft(
  rows: readonly DraftRow[],
  names: readonly string[],
): NamedItem[] {
  return filledRows(rows).map((row, i) => ({
    id: row.id ?? newId(),
    name: names[i] ?? row.name.trim(),
  }));
}

/** Ids of `before` that are missing from `after`. */
export function removedIds(
  before: readonly NamedItem[],
  after: readonly { id: string | null }[],
): Set<string> {
  const kept = new Set(after.map((item) => item.id));
  return new Set(before.filter((item) => !kept.has(item.id)).map((i) => i.id));
}

/** Whether removing these decision-makers loses ratings (ask first). */
export function decisionMakerRemovalLosesRatings(
  data: Pick<ProjectData, "decisionMakers" | "matrices">,
  rows: readonly DraftRow[],
): boolean {
  const removed = removedIds(data.decisionMakers, filledRows(rows));
  return [...removed].some((id) => hasRatings(data.matrices[id] ?? []));
}

/** Whether removing these policies loses ratings in any matrix (ask first). */
export function policyRemovalLosesRatings(
  data: Pick<ProjectData, "policies" | "matrices">,
  rows: readonly DraftRow[],
): boolean {
  const removed = removedIds(data.policies, filledRows(rows));
  if (removed.size === 0) return false;
  const ids = data.policies.map((policy) => policy.id);
  return Object.values(data.matrices).some((matrix) =>
    hasRatingsInPolicies(matrix, ids, removed),
  );
}

function sameIdSet(a: readonly NamedItem[], b: readonly NamedItem[]): boolean {
  if (a.length !== b.length) return false;
  const ids = new Set(a.map((item) => item.id));
  return b.every((item) => ids.has(item.id));
}

function pick<T>(record: Record<string, T>, ids: readonly string[]) {
  return Object.fromEntries(
    ids.filter((id) => id in record).map((id) => [id, record[id]]),
  ) as Record<string, T>;
}

const WEIGHT_STEPS: readonly FixedStepId[] = ["weights", "ties"];

/**
 * Commit the decision-makers: kept ids keep matrix, weight text and answered matrix step; new ids
 * get a blank matrix; removed ids lose theirs. Parsed weights and the weights/ties answers are
 * cleared when the set of ids changes (a reorder keeps them).
 */
export function commitDecisionMakers(
  data: ProjectData,
  items: NamedItem[],
  diagonal: string,
): Partial<ProjectData> {
  const ids = items.map((item) => item.id);
  const size = data.policies.length;
  const matrices = Object.fromEntries(
    ids.map((id) => [id, data.matrices[id] ?? createMatrix(size, diagonal)]),
  );
  const changed = !sameIdSet(data.decisionMakers, items);
  return {
    decisionMakers: items,
    matrices,
    weightTexts: pick(data.weightTexts, ids),
    answeredMatrices: data.answeredMatrices.filter((id) => ids.includes(id)),
    weights: changed ? null : data.weights,
    answered: changed
      ? data.answered.filter((step) => !WEIGHT_STEPS.includes(step))
      : data.answered,
  };
}

/** Commit the policies: every matrix is remapped by policy id; codes are the API's. */
export function commitPolicies(
  data: ProjectData,
  items: NamedItem[],
  codes: string[],
  diagonal: string,
): Partial<ProjectData> {
  const from = data.policies.map((policy) => policy.id);
  const to = items.map((policy) => policy.id);
  const matrices = Object.fromEntries(
    Object.entries(data.matrices).map(([id, matrix]) => [
      id,
      remapMatrix(matrix, from, to, diagonal),
    ]),
  );
  return { policies: items, codes, matrices };
}

/** Names of existing decision-makers with ratings that a merge import would replace. */
export function mergeReplacesRatings(
  data: Pick<ProjectData, "decisionMakers" | "matrices">,
  imported: ImportData,
): string[] {
  const sheets = new Set(imported.matrices.map((m) => m.decision_maker));
  return data.decisionMakers
    .filter(
      (dm) => sheets.has(dm.name) && hasRatings(data.matrices[dm.id] ?? []),
    )
    .map((dm) => dm.name);
}

/** Decision-maker count after a merge import (existing + sheets matching no name). */
export function countAfterMerge(
  decisionMakers: readonly NamedItem[],
  imported: ImportData,
): number {
  const names = new Set(decisionMakers.map((dm) => dm.name));
  const added = imported.matrices.filter((m) => !names.has(m.decision_maker));
  return decisionMakers.length + added.length;
}

/** Import into the project: same-name sheets replace that matrix, other sheets are appended. */
export function mergeWorkbook(
  data: ProjectData,
  imported: ImportData,
  diagonal: string,
): Partial<ProjectData> {
  const decisionMakers = [...data.decisionMakers];
  const matrices = { ...data.matrices };
  const importedIds: string[] = [];
  for (const sheet of imported.matrices) {
    let dm = decisionMakers.find((item) => item.name === sheet.decision_maker);
    if (!dm) {
      dm = { id: newId(), name: sheet.decision_maker };
      decisionMakers.push(dm);
    }
    matrices[dm.id] = withDiagonal(sheet.ratings, diagonal);
    importedIds.push(dm.id);
  }
  const changed = decisionMakers.length !== data.decisionMakers.length;
  return {
    decisionMakers,
    matrices,
    answeredMatrices: [...new Set([...data.answeredMatrices, ...importedIds])],
    weights: changed ? null : data.weights,
    answered: changed
      ? data.answered.filter((step) => !WEIGHT_STEPS.includes(step))
      : data.answered,
  };
}

/** A new project from a workbook: its sheets, policies and ratings replace everything. */
export function replaceWithWorkbook(
  data: ProjectData,
  imported: ImportData,
  projectName: string,
  diagonal: string,
): Partial<ProjectData> {
  const decisionMakers = imported.matrices.map((sheet) => ({
    id: newId(),
    name: sheet.decision_maker,
  }));
  const keep = data.answered.filter(
    (step) => !["weights", "ties", "review", "method", "median"].includes(step),
  );
  return {
    projectName,
    decisionMakers,
    policies: imported.policies.map((name) => ({ id: newId(), name })),
    codes: imported.codes,
    matrices: Object.fromEntries(
      imported.matrices.map((sheet, i) => [
        decisionMakers[i].id,
        withDiagonal(sheet.ratings, diagonal),
      ]),
    ),
    answeredMatrices: decisionMakers.map((dm) => dm.id),
    answered: [
      ...new Set<FixedStepId>([
        ...keep,
        "project",
        "decision-makers",
        "policies",
        "import",
      ]),
    ],
    weightTexts: {},
    weights: null,
    tieChoices: {},
  };
}
