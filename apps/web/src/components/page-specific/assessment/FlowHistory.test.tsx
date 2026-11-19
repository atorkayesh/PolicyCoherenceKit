import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FlowShell } from "@/components/page-specific/assessment/FlowShell";
import { flowSearchSchema } from "@/interfaces/project.interface";
import { getScales } from "@/services/scales.service";
import { useProjectStore } from "@/store/project.store";
import { SCALES } from "@/test/fixtures/scales.fixture";

vi.mock("@/services/scales.service", () => ({ getScales: vi.fn() }));

const store = () => useProjectStore.getState();

/** The `/` route with a real router on a memory history, as in the app. */
function renderFlow(step: string) {
  const rootRoute = createRootRoute();
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/",
    validateSearch: flowSearchSchema,
    component: FlowShell,
  });
  const history = createMemoryHistory({ initialEntries: [`/?step=${step}`] });
  const router = createRouter({
    routeTree: rootRoute.addChildren([indexRoute]),
    history,
  });
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return history;
}

const heading = () => screen.findByRole("heading", { level: 1 });

describe("flow history", () => {
  beforeEach(() => {
    store().reset();
    vi.mocked(getScales).mockResolvedValue(SCALES);
  });

  it("moves between steps with browser Back and Forward", async () => {
    store().setProjectName("Nexus");
    store().markAnswered("project");
    const history = renderFlow("project");
    expect((await heading()).textContent).toBe("What is this project called?");
    act(() => history.push("/?step=decision-makers"));
    await waitFor(async () =>
      expect((await heading()).textContent).toBe(
        "Who are the decision-makers?",
      ),
    );
    act(() => history.back());
    await waitFor(async () =>
      expect((await heading()).textContent).toBe(
        "What is this project called?",
      ),
    );
    act(() => history.forward());
    await waitFor(async () =>
      expect((await heading()).textContent).toBe(
        "Who are the decision-makers?",
      ),
    );
  });

  it("replaces a blocked step with the first unanswered one", async () => {
    const history = renderFlow("review");
    expect((await heading()).textContent).toBe("What is this project called?");
    expect(history.location.search).toBe("?step=project");
  });
});
