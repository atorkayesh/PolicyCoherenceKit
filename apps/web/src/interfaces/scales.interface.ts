import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";

/** A choice with a key, label and description (methods, median choices). */
export const optionSchema = z.object({
  key: z.string(),
  label: z.string(),
  description: z.string().nullish(),
});

export type Option = z.infer<typeof optionSchema>;

const colourPairSchema = { fill: z.string(), text: z.string() };

export const rulesSchema = z.object({
  min_policies: z.number(),
  max_policies: z.number(),
  min_decision_makers: z.number(),
  max_decision_makers: z.number(),
  method_choice_min_decision_makers: z.number(),
  forced_method: z.string(),
  default_method: z.string(),
  default_median_choice: z.string(),
  weight_min: z.number(),
  weight_max: z.number(),
  weight_sum_target: z.number(),
  weight_sum_tolerance: z.number(),
});

export type ScalesRules = z.infer<typeof rulesSchema>;

export const networkScaleSchema = z.object({
  layouts: z.array(z.object({ key: z.string(), label: z.string() })),
  default_layout: z.string(),
  positive_colour: z.string(),
  negative_colour: z.string(),
  isolated_colour: z.string(),
  node_colour: z.string(),
  focus_colour: z.string(),
  node_text_colour: z.string(),
  layout_canvas: z.tuple([z.number(), z.number()]),
});

export type NetworkScale = z.infer<typeof networkScaleSchema>;

export const entropyCategorySchema = z.object({
  label: z.string(),
  threshold_text: z.string(),
  ...colourPairSchema,
});

export type EntropyCategory = z.infer<typeof entropyCategorySchema>;

/** `GET /scales`: every label, limit, default and colour the UI shows. */
export const scalesDataSchema = z.object({
  ratings: z.array(
    z.object({ label: z.string(), score: z.number(), ...colourPairSchema }),
  ),
  diagonal_label: z.string(),
  methods: z.array(optionSchema),
  median_choices: z.array(optionSchema),
  rules: rulesSchema,
  count_bands: z.array(
    z.object({
      key: z.string(),
      min_ratio: z.number().nullish(),
      ...colourPairSchema,
    }),
  ),
  value_bands: z.array(z.object({ key: z.string(), ...colourPairSchema })),
  entropy_categories: z.array(entropyCategorySchema),
  network: networkScaleSchema,
  pca: z.object({ point_colour: z.string(), axis_colour: z.string() }),
  texts: z.object({ most_contested_value_label: z.string() }),
  imports: z.object({ accept: z.array(z.string()), max_bytes: z.number() }),
});

export const scalesResponseSchema = apiResponseSchema(scalesDataSchema);

export type ScalesData = z.infer<typeof scalesDataSchema>;
