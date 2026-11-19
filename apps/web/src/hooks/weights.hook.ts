import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  QUERY_KEYS,
  WEIGHT_CHECK_DEBOUNCE_MS,
} from "@/constants/query.constants";
import type { WeightCheckRequest } from "@/interfaces/weights.interface";
import { checkWeights } from "@/services/weights.service";

/** `value`, updated only after it stayed unchanged for `delay` ms. */
export function useDebounced<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/** The live weight sum: `/weights/check` on the debounced raw texts, keeping the last answer. */
export function useWeightCheck(body: WeightCheckRequest) {
  // Debounce the text form: a new object each render must not restart the timer.
  const text = useDebounced(JSON.stringify(body), WEIGHT_CHECK_DEBOUNCE_MS);
  return useQuery({
    queryKey: [QUERY_KEYS.WEIGHT_CHECK, text],
    queryFn: () => checkWeights(JSON.parse(text) as WeightCheckRequest),
    placeholderData: keepPreviousData,
    retry: false,
  });
}
