import type { ExplanationProvider } from "@/interfaces/explanation.interface";

export const PROVIDERS: ExplanationProvider[] = [
  {
    id: "groq",
    label: "Groq",
    models: ["llama-3.1-8b", "llama-3.3-70b"],
    default_model: "llama-3.1-8b",
    free_text_model: false,
  },
  {
    id: "openai",
    label: "OpenAI",
    models: ["gpt-4o-mini", "gpt-4o"],
    default_model: "gpt-4o-mini",
    free_text_model: false,
  },
  {
    id: "azure_openai",
    label: "Azure OpenAI",
    models: [],
    default_model: null,
    free_text_model: true,
  },
];

export const INTERPRETATION =
  "## 1. Overall coherence\nThe system is coherent.\n2. Key synergies\nEnergy & water.";
