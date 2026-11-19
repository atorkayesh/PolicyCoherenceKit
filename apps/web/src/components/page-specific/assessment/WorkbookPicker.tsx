import { FileSpreadsheetIcon, LoaderCircleIcon } from "lucide-react";
import { type ChangeEvent, useRef } from "react";
import { Button } from "@/components/ui/button";
import { IMPORT_TEXT } from "@/constants/import.constants";

/**
 * "Import from Excel": a button that opens a hidden file input. The input is reset after each pick,
 * so the same file can be picked again.
 */
export function WorkbookPicker({
  accept,
  pending,
  disabled = false,
  onFile,
}: {
  accept: readonly string[];
  pending: boolean;
  disabled?: boolean;
  onFile: (file: File) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const takeFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) onFile(file);
  };
  return (
    <>
      <Button
        type="button"
        variant="outline"
        className="w-full max-sm:h-11 sm:w-auto"
        disabled={disabled || pending}
        aria-busy={pending}
        onClick={() => input.current?.click()}
      >
        {pending ? (
          <LoaderCircleIcon className="animate-spin" data-icon="inline-start" />
        ) : (
          <FileSpreadsheetIcon data-icon="inline-start" />
        )}
        {IMPORT_TEXT.BUTTON}
      </Button>
      <input
        ref={input}
        type="file"
        hidden
        accept={accept.join(",")}
        data-testid="workbook-input"
        onChange={takeFile}
      />
    </>
  );
}
