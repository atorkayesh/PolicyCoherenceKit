import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { NETWORK_TEXT } from "@/constants/results.constants";
import { useNetworkView } from "@/hooks/chart-view.hook";
import type { AggregationData } from "@/interfaces/aggregation.interface";
import type { ScalesData } from "@/interfaces/scales.interface";
import { useProjectStore } from "@/store/project.store";

const FIELD = "flex min-w-0 flex-col gap-1 text-sm";
const TRIGGER = "h-8 w-full min-w-44 bg-card max-sm:h-11";
const FULL = "full";

/** Layout (from `/scales`) and Focus policy selects; they write the chart view in the store. */
export function NetworkSelects({
  scales,
  policies,
}: {
  scales: ScalesData;
  policies: Pick<AggregationData, "codes" | "policies">;
}) {
  const { layout, focus } = useNetworkView(scales);
  const setChartView = useProjectStore((state) => state.setChartView);
  const layoutLabel = (key: string) =>
    scales.network.layouts.find((item) => item.key === key)?.label ?? key;
  const focusLabel = (value: string) =>
    value === FULL
      ? NETWORK_TEXT.FULL_NETWORK
      : NETWORK_TEXT.FOCUS_OPTION(
          policies.codes[Number(value)],
          policies.policies[Number(value)],
        );

  return (
    <>
      <div className={FIELD}>
        {NETWORK_TEXT.LAYOUT}
        <Select
          value={layout}
          onValueChange={(next) =>
            typeof next === "string" && setChartView({ networkLayout: next })
          }
        >
          <SelectTrigger aria-label={NETWORK_TEXT.LAYOUT} className={TRIGGER}>
            <SelectValue>{(value: string) => layoutLabel(value)}</SelectValue>
          </SelectTrigger>
          <SelectContent alignItemWithTrigger={false}>
            {scales.network.layouts.map((item) => (
              <SelectItem key={item.key} value={item.key}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className={FIELD}>
        {NETWORK_TEXT.FOCUS}
        <Select
          value={focus === null ? FULL : String(focus)}
          onValueChange={(next) =>
            typeof next === "string" &&
            setChartView({ networkFocus: next === FULL ? null : Number(next) })
          }
        >
          <SelectTrigger aria-label={NETWORK_TEXT.FOCUS} className={TRIGGER}>
            <SelectValue>{(value: string) => focusLabel(value)}</SelectValue>
          </SelectTrigger>
          <SelectContent alignItemWithTrigger={false}>
            <SelectItem value={FULL}>{NETWORK_TEXT.FULL_NETWORK}</SelectItem>
            {policies.codes.map((code, index) => (
              <SelectItem key={code} value={String(index)}>
                {NETWORK_TEXT.FOCUS_OPTION(code, policies.policies[index])}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </>
  );
}
