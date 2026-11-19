import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/constants/query.constants";
import { getScales } from "@/services/scales.service";

/** Ratings, methods, rules, limits and colours from the API; they never change while the app runs. */
export function useScales() {
  return useQuery({
    queryKey: QUERY_KEYS.SCALES,
    queryFn: getScales,
    staleTime: Number.POSITIVE_INFINITY,
  });
}
