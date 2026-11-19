import {
  BandCell,
  CodeTable,
  type CodeTableColumn,
} from "@/components/page-specific/assessment/CodeTable";
import {
  SCORES_TEXT,
  TAB_LABELS,
  TABLE_TEXT,
} from "@/constants/results.constants";
import {
  COUNT_BAND_TOKENS,
  tokenFor,
  VALUE_BAND_TOKENS,
} from "@/constants/theme.constants";
import type {
  AnalysisData,
  CoherenceRow,
} from "@/interfaces/analysis.interface";
import { formatInt, formatSigned } from "@/utils/format.utils";

const [OI, II, WOI, WII] = SCORES_TEXT.COLUMNS;

const COLUMNS: CodeTableColumn<CoherenceRow>[] = [
  {
    key: "code",
    label: TABLE_TEXT.CODE,
    title: TABLE_TEXT.CODE_TITLE,
    cell: (r) => r.code,
  },
  {
    ...OI,
    align: "right",
    cell: (r) => (
      <BandCell token={tokenFor(COUNT_BAND_TOKENS, r.oi_band)}>
        {formatInt(r.oi)}
      </BandCell>
    ),
  },
  {
    ...II,
    align: "right",
    cell: (r) => (
      <BandCell token={tokenFor(COUNT_BAND_TOKENS, r.ii_band)}>
        {formatInt(r.ii)}
      </BandCell>
    ),
  },
  {
    ...WOI,
    align: "right",
    cell: (r) => (
      <BandCell token={tokenFor(VALUE_BAND_TOKENS, r.woi_band)}>
        {formatSigned(r.woi, 2)}
      </BandCell>
    ),
  },
  {
    ...WII,
    align: "right",
    cell: (r) => (
      <BandCell token={tokenFor(VALUE_BAND_TOKENS, r.wii_band)}>
        {formatSigned(r.wii, 2)}
      </BandCell>
    ),
  },
  { key: "policy", label: TABLE_TEXT.POLICY, cell: (r) => r.policy },
];

/** Coherence Scores: the legend and the per-policy OI/II/WOI/WII table, coloured by API bands. */
export function CoherenceScoresPanel({ data }: { data: AnalysisData }) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-semibold">{TAB_LABELS.SCORES}</h3>
      <dl className="grid gap-1 text-sm sm:grid-cols-[auto_1fr] sm:gap-x-3">
        {SCORES_TEXT.LEGEND.map((item) => (
          <div key={item.abbr} className="contents">
            <dt className="font-semibold">{item.abbr}</dt>
            <dd className="text-muted-foreground">{item.text}</dd>
          </div>
        ))}
      </dl>
      <CodeTable
        caption={TAB_LABELS.SCORES}
        columns={COLUMNS}
        rows={data.coherence_scores}
        rowKey={(row) => row.code}
      />
    </div>
  );
}
