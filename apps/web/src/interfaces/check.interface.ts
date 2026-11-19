import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";

export const aggregationOptionsSchema = z.object({
  decision_maker_count: z.number(),
  method_choice_available: z.boolean(),
  forced_method: z.string().nullable(),
  median_choice_applies: z.boolean(),
});

export type AggregationOptions = z.infer<typeof aggregationOptionsSchema>;

/** `POST /matrices/check`: completeness per decision-maker and which methods apply. */
export const matrixCheckDataSchema = z.object({
  complete: z.boolean(),
  decision_makers: z.array(
    z.object({
      name: z.string(),
      filled: z.number(),
      total: z.number(),
      complete: z.boolean(),
      blank_count: z.number(),
      blank_cells: z.array(
        z.object({
          row: z.number(),
          col: z.number(),
          code_row: z.string(),
          code_col: z.string(),
        }),
      ),
    }),
  ),
  incomplete_message: z.string().nullable(),
  aggregation_options: aggregationOptionsSchema,
});

export const matrixCheckResponseSchema = apiResponseSchema(
  matrixCheckDataSchema,
);

export type MatrixCheckData = z.infer<typeof matrixCheckDataSchema>;
