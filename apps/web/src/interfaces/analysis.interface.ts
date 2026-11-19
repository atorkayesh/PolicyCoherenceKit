import { z } from "zod";
import { aggregationDataSchema } from "@/interfaces/aggregation.interface";
import { apiResponseSchema } from "@/interfaces/api.interface";
import { insightsDataSchema } from "@/interfaces/insights.interface";

export const coherenceRowSchema = z.object({
  code: z.string(),
  policy: z.string(),
  oi: z.number(),
  ii: z.number(),
  woi: z.number(),
  wii: z.number(),
  oi_band: z.string(),
  ii_band: z.string(),
  woi_band: z.string(),
  wii_band: z.string(),
});

export type CoherenceRow = z.infer<typeof coherenceRowSchema>;

export const pcaPointSchema = z.object({
  index: z.number(),
  code: z.string(),
  policy: z.string(),
  label: z.string(),
  x: z.number(),
  y: z.number(),
  entropy_category: z.string(),
});

export type PcaPoint = z.infer<typeof pcaPointSchema>;

export const pcaBoundsSchema = z.object({
  x_min: z.number(),
  x_max: z.number(),
  y_min: z.number(),
  y_max: z.number(),
});

export type PcaBounds = z.infer<typeof pcaBoundsSchema>;

export const pcaDataSchema = z.object({
  valid: z.boolean(),
  explained: z.array(z.number()),
  total_explained: z.number().nullable(),
  points: z.array(pcaPointSchema),
  bounds: pcaBoundsSchema.nullable(),
  x_axis_label: z.string().nullable(),
  y_axis_label: z.string().nullable(),
  stats_text: z.string().nullable(),
  message: z.string().nullable(),
});

export type PcaData = z.infer<typeof pcaDataSchema>;

export const networkDataSchema = z.object({
  node_count: z.number(),
  edge_count: z.number(),
  density: z.number(),
  isolated_count: z.number(),
  stats_text: z.string(),
  centrality: z.array(
    z.object({
      code: z.string(),
      policy: z.string(),
      betweenness: z.number(),
      closeness: z.number(),
    }),
  ),
  centrality_ranking: z.array(z.string()),
});

export type NetworkData = z.infer<typeof networkDataSchema>;

/** `POST /analysis`: every value the Results tabs show. */
export const analysisDataSchema = z.object({
  project_name: z.string(),
  aggregation: aggregationDataSchema,
  coherence_scores: z.array(coherenceRowSchema),
  range_of_influence: z.object({
    hmax: z.number(),
    rows: z.array(
      z.object({
        code: z.string(),
        policy: z.string(),
        entropy: z.number(),
        category: z.string(),
      }),
    ),
  }),
  pca: pcaDataSchema,
  network: networkDataSchema,
  insights: insightsDataSchema,
});

export const analysisResponseSchema = apiResponseSchema(analysisDataSchema);

export type AnalysisData = z.infer<typeof analysisDataSchema>;
