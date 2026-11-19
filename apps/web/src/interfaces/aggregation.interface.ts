import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";

/** One decision-maker as sent to the API: rating labels, row = influencing policy ("" = blank). */
export interface DecisionMakerInput {
  name: string;
  ratings: string[][];
}

/** The project part of every request. */
export interface ProjectInput {
  project_name: string;
  policies: string[];
  decision_makers: DecisionMakerInput[];
}

/** A chosen rating for a tied cell (0-based policy indices). */
export interface TieChoice {
  row: number;
  col: number;
  rating: string;
}

export interface AggregationSettings {
  method: string;
  weights: number[] | null;
  median_choice: string | null;
  tie_choices: TieChoice[];
}

/** Body of every analysis-derived endpoint (preview, analysis, export, charts, explanation). */
export interface AnalysisRequest extends ProjectInput {
  aggregation: AggregationSettings;
}

export const tieSchema = z.object({
  row: z.number(),
  col: z.number(),
  code_row: z.string(),
  code_col: z.string(),
  policy_row: z.string(),
  policy_col: z.string(),
  tied_options: z.array(z.object({ label: z.string(), score: z.number() })),
  votes: z.array(z.object({ decision_maker: z.string(), rating: z.string() })),
  chosen: z.string().nullable(),
});

export type Tie = z.infer<typeof tieSchema>;

/** `POST /aggregation/preview` and `AnalysisData.aggregation`. */
export const aggregationDataSchema = z.object({
  requested_method: z.string(),
  method: z.string(),
  method_label: z.string(),
  method_forced: z.boolean(),
  decision_maker_count: z.number(),
  decision_makers: z.array(z.string()),
  policies: z.array(z.string()),
  codes: z.array(z.string()),
  weights: z.array(z.number()).nullable(),
  median_choice: z.string().nullable(),
  scores: z.array(z.array(z.number().nullable())),
  bands: z.array(z.array(z.string())),
  ordinal_cells: z.array(z.array(z.array(z.string()))).nullable(),
  ties: z.array(tieSchema),
  ready: z.boolean(),
});

export const aggregationResponseSchema = apiResponseSchema(
  aggregationDataSchema,
);

export type AggregationData = z.infer<typeof aggregationDataSchema>;
