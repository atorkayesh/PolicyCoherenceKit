import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";
import { MatrixCell } from "@/components/page-specific/assessment/MatrixCell";
import { MATRIX_GRID, MATRIX_TEXT } from "@/constants/steps.constants";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/store/project.store";

/** Frozen policy column: narrower on phones so more cells fit. */
const ROW_HEADER_WIDTH = "w-28 sm:w-48";

const HEADER_CLASS =
  "flex items-center truncate px-2 text-xs font-semibold text-foreground";

/**
 * One decision-maker's matrix: rows and columns virtualised so 100 × 100 stays responsive, with
 * the header row and column frozen (sticky). Rows are the influencing policies. The first editable
 * cell (row 1, column 2) is the step's initial focus.
 */
export function MatrixGrid({
  dmId,
  ratings,
  diagonalLabel,
}: {
  dmId: string;
  ratings: readonly string[];
  diagonalLabel: string;
}) {
  const policies = useProjectStore((state) => state.policies);
  const codes = useProjectStore((state) => state.codes);
  const scrollRef = useRef<HTMLDivElement>(null);
  const size = policies.length;
  const header = (i: number) =>
    MATRIX_TEXT.HEADER_TITLE(codes[i], policies[i].name);

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
    estimateSize: () => MATRIX_GRID.CELL_WIDTH,
    overscan: MATRIX_GRID.OVERSCAN,
    initialRect: MATRIX_GRID.INITIAL_RECT,
  });
  const bodyWidth = columns.getTotalSize();
  const bodyHeight = rows.getTotalSize();
  const virtualRows = rows.getVirtualItems();
  const virtualColumns = columns.getVirtualItems();

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
          <div className="relative shrink-0" style={{ width: bodyWidth }}>
            {virtualColumns.map((column) => (
              <div
                key={column.key}
                title={header(column.index)}
                className={`absolute top-0 h-full ${HEADER_CLASS}`}
                style={{ left: column.start, width: column.size }}
              >
                {codes[column.index]}
              </div>
            ))}
          </div>
        </div>
        <div className="flex" style={{ height: bodyHeight }}>
          <div
            className={cn(
              "sticky left-0 z-10 shrink-0 border-r bg-card",
              ROW_HEADER_WIDTH,
            )}
            style={{ height: bodyHeight }}
          >
            {virtualRows.map((row) => (
              <div
                key={row.key}
                title={header(row.index)}
                className={`absolute left-0 w-full ${HEADER_CLASS}`}
                style={{ top: row.start, height: row.size }}
              >
                <span className="truncate">
                  {codes[row.index]} {policies[row.index].name}
                </span>
              </div>
            ))}
          </div>
          <div className="relative shrink-0" style={{ width: bodyWidth }}>
            {virtualRows.map((row) =>
              virtualColumns.map((column) => (
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
                  <MatrixCell
                    dmId={dmId}
                    row={row.index}
                    col={column.index}
                    label={MATRIX_TEXT.CELL_LABEL(
                      codes[row.index],
                      policies[row.index].name,
                      codes[column.index],
                      policies[column.index].name,
                    )}
                    ratings={ratings}
                    diagonalLabel={diagonalLabel}
                    autoFocus={row.index === 0 && column.index === 1}
                  />
                </div>
              )),
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
