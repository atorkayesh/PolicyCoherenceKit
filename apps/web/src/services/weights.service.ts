import { API_ENDPOINTS } from "@/constants/api.constants";
import {
  type WeightCheckData,
  type WeightCheckRequest,
  weightCheckResponseSchema,
} from "@/interfaces/weights.interface";
import { apiData, jsonPost } from "@/utils/api.utils";

/** Parse the raw weight texts, with the live sum text and the first error (always 200). */
export function checkWeights(
  body: WeightCheckRequest,
): Promise<WeightCheckData> {
  return apiData(
    API_ENDPOINTS.WEIGHTS_CHECK,
    jsonPost(body),
    weightCheckResponseSchema,
  );
}
