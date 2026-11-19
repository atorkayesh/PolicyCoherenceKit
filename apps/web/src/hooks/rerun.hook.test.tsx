import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useRerun } from "@/hooks/rerun.hook";
import { runAnalysis } from "@/services/analysis.service";
import { checkMatrices } from "@/services/matrices.service";
import { getScales } from "@/services/scales.service";
import { useProjectStore } from "@/store/project.store";
import {
  CHECK_COMPLETE_TWO,
  choiceOptions,
} from "@/test/fixtures/check.fixture";
import { SCALES } from "@/test/fixtures/scales.fixture";
import { seedProject } from "@/test/project";

vi.mock("@/services/scales.service", () => ({ getScales: vi.fn() }));
vi.mock("@/services/matrices.service", () => ({ checkMatrices: vi.fn() }));
vi.mock("@/services/analysis.service", () => ({ runAnalysis: vi.fn() }));
vi.mock("@/services/aggregation.service", () => ({
  previewAggregation: vi.fn(),
}));

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useRerun", () => {
  beforeEach(() => {
    useProjectStore.getState().reset();
    vi.mocked(getScales).mockResolvedValue(SCALES);
  });

  it("opens Weights when the weighted method has no stored weights", async () => {
    seedProject({ dms: ["A", "B", "C"], fill: "Enabling" });
    useProjectStore.getState().setMethod("weighted");
    vi.mocked(checkMatrices).mockResolvedValue({
      ...CHECK_COMPLETE_TWO,
      aggregation_options: choiceOptions(3),
    });
    const onOpen = vi.fn();
    const { result } = renderHook(() => useRerun(onOpen), { wrapper });
    await waitFor(() => expect(getScales).toHaveBeenCalled());
    await waitFor(() => expect(result.current).toBeDefined());
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
      result.current.mutate();
    });
    await waitFor(() => expect(onOpen).toHaveBeenCalledWith("weights"));
    expect(runAnalysis).not.toHaveBeenCalled();
    expect(useProjectStore.getState().aggregationOptions?.forNames).toBe(
      "A\nB\nC",
    );
  });
});
