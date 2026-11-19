import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface CodeTableColumn<Row> {
  key: string;
  label: string;
  /** Header tooltip (legacy texts). */
  title?: string;
  align?: "left" | "right";
  cell: (row: Row) => ReactNode;
}

/** Shared striped results table (fixed legacy order, no sorting), scrolling horizontally. */
export function CodeTable<Row>({
  caption,
  columns,
  rows,
  rowKey,
}: {
  caption: string;
  columns: readonly CodeTableColumn<Row>[];
  rows: readonly Row[];
  rowKey: (row: Row) => string;
}) {
  return (
    <div className="w-full overflow-x-auto rounded-lg border bg-card">
      <table className="w-full min-w-max border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b bg-muted">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                title={column.title}
                className={cn(
                  "px-3 py-2 font-semibold whitespace-nowrap",
                  column.align === "right" ? "text-right" : "text-left",
                )}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              className="border-b last:border-0 even:bg-muted/40"
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn(
                    "px-3 py-1.5",
                    column.align === "right"
                      ? "text-right tabular-nums"
                      : "text-left",
                  )}
                >
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** A value in a coloured band chip (token classes from the theme constants). */
export function BandCell({
  token,
  children,
}: {
  token: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-block min-w-14 rounded-md px-2 py-0.5 text-right font-medium tabular-nums",
        token,
      )}
    >
      {children}
    </span>
  );
}
