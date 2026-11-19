export const EXPLANATION_TEXT = {
  TITLE: "AI Interpretation",
  NOTE: "This section provides an AI-assisted interpretation of the policy coherence results. After choosing a provider and model and entering an API key, a structured interpretation is generated covering overall coherence, key synergies and conflicts, influential policies, range of influence, network structure and strategic recommendations.",
  PROVIDER: "AI Provider",
  API_KEY: "API Key",
  SHOW_KEY: "Show API key",
  HIDE_KEY: "Hide API key",
  KEY_PRIVACY:
    "Your API key is sent through our server to the AI provider for this request only. It is never saved, stored or logged.",
  MODEL: "Model",
  AZURE_MODEL_PLACEHOLDER: "Your Azure deployment name, e.g. gpt-4o-mini",
  PROVIDERS_ERROR: "The AI providers could not be loaded.",
  GENERATE: "Generate Interpretation",
  GENERATING: "Generating...",
  OUTPUT_LABEL: "Interpretation:",
} as const;

/** Status line under the button (llm_tab.py:812-848). */
export const EXPLANATION_STATUS = {
  MISSING_KEY_TITLE: "API Key Required",
  MISSING_KEY: "Please enter your API key before generating.",
  MISSING_ENDPOINT: "Azure OpenAI endpoint is required.",
  PENDING: (provider: string, model: string) =>
    `Calling ${provider} / ${model} ...`,
  DONE: "Done.",
  ERROR: "Error.",
} as const;

/** Toast shown when generating the interpretation fails (the API's message is the description). */
export const EXPLANATION_TOAST = {
  ERROR_TITLE: "The request failed",
} as const;

/** The Azure OpenAI endpoint dialog. */
export const AZURE_DIALOG_TEXT = {
  TITLE: "Azure OpenAI Endpoint",
  PROMPT: "Enter your Azure OpenAI endpoint, for example:",
  EXAMPLE: "https://YOUR-RESOURCE-NAME.openai.azure.com",
  PLACEHOLDER: "https://YOUR-RESOURCE-NAME.openai.azure.com",
  OK: "OK",
  CANCEL: "Cancel",
} as const;

/** Interpretation download names (llm_tab.py:897, 916). */
export const INTERPRETATION_FILES = {
  TXT: "policy_interpretation.txt",
  PDF: "policy_interpretation.pdf",
} as const;
