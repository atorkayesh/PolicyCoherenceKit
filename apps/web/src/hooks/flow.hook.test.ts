import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useFlowSteps } from "@/hooks/flow.hook";
import { useProjectStore } from "@/store/project.store";
import { seedProject } from "@/test/project";

describe("useFlowSteps", () => {
  beforeEach(() => useProjectStore.getState().reset());

  it("follows decision-maker ids for answered matrix steps", () => {
    seedProject({ dms: ["A", "B"], matricesAnswered: false });
    useProjectStore.setState({ answeredMatrices: ["dm-2"] });
    const { result } = renderHook(() => useFlowSteps());
    expect(result.current.answered.has("matrix-2")).toBe(true);
    act(() =>
      useProjectStore.getState().commitDecisionMakers(
        [
          { id: "dm-2", name: "B" },
          { id: "dm-1", name: "A" },
        ],
        "Neutral",
      ),
    );
    expect(result.current.answered.has("matrix-1")).toBe(true);
    expect(result.current.answered.has("matrix-2")).toBe(false);
    expect(result.current.hasResults).toBe(false);
  });
});
