import type { AnalysisRequest } from "@/interfaces/aggregation.interface";

/** A 2-decision-maker, 3-policy request (complete). */
export const REQUEST: AnalysisRequest = {
  project_name: "Nexus",
  policies: ["Energy", "Water", "Food"],
  decision_makers: [
    {
      name: "Alice",
      ratings: [
        ["Neutral", "Enabling", "Neutral"],
        ["Reinforcing", "Neutral", "Enabling"],
        ["Neutral", "Indivisible", "Neutral"],
      ],
    },
    {
      name: "Bob",
      ratings: [
        ["Neutral", "Reinforcing", "Neutral"],
        ["Cancelling", "Neutral", "Neutral"],
        ["Neutral", "Indivisible", "Neutral"],
      ],
    },
  ],
  aggregation: {
    method: "average",
    weights: null,
    median_choice: null,
    tie_choices: [],
  },
};
