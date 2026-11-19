import { PlusIcon, XIcon } from "lucide-react";
import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NAME_LIST_TEXT } from "@/constants/steps.constants";
import type { DraftRow, NamedItem } from "@/interfaces/project.interface";
import { newId } from "@/utils/project-state.utils";

/** Draft rows for committed items, or the legacy two empty rows. */
export function initialRows(items: readonly NamedItem[]): DraftRow[] {
  if (items.length > 0) {
    return items.map((item) => ({
      key: item.id,
      id: item.id,
      name: item.name,
    }));
  }
  return Array.from({ length: NAME_LIST_TEXT.INITIAL_ROWS }, () => ({
    key: newId(),
    id: null,
    name: "",
  }));
}

/**
 * Editable list of names (legacy dialog rows): `Add` appends a row and focuses it (disabled at
 * `max`), rows 3 and up can be removed. Enter in a row submits the step (StepFrame), Tab moves on.
 */
export function NameListEditor({
  label,
  rows,
  max,
  placeholder,
  onChange,
}: {
  label: string;
  rows: DraftRow[];
  max: number;
  placeholder: (index: number) => string;
  onChange: (rows: DraftRow[]) => void;
}) {
  const inputs = useRef(new Map<string, HTMLInputElement>());
  const focusKey = useRef<string | null>(null);

  useEffect(() => {
    if (!focusKey.current) return;
    inputs.current.get(focusKey.current)?.focus();
    focusKey.current = null;
  });

  const add = () => {
    const row = { key: newId(), id: null, name: "" };
    focusKey.current = row.key;
    onChange([...rows, row]);
  };

  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="pb-2 text-sm font-medium">{label}</legend>
      {rows.map((row, index) => (
        <div key={row.key} className="flex items-center gap-2">
          <Input
            ref={(element) => {
              if (element) inputs.current.set(row.key, element);
              else inputs.current.delete(row.key);
            }}
            aria-label={NAME_LIST_TEXT.ROW_LABEL(label, index + 1)}
            value={row.name}
            placeholder={placeholder(index)}
            onChange={(event) =>
              onChange(
                rows.map((item) =>
                  item.key === row.key
                    ? { ...item, name: event.target.value }
                    : item,
                ),
              )
            }
            className="h-10 text-base sm:text-sm"
          />
          {index >= NAME_LIST_TEXT.FIXED_ROWS ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label={NAME_LIST_TEXT.REMOVE_ROW(index + 1)}
              onClick={() =>
                onChange(rows.filter((item) => item.key !== row.key))
              }
              className="shrink-0 text-muted-foreground hover:text-destructive"
            >
              <XIcon />
            </Button>
          ) : (
            <span aria-hidden="true" className="size-8 shrink-0" />
          )}
        </div>
      ))}
      <div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={add}
          disabled={rows.length >= max}
        >
          <PlusIcon data-icon="inline-start" />
          {NAME_LIST_TEXT.ADD}
        </Button>
      </div>
    </fieldset>
  );
}
