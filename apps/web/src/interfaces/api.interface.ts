import { z } from "zod";

/** Zod schema for the backend `ApiResponseModel` wrapper around `data`. */
export function apiResponseSchema<T extends z.ZodType>(data: T) {
  return z.object({
    success: z.boolean(),
    message: z.string().nullish(),
    data: data.nullish(),
    metadata: z.record(z.string(), z.unknown()).nullish(),
  });
}

/** One invalid request field of a 422 validation error. */
export const fieldErrorSchema = z.object({
  field: z.string(),
  message: z.string(),
});

/**
 * Body of a non-OK response: the API's `message`, its `error` block (`code`, `fields`) and the
 * feature error's `data` (for example `{title, field}` or `{warning_groups}`).
 */
export const apiErrorBodySchema = z.object({
  message: z.string().nullish(),
  data: z.unknown().nullish(),
  error: z
    .union([
      z.object({
        code: z.string(),
        fields: z.array(fieldErrorSchema).nullish(),
      }),
      z.string(),
    ])
    .nullish(),
});
