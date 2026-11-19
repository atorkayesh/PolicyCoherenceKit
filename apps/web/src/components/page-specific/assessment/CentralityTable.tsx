import {
  CodeTable,
  type CodeTableColumn,
} from "@/components/page-specific/assessment/CodeTable";
import { NETWORK_TEXT, TABLE_TEXT } from "@/constants/results.constants";
import type { NetworkData } from "@/interfaces/analysis.interface";
import { formatFixed } from "@/utils/format.utils";

type Row = NetworkData["centrality"][number];

const COLUMNS: CodeTableColumn<Row>[] = [
  {
    key: "code",
    label: TABLE_TEXT.CODE,
    title: TABLE_TEXT.CODE_TITLE,
    cell: (r) => r.code,
  },
  {
    key: "betweenness",
    label: NETWORK_TEXT.BETWEENNESS,
    align: "right",
    cell: (r) => formatFixed(r.betweenness, 4),
  },
  {
    key: "closeness",
    label: NETWORK_TEXT.CLOSENESS,
    align: "right",
    cell: (r) => formatFixed(r.closeness, 4),
  },
  { key: "policy", label: TABLE_TEXT.POLICY, cell: (r) => r.policy },
];

/** Centrality Measures in the API's ranking order. */
export function CentralityTable({ network }: { network: NetworkData }) {
  const byCode = new Map(network.centrality.map((row) => [row.code, row]));
  const rows = network.centrality_ranking.flatMap((code) => {
    const row = byCode.get(code);
    return row ? [row] : [];
  });
  return (
    <div className="flex flex-col gap-2">
      <div>
        <h4 className="font-semibold">{NETWORK_TEXT.CENTRALITY}</h4>
        <p className="text-xs whitespace-pre text-muted-foreground">
          {NETWORK_TEXT.CENTRALITY_HELP}
        </p>
      </div>
      <CodeTable
        caption={NETWORK_TEXT.CENTRALITY}
        columns={COLUMNS}
        rows={rows}
        rowKey={(row) => row.code}
      />
    </div>
  );
}
