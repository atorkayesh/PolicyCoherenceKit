import { cn } from "@/lib/utils";

export interface LegendItem {
  key: string;
  label: string;
  /** Swatch colour (from the API, the same value the chart series uses). */
  colour: string;
  /** Hidden entries are shown struck through (toggle legends only). */
  hidden?: boolean;
}

const ITEM_CLASS =
  "inline-flex items-center gap-1.5 rounded-md border bg-card px-2 py-0.5 text-xs font-medium text-foreground";

/**
 * Chart legend: API-colour swatches with ink labels in badge-like chips. With `onToggle`, each
 * entry is a toggle button (`aria-pressed`) that shows or hides its part of the chart.
 */
export function ChartLegend({
  label,
  items,
  onToggle,
}: {
  label?: string;
  items: readonly LegendItem[];
  onToggle?: (key: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {label && <span className="text-sm text-muted-foreground">{label}</span>}
      {items.map((item) => {
        const swatch = (
          <span
            key="swatch"
            aria-hidden="true"
            className="size-3 shrink-0 rounded-sm"
            style={{ backgroundColor: item.colour }}
          />
        );
        return onToggle ? (
          <button
            key={item.key}
            type="button"
            aria-pressed={!item.hidden}
            onClick={() => onToggle(item.key)}
            className={cn(
              ITEM_CLASS,
              "hover:bg-muted max-sm:py-1.5",
              item.hidden && "text-muted-foreground line-through opacity-70",
            )}
          >
            {swatch}
            {item.label}
          </button>
        ) : (
          <span key={item.key} className={ITEM_CLASS}>
            {swatch}
            {item.label}
          </span>
        );
      })}
    </div>
  );
}
