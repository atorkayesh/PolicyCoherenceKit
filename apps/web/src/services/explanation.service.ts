import { API_ENDPOINTS } from "@/constants/api.constants";
import { INTERPRETATION_FILES } from "@/constants/explanation.constants";
import {
  type ExplanationData,
  type ExplanationProvider,
  type ExplanationRequest,
  explanationProvidersResponseSchema,
  explanationResponseSchema,
} from "@/interfaces/explanation.interface";
import { apiBlob, apiData, jsonPost } from "@/utils/api.utils";

/** Ask the API for an AI interpretation. The key is only in this request's body. */
export function explain(request: ExplanationRequest): Promise<ExplanationData> {
  return apiData(
    API_ENDPOINTS.EXPLANATIONS,
    jsonPost(request),
    explanationResponseSchema,
  );
}

/** AI providers with their models and default model. */
export async function getExplanationProviders(): Promise<
  ExplanationProvider[]
> {
  const data = await apiData(
    API_ENDPOINTS.EXPLANATION_PROVIDERS,
    { headers: { Accept: "application/json" } },
    explanationProvidersResponseSchema,
  );
  return data.providers;
}

/** The interpretation as a PDF (`policy_interpretation.pdf`). */
export async function exportInterpretationPdf(
  text: string,
): Promise<{ blob: Blob; filename: string }> {
  const blob = await apiBlob(API_ENDPOINTS.EXPLANATION_PDF, jsonPost({ text }));
  return { blob, filename: INTERPRETATION_FILES.PDF };
}
