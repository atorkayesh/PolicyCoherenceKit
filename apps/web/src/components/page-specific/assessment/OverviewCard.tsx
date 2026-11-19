import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { INSIGHTS_TEXT } from "@/constants/insights.constants";
import type { AnalysisData } from "@/interfaces/analysis.interface";

/** Analysis Overview: counts, method and the decision-makers' rank agreement (API text). */
export function OverviewCard({ data }: { data: AnalysisData }) {
  const { aggregation } = data;
  const rows = [
    {
      label: INSIGHTS_TEXT.POLICIES,
      value: String(aggregation.policies.length),
    },
    {
      label: INSIGHTS_TEXT.DECISION_MAKERS,
      value: String(aggregation.decision_maker_count),
    },
    { label: INSIGHTS_TEXT.METHOD, value: aggregation.method_label },
    {
      label: INSIGHTS_TEXT.AGREEMENT,
      value: data.insights.texts.overview_agreement_text,
      help: INSIGHTS_TEXT.AGREEMENT_HELP,
    },
  ];
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base font-semibold">
          {INSIGHTS_TEXT.OVERVIEW}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="flex flex-col gap-2 text-sm">
          {rows.map((row) => (
            <div key={row.label} className="flex flex-col">
              <div className="flex items-baseline justify-between gap-3">
                <dt className="text-muted-foreground">{row.label}</dt>
                <dd className="text-right font-semibold">{row.value}</dd>
              </div>
              {row.help && (
                <p className="text-xs text-muted-foreground">{row.help}</p>
              )}
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
