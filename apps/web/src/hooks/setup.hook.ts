import { useMutation } from "@tanstack/react-query";
import { MUTATION_KEYS } from "@/constants/query.constants";
import { validateSetup } from "@/services/setup.service";

/** Validate a name step's draft through `/setup/validate` (legacy messages on failure). */
export function useValidateSetup() {
  return useMutation({
    mutationKey: MUTATION_KEYS.VALIDATE_SETUP,
    mutationFn: validateSetup,
  });
}
