import { AggregatedPanel } from "@/components/page-specific/assessment/AggregatedPanel";
import { CoherenceScoresPanel } from "@/components/page-specific/assessment/CoherenceScoresPanel";
import { ExplanationPanel } from "@/components/page-specific/assessment/ExplanationPanel";
import { InsightsPanel } from "@/components/page-specific/assessment/InsightsPanel";
import { NetworkPanel } from "@/components/page-specific/assessment/NetworkPanel";
import { PcaPanel } from "@/components/page-specific/assessment/PcaPanel";
import { RangeOfInfluencePanel } from "@/components/page-specific/assessment/RangeOfInfluencePanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TAB_IDS, TAB_LABELS } from "@/constants/results.constants";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { ScalesData } from "@/interfaces/scales.interface";

const TRIGGER_CLASS = "flex-none px-3 max-sm:h-10";
const ORDER = [
  "INSIGHTS",
  "AGGREGATED",
  "SCORES",
  "RANGE",
  "PCA",
  "NETWORK",
  "AI",
] as const;

/**
 * The seven legacy result tabs as a scrolling segmented control. Only the open tab is mounted
 * (charts load on first view), except the AI tab, which keeps its key field and output.
 */
export function ResultTabs({
  snapshot,
  snapshotHash,
  data,
  scales,
}: {
  snapshot: AnalysisRequest;
  snapshotHash: string;
  data: AnalysisData;
  scales: ScalesData;
}) {
  return (
    <Tabs defaultValue={TAB_IDS.INSIGHTS} className="gap-4">
      <div className="w-full overflow-x-auto pb-1">
        <TabsList className="h-9 max-sm:h-11">
          {ORDER.map((tab) => (
            <TabsTrigger
              key={tab}
              value={TAB_IDS[tab]}
              className={TRIGGER_CLASS}
            >
              {TAB_LABELS[tab]}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      <TabsContent value={TAB_IDS.INSIGHTS}>
        <InsightsPanel data={data} />
      </TabsContent>
      <TabsContent value={TAB_IDS.AGGREGATED}>
        <AggregatedPanel data={data} scales={scales} />
      </TabsContent>
      <TabsContent value={TAB_IDS.SCORES}>
        <CoherenceScoresPanel data={data} />
      </TabsContent>
      <TabsContent value={TAB_IDS.RANGE}>
        <RangeOfInfluencePanel data={data} scales={scales} />
      </TabsContent>
      <TabsContent value={TAB_IDS.PCA}>
        <PcaPanel data={data} scales={scales} />
      </TabsContent>
      <TabsContent value={TAB_IDS.NETWORK}>
        <NetworkPanel
          snapshot={snapshot}
          snapshotHash={snapshotHash}
          data={data}
          scales={scales}
        />
      </TabsContent>
      <TabsContent value={TAB_IDS.AI} keepMounted>
        <ExplanationPanel snapshot={snapshot} />
      </TabsContent>
    </Tabs>
  );
}
