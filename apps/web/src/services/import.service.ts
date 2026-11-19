import { API_ENDPOINTS } from "@/constants/api.constants";
import {
  type ImportData,
  importResponseSchema,
} from "@/interfaces/import.interface";
import { apiData } from "@/utils/api.utils";

/**
 * Import an `.xlsx` workbook (one sheet per decision-maker). With `policies`, every sheet must
 * have that policy list (import into the project); without, the workbook defines it.
 */
export function importWorkbook(
  file: File,
  policies?: readonly string[],
): Promise<ImportData> {
  const form = new FormData();
  form.append("file", file);
  for (const name of policies ?? []) form.append("policies", name);
  return apiData(
    API_ENDPOINTS.IMPORT_WORKBOOK,
    { method: "POST", body: form },
    importResponseSchema,
  );
}
