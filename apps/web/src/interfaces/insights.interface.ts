import { z } from "zod";

const heroSchema = z.object({ hero: z.string(), value_text: z.string() });

/** `AnalysisData.insights`: what the Results Insights cards show, as the legacy tab computes it. */
export const insightsDataSchema = z.object({
  rows: z.array(
    z.object({
      code: z.string(),
      policy: z.string(),
      role: z.string(),
    }),
  ),
  health: z.object({
    score: z.number(),
    synergy: z.number(),
    conflict: z.number(),
    neutral_uncertain: z.number(),
  }),
  texts: z.object({
    story: z.string(),
    interpretation_label: z.string(),
    interpretation_text: z.string(),
    overview_agreement_text: z.string(),
    tag_top_driver: z.string(),
    tag_strongest_link: z.string(),
    tag_contested: z.string(),
    top_driver: heroSchema,
    top_dependent: heroSchema,
    strongest_link: z.object({
      main: z.string(),
      value_text: z.string(),
      caption: z.string(),
    }),
    most_contested: z.object({
      main: z.string(),
      value_text: z.string(),
      caption: z.string(),
    }),
    conflict_ratio: z.object({
      ratio: z.number(),
      main_text: z.string(),
      value_text: z.string(),
      caption: z.string(),
    }),
  }),
});

export type InsightsData = z.infer<typeof insightsDataSchema>;
