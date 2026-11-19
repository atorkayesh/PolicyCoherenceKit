import {
  BandCell,
  CodeTable,
  type CodeTableColumn,
} from "@/components/page-specific/assessment/CodeTable";
import {
  RANGE_TEXT,
  TAB_LABELS,
  TABLE_TEXT,
} from "@/constants/results.constants";
import { ENTROPY_TOKENS, tokenFor } from "@/constants/theme.constants";
import type { AnalysisData } from "@/interfaces/analysis.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { formatFixed } from "@/utils/format.utils";

type Row = AnalysisData["range_of_influence"]["rows"][number];

const COLUMNS: CodeTableColumn<Row>[] = [
  {
    key: "code",
    label: TABLE_TEXT.CODE,
    title: TABLE_TEXT.CODE_TITLE,
    cell: (r) => r.code,
  },
  {
    key: "entropy",
    label: RANGE_TEXT.ENTROPY,
    title: RANGE_TEXT.ENTROPY_TITLE,
    align: "right",
    cell: (r) => formatFixed(r.entropy, 4),
  },
  {
    key: "category",
    label: RANGE_TEXT.CATEGORY,
    title: RANGE_TEXT.CATEGORY_TITLE,
    cell: (r) => (
      <BandCell token={tokenFor(ENTROPY_TOKENS, r.category)}>
        {r.category}
      </BandCell>
    ),
  },
  { key: "policy", label: TABLE_TEXT.POLICY, cell: (r) => r.policy },
];

/** Range of Influence: entropy per policy, the categories and their thresholds (API texts). */
export function RangeOfInfluencePanel({
  data,
  scales,
}: {
  data: AnalysisData;
  scales: ScalesData;
}) {
  const { hmax, rows } = data.range_of_influence;
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="font-semibold">{TAB_LABELS.RANGE}</h3>
        <p className="text-sm text-muted-foreground">
          {RANGE_TEXT.SUBTITLE(formatFixed(hmax, 4))}
        </p>
      </div>
      <p className="text-sm">
        {RANGE_TEXT.EXPLANATION} {RANGE_TEXT.LOW_NOTE}
      </p>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-muted-foreground">{RANGE_TEXT.CATEGORIES}</span>
        {scales.entropy_categories.map((category) => (
          <span key={category.label} className="flex items-center gap-1.5">
            <BandCell token={tokenFor(ENTROPY_TOKENS, category.label)}>
              {category.label}
            </BandCell>
            <span className="text-muted-foreground">
              {category.threshold_text}
            </span>
          </span>
        ))}
      </div>
      <CodeTable
        caption={TAB_LABELS.RANGE}
        columns={COLUMNS}
        rows={rows}
        rowKey={(r) => r.code}
      />
    </div>
  );
}
