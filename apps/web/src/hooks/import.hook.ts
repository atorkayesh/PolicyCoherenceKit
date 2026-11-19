import { useMutation } from "@tanstack/react-query";
import { MUTATION_KEYS } from "@/constants/query.constants";
import { importWorkbook } from "@/services/import.service";

/** Upload a workbook; the caller confirms and applies the result (replace or merge). */
export function useImportWorkbook() {
  return useMutation({
    mutationKey: MUTATION_KEYS.IMPORT_WORKBOOK,
    mutationFn: ({ file, policies }: { file: File; policies?: string[] }) =>
      importWorkbook(file, policies),
  });
}
