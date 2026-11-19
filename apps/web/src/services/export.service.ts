import { API_ENDPOINTS } from "@/constants/api.constants";
import { EXPORT_FILES } from "@/constants/results.constants";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import { apiFile, jsonPost } from "@/utils/api.utils";

/** The XLSX workbook of the request, named by the API (`{project}_coherence.xlsx`). */
export function exportXlsx(
  request: AnalysisRequest,
): Promise<{ blob: Blob; filename: string }> {
  return apiFile(
    API_ENDPOINTS.EXPORT_XLSX,
    jsonPost(request),
    EXPORT_FILES.XLSX_FALLBACK,
  );
}
