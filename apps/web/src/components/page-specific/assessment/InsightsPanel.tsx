import { HealthCard } from "@/components/page-specific/assessment/HealthCard";
import { KeyInsightsCard } from "@/components/page-specific/assessment/KeyInsightsCard";
import { OverviewCard } from "@/components/page-specific/assessment/OverviewCard";
import { SignalCard } from "@/components/page-specific/assessment/SignalCard";
import { INSIGHTS_TEXT } from "@/constants/insights.constants";
import type { AnalysisData } from "@/interfaces/analysis.interface";

/** Results Insights: the legacy cards with the API's texts (Key Insights spans two columns on lg). */
export function InsightsPanel({ data }: { data: AnalysisData }) {
  const { texts } = data.insights;
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div className="md:col-span-2">
        <KeyInsightsCard insights={data.insights} />
      </div>
      <OverviewCard data={data} />
      <HealthCard health={data.insights.health} />
      <SignalCard
        title={INSIGHTS_TEXT.TOP_DRIVER}
        main={texts.top_driver.hero}
        value={texts.top_driver.value_text}
      />
      <SignalCard
        title={INSIGHTS_TEXT.TOP_DEPENDENT}
        main={texts.top_dependent.hero}
        value={texts.top_dependent.value_text}
      />
      <SignalCard
        title={INSIGHTS_TEXT.STRONGEST_LINK}
        main={texts.strongest_link.main}
        value={texts.strongest_link.value_text}
        caption={texts.strongest_link.caption}
      />
      <SignalCard
        title={INSIGHTS_TEXT.MOST_CONTESTED}
        main={texts.most_contested.main}
        value={texts.most_contested.value_text}
        caption={texts.most_contested.caption}
        help={INSIGHTS_TEXT.CONTESTED_HELP}
      />
      <SignalCard
        title={INSIGHTS_TEXT.CONFLICT_RATIO}
        main={texts.conflict_ratio.main_text}
        value={texts.conflict_ratio.value_text}
        caption={texts.conflict_ratio.caption}
      />
    </div>
  );
}
