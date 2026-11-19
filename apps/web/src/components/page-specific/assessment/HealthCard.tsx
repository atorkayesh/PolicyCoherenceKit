import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { INSIGHTS_TEXT } from "@/constants/insights.constants";
import type { InsightsData } from "@/interfaces/insights.interface";

/** System Health: synergy, conflict and neutral/uncertain shares as bars with `%` (item 31). */
export function HealthCard({ health }: { health: InsightsData["health"] }) {
  const bars = [
    {
      label: INSIGHTS_TEXT.SYNERGY,
      value: health.synergy,
      fill: "bg-health-synergy",
    },
    {
      label: INSIGHTS_TEXT.CONFLICT,
      value: health.conflict,
      fill: "bg-health-conflict",
    },
    {
      label: INSIGHTS_TEXT.NEUTRAL,
      value: health.neutral_uncertain,
      fill: "bg-health-neutral",
    },
  ];
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base font-semibold">
          {INSIGHTS_TEXT.HEALTH}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {bars.map((bar) => (
          <div
            key={bar.label}
            className="grid grid-cols-[8rem_1fr_3rem] items-center gap-2 text-sm"
          >
            <span className="text-muted-foreground">{bar.label}</span>
            <div className="h-2 overflow-hidden rounded-full bg-health-track">
              <div
                className={`h-full rounded-full ${bar.fill}`}
                style={{
                  width: `${Math.max(INSIGHTS_TEXT.MIN_BAR_PERCENT, bar.value)}%`,
                }}
              />
            </div>
            <span className="text-right font-semibold">{bar.value}%</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
