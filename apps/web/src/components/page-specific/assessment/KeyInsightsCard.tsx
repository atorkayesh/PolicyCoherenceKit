import { StoryText } from "@/components/page-specific/assessment/StoryText";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { INSIGHTS_TEXT } from "@/constants/insights.constants";
import type { InsightsData } from "@/interfaces/insights.interface";

/** Key Insights: the story, the interpretation and the three tags (API texts). */
export function KeyInsightsCard({ insights }: { insights: InsightsData }) {
  const { texts } = insights;
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base font-semibold">
          {INSIGHTS_TEXT.KEY_INSIGHTS}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <StoryText story={texts.story} rows={insights.rows} />
        <p className="text-sm">
          <span className="font-semibold">{texts.interpretation_label}</span>{" "}
          {texts.interpretation_text}
        </p>
        <ul className="flex flex-wrap gap-2">
          {[
            texts.tag_top_driver,
            texts.tag_strongest_link,
            texts.tag_contested,
          ].map((tag) => (
            <li
              key={tag}
              className="rounded-full border bg-muted px-3 py-1 text-xs font-medium"
            >
              {tag}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
