import { Button } from "@/components/ui/button";
import { RUN_ERROR_LINKS } from "@/constants/aggregation.constants";
import type { StepError, StepId } from "@/interfaces/project.interface";
import { errorCode, stepError } from "@/utils/api.utils";

/** A failed run as a step error; incomplete matrices link to Review, unresolved ties to Ties. */
export function runError(
  error: unknown,
  onOpen: (step: StepId) => void,
): StepError {
  const code = errorCode(error);
  const link = code ? RUN_ERROR_LINKS[code] : undefined;
  return stepError(
    error,
    link ? (
      <div>
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto px-0"
          onClick={() => onOpen(link.step as StepId)}
        >
          {link.label}
        </Button>
      </div>
    ) : undefined,
  );
}
