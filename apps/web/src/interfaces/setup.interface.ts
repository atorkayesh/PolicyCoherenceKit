import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";

/** Body of `POST /setup/validate`: only the parts present are validated. */
export interface SetupValidateRequest {
  project_name?: string;
  decision_makers?: string[];
  policies?: string[];
  existing_decision_makers?: string[];
}

export const setupDataSchema = z.object({
  project_name: z.string().nullish(),
  decision_makers: z.array(z.string()).nullish(),
  policies: z.array(z.string()).nullish(),
  codes: z.array(z.string()).nullish(),
});

export const setupResponseSchema = apiResponseSchema(setupDataSchema);

export type SetupData = z.infer<typeof setupDataSchema>;
