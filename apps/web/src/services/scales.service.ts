import { API_ENDPOINTS } from "@/constants/api.constants";
import {
  type ScalesData,
  scalesResponseSchema,
} from "@/interfaces/scales.interface";
import { apiData } from "@/utils/api.utils";

/** Ratings, methods, rules, limits and colours (they never change while the app runs). */
export function getScales(): Promise<ScalesData> {
  return apiData(
    API_ENDPOINTS.SCALES,
    { headers: { Accept: "application/json" } },
    scalesResponseSchema,
  );
}
