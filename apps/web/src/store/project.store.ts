import { create } from "zustand";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { ImportData, ImportReport } from "@/interfaces/import.interface";
import type {
  ChartView,
  FixedStepId,
  NamedItem,
  StoredAggregationOptions,
} from "@/interfaces/project.interface";
import { hashString, requestKey } from "@/utils/analysis-request.utils";
import { setMatrixCell } from "@/utils/matrix.utils";
import {
  commitDecisionMakers,
  commitPolicies,
  mergeWorkbook,
  type ProjectData,
  replaceWithWorkbook,
} from "@/utils/project-state.utils";

/**
 * The assessment answers (keyed by stable decision-maker and policy ids), and the results with the
 * request snapshot they were computed from. Results, charts, exports and the AI request always use
 * the snapshot. Nothing is persisted: a refresh starts over.
 */
export interface ProjectState extends ProjectData {
  importReport: ImportReport | null;
  method: string | null;
  medianChoice: string | null;
  aggregationOptions: StoredAggregationOptions | null;
  tieCount: number | null;
  snapshot: AnalysisRequest | null;
  snapshotHash: string;
  results: AnalysisData | null;
  interpretationText: string;
  chartView: ChartView;
}

export interface ProjectActions {
  setProjectName: (name: string) => void;
  commitDecisionMakers: (items: NamedItem[], diagonal: string) => void;
  commitPolicies: (
    items: NamedItem[],
    codes: string[],
    diagonal: string,
  ) => void;
  setCell: (dmId: string, row: number, col: number, value: string) => void;
  applyWorkbook: (
    mode: "replace" | "merge",
    data: ImportData,
    diagonal: string,
    projectName?: string,
  ) => void;
  markAnswered: (step: FixedStepId) => void;
  markMatrixAnswered: (dmId: string) => void;
  setMethod: (method: string) => void;
  setWeightText: (dmId: string, text: string) => void;
  setWeights: (weights: Record<string, number> | null) => void;
  setMedianChoice: (choice: string) => void;
  setTieChoice: (key: string, rating: string) => void;
  setAggregationOptions: (options: StoredAggregationOptions) => void;
  setTieCount: (count: number) => void;
  setResults: (snapshot: AnalysisRequest, data: AnalysisData) => void;
  setInterpretationText: (text: string) => void;
  setChartView: (view: Partial<ChartView>) => void;
  reset: () => void;
}

export const initialProjectState: ProjectState = {
  projectName: "",
  decisionMakers: [],
  policies: [],
  codes: [],
  matrices: {},
  answered: [],
  answeredMatrices: [],
  importReport: null,
  method: null,
  weightTexts: {},
  weights: null,
  medianChoice: null,
  tieChoices: {},
  aggregationOptions: null,
  tieCount: null,
  snapshot: null,
  snapshotHash: "",
  results: null,
  interpretationText: "",
  chartView: {
    pcaColourByEntropy: false,
    networkLayout: null,
    networkFocus: null,
  },
};

export const useProjectStore = create<ProjectState & ProjectActions>()(
  (set) => ({
    ...initialProjectState,

    setProjectName: (projectName) => set({ projectName }),

    commitDecisionMakers: (items, diagonal) =>
      set((state) => commitDecisionMakers(state, items, diagonal)),

    commitPolicies: (items, codes, diagonal) =>
      set((state) => commitPolicies(state, items, codes, diagonal)),

    // Only the changed row is copied, so every other cell keeps its identity and does not re-render.
    setCell: (dmId, row, col, value) =>
      set((state) => {
        const matrix = state.matrices[dmId];
        if (!matrix) return state;
        return {
          matrices: {
            ...state.matrices,
            [dmId]: setMatrixCell(matrix, row, col, value),
          },
        };
      }),

    applyWorkbook: (mode, data, diagonal, projectName) =>
      set((state) => ({
        ...(mode === "replace"
          ? replaceWithWorkbook(
              state,
              data,
              projectName || data.suggested_project_name || state.projectName,
              diagonal,
            )
          : mergeWorkbook(state, data, diagonal)),
        importReport: {
          summaryMessage: data.summary_message,
          warningGroups: data.warning_groups,
        },
      })),

    markAnswered: (step) =>
      set((state) =>
        state.answered.includes(step)
          ? state
          : { answered: [...state.answered, step] },
      ),

    markMatrixAnswered: (dmId) =>
      set((state) =>
        state.answeredMatrices.includes(dmId)
          ? state
          : { answeredMatrices: [...state.answeredMatrices, dmId] },
      ),

    setMethod: (method) => set({ method }),

    setWeightText: (dmId, text) =>
      set((state) => ({ weightTexts: { ...state.weightTexts, [dmId]: text } })),

    setWeights: (weights) => set({ weights }),

    setMedianChoice: (medianChoice) => set({ medianChoice }),

    setTieChoice: (key, rating) =>
      set((state) => ({ tieChoices: { ...state.tieChoices, [key]: rating } })),

    setAggregationOptions: (aggregationOptions) => set({ aggregationOptions }),

    setTieCount: (tieCount) => set({ tieCount }),

    setResults: (snapshot, data) =>
      set({
        snapshot,
        snapshotHash: hashString(requestKey(snapshot)),
        results: data,
      }),

    setInterpretationText: (interpretationText) => set({ interpretationText }),

    setChartView: (view) =>
      set((state) => ({ chartView: { ...state.chartView, ...view } })),

    reset: () => set(initialProjectState),
  }),
);
