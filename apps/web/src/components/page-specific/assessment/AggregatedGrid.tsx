import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";
import { AGGREGATED_TEXT } from "@/constants/results.constants";
import { MATRIX_GRID, MATRIX_TEXT } from "@/constants/steps.constants";
import { RATING_TOKENS, tokenFor } from "@/constants/theme.constants";
import type { AggregationData } from "@/interfaces/aggregation.interface";
import { cn } from "@/lib/utils";
import { formatFixed } from "@/utils/format.utils";

const ROW_HEADER_WIDTH = "w-28 sm:w-48";
const HEADER_CLASS =
  "flex items-center truncate px-2 text-xs font-semibold text-foreground";
/** Score cells are narrower than editor cells: they show `+0.00`-style numbers only. */
const CELL_WIDTH = MATRIX_GRID.CELL_WIDTH / 2;

/**
 * Read-only aggregated scores, virtualised like the editor: `{score:.2f}` in the colour of the
 * API's band (a rating label), with the legacy tooltips.
 */
export function AggregatedGrid({
  aggregation,
}: {
  aggregation: AggregationData;
}) {
  const { codes, policies, scores, bands } = aggregation;
  const scrollRef = useRef<HTMLDivElement>(null);
  const size = policies.length;
  const header = (i: number) => MATRIX_TEXT.HEADER_TITLE(codes[i], policies[i]);
  const rows = useVirtualizer({
    count: size,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => MATRIX_GRID.ROW_HEIGHT,
    overscan: MATRIX_GRID.OVERSCAN,
    initialRect: MATRIX_GRID.INITIAL_RECT,
  });
  const columns = useVirtualizer({
    horizontal: true,
    count: size,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => CELL_WIDTH,
    overscan: MATRIX_GRID.OVERSCAN,
    initialRect: MATRIX_GRID.INITIAL_RECT,
  });
  const width = columns.getTotalSize();
  const height = rows.getTotalSize();

  const cellTitle = (i: number, j: number, text: string) =>
    i === j
      ? AGGREGATED_TEXT.DIAGONAL_TITLE(codes[i])
      : AGGREGATED_TEXT.CELL_TITLE(codes[i], codes[j], text, bands[i][j]);

  return (
    <div
      ref={scrollRef}
      className="max-h-[60vh] w-full overflow-auto rounded-lg border bg-card"
    >
      <div className="w-max">
        <div
          className="sticky top-0 z-20 flex border-b bg-card"
          style={{ height: MATRIX_GRID.HEADER_HEIGHT }}
        >
          <div
            className={cn(
              "sticky left-0 z-30 flex shrink-0 items-center border-r bg-card px-2 text-xs text-muted-foreground",
              ROW_HEADER_WIDTH,
            )}
          >
            {MATRIX_TEXT.CORNER}
          </div>
          <div className="relative shrink-0" style={{ width }}>
            {columns.getVirtualItems().map((column) => (
              <div
                key={column.key}
                title={header(column.index)}
                className={`absolute top-0 h-full justify-center ${HEADER_CLASS}`}
                style={{ left: column.start, width: column.size }}
              >
                {codes[column.index]}
              </div>
            ))}
          </div>
        </div>
        <div className="flex" style={{ height }}>
          <div
            className={cn(
              "sticky left-0 z-10 shrink-0 border-r bg-card",
              ROW_HEADER_WIDTH,
            )}
            style={{ height }}
          >
            {rows.getVirtualItems().map((row) => (
              <div
                key={row.key}
                title={header(row.index)}
                className={`absolute left-0 w-full ${HEADER_CLASS}`}
                style={{ top: row.start, height: row.size }}
              >
                <span className="truncate">
                  {codes[row.index]} {policies[row.index]}
                </span>
              </div>
            ))}
          </div>
          <div className="relative shrink-0" style={{ width }}>
            {rows.getVirtualItems().map((row) =>
              columns.getVirtualItems().map((column) => {
                const i = row.index;
                const j = column.index;
                const text = formatFixed(scores[i][j] ?? 0, 2);
                return (
                  <div
                    key={`${row.key}-${column.key}`}
                    className="absolute p-1"
                    style={{
                      top: row.start,
                      left: column.start,
                      width: column.size,
                      height: row.size,
                    }}
                  >
                    <div
                      title={cellTitle(i, j, text)}
                      data-band={bands[i][j]}
                      className={cn(
                        "flex h-full items-center justify-center rounded-md text-sm font-medium tabular-nums",
                        i === j
                          ? "bg-muted text-muted-foreground"
                          : tokenFor(RATING_TOKENS, bands[i][j]),
                      )}
                    >
                      {text}
                    </div>
                  </div>
                );
              }),
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
