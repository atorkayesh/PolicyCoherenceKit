import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";

export const networkNodeSchema = z.object({
  index: z.number(),
  code: z.string(),
  policy: z.string(),
  label: z.string(),
  x: z.number(),
  y: z.number(),
  isolated: z.boolean(),
  is_focus: z.boolean(),
  radius: z.number(),
  fill: z.string(),
});

export const networkEdgeSchema = z.object({
  source: z.number(),
  target: z.number(),
  score: z.number(),
  sign: z.string(),
  colour: z.string(),
  width: z.number(),
  two_way: z.boolean(),
  label: z.string().nullable(),
});

/** `POST /analysis/charts/network`: everything the graph series draws (no browser maths). */
export const networkChartDataSchema = z.object({
  layout: z.string(),
  layout_label: z.string(),
  focus: z.number().nullable(),
  canvas: z.object({ width: z.number(), height: z.number() }),
  title: z.string().nullable(),
  empty_message: z.string().nullable(),
  nodes: z.array(networkNodeSchema),
  edges: z.array(networkEdgeSchema),
  stats: z.object({
    node_count: z.number(),
    edge_count: z.number(),
    density: z.number(),
    isolated_count: z.number(),
    text: z.string(),
  }),
});

export const networkChartResponseSchema = apiResponseSchema(
  networkChartDataSchema,
);

export type NetworkChartData = z.infer<typeof networkChartDataSchema>;
export type NetworkNode = z.infer<typeof networkNodeSchema>;
export type NetworkEdge = z.infer<typeof networkEdgeSchema>;
