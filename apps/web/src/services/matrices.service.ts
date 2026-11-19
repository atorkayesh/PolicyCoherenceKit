import { API_ENDPOINTS } from "@/constants/api.constants";
import type { ProjectInput } from "@/interfaces/aggregation.interface";
import {
  type MatrixCheckData,
  matrixCheckResponseSchema,
} from "@/interfaces/check.interface";
import { apiData, jsonPost } from "@/utils/api.utils";

/** Completeness of every matrix and which aggregation choices apply. */
export function checkMatrices(project: ProjectInput): Promise<MatrixCheckData> {
  return apiData(
    API_ENDPOINTS.MATRICES_CHECK,
    jsonPost(project),
    matrixCheckResponseSchema,
  );
}
