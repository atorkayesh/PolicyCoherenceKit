import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";

/** Body of `POST /weights/check`: the raw texts of the inputs, in decision-maker order. */
export interface WeightCheckRequest {
  decision_makers: string[];
  weights: (string | null)[];
}

const weightErrorSchema = z.object({
  index: z.number().nullable(),
  decision_maker: z.string().nullable(),
  title: z.string(),
  message: z.string(),
});

export const weightCheckDataSchema = z.object({
  total: z.number().nullable(),
  sum_text: z.string(),
  within_tolerance: z.boolean(),
  valid: z.boolean(),
  weights: z.array(z.number().nullable()),
  errors: z.array(weightErrorSchema),
  first_error: weightErrorSchema.nullable(),
});

export const weightCheckResponseSchema = apiResponseSchema(
  weightCheckDataSchema,
);

export type WeightCheckData = z.infer<typeof weightCheckDataSchema>;
