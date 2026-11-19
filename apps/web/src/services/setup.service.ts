import { API_ENDPOINTS } from "@/constants/api.constants";
import {
  type SetupData,
  type SetupValidateRequest,
  setupResponseSchema,
} from "@/interfaces/setup.interface";
import { apiData, jsonPost } from "@/utils/api.utils";

/** Validate the project name, decision-makers or policies; returns trimmed names and codes. */
export function validateSetup(body: SetupValidateRequest): Promise<SetupData> {
  return apiData(
    API_ENDPOINTS.SETUP_VALIDATE,
    jsonPost(body),
    setupResponseSchema,
  );
}
