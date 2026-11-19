import { createFileRoute } from "@tanstack/react-router";
import { FlowShell } from "@/components/page-specific/assessment/FlowShell";
import { PAGE_TITLES } from "@/constants/layout.constants";
import { flowSearchSchema } from "@/interfaces/project.interface";

export const Route = createFileRoute("/")({
  validateSearch: flowSearchSchema,
  head: () => ({ meta: [{ title: PAGE_TITLES.HOME }] }),
  component: FlowShell,
});
